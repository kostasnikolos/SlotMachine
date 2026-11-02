/*
 * audio_dark.js - dark procedural event sounds for the canvas front end (docs/feel_design_plan.md, section B).
 *
 * Usage (after the game has booted):   window.DarkAudio.install(game.aud)
 *
 * install(A) patches the audio object built by makeAudio() IN PLACE and returns it (idempotent). It keeps the
 * ambience bed, breathing and A.bubble, and replaces the "bubbly" event sounds with dark recipes under the same
 * method names and signatures. It also adds a shared bus: dry -> procedural ConvolverNode at -12 dB, a master
 * DynamicsCompressor (-18 dB, 4:1, 3 ms, 250 ms), an ambience low-pass that closes with depth, a very quiet per-depth
 * drone, and duck(dB, attackMs, releaseMs) which dips the ambience on every impact (-9 dB in 20 ms, back in 600 ms).
 *
 * Everything is synthesised with Web Audio nodes only (no samples). Every public call is guarded against a missing,
 * closed or suspended context (an OfflineAudioContext counts as usable so the lab can render).
 */
(function (root) {
  'use strict';

  const dB = (d) => Math.pow(10, d / 20);
  const semi = (f, s) => f * Math.pow(2, s / 12);
  const rnd = (a, b) => a + Math.random() * (b - a);
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const DRONE = [0, 36.7, 32.7, 29.1, 24.5, 24.5]; // D1 sinking with depth (game levels 0..5)

  function install(A) {
    if (!A || typeof A !== 'object') return A;
    if (A.__dark) return A;
    A.__dark = true;
    const D = A.dark = { ready: false, cascade: 0, lastLand: -1e9, hold: false, levelInit: false, version: 1 };

    // ---- guards -------------------------------------------------------------------------------------------------
    const isOffline = () => typeof OfflineAudioContext !== 'undefined' && A.ctx instanceof OfflineAudioContext;
    const have = () => !!(A.ctx && A.master && A.sfx && A.amb);
    const live = () => { if (!have()) return false; if (A.ctx.state === 'closed') return false; if (A.ctx.state === 'suspended' && !isOffline()) return false; if (!D.ready) setupBus(); return D.ready; };
    const now = () => A.ctx.currentTime;

    // ---- node helpers (same shapes as makeAudio's, re-created here because those live in a closure) --------------
    const gain = (v, to) => { const g = A.ctx.createGain(); g.gain.value = v; if (to) g.connect(to); return g; };
    const osc = (type, f) => { const o = A.ctx.createOscillator(); o.type = type; o.frequency.value = f; return o; };
    const filt = (type, f, q) => { const b = A.ctx.createBiquadFilter(); b.type = type; b.frequency.value = f; if (q) b.Q.value = q; return b; };
    const env = (g, t, a, peak, d) => { g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(peak, t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + a + d); };
    const wet = (node, amt) => { if (D.verb && amt > 0) node.connect(gain(amt, D.verb)); };
    const buf = (kind) => {
      const ctx = A.ctx, sr = ctx.sampleRate;
      if (kind === 'w') {
        if (!A.noiseBuf) { A.noiseBuf = ctx.createBuffer(1, sr * 2, sr); const d = A.noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; }
        return A.noiseBuf;
      }
      if (kind === 'b') {
        if (!A.brownBuf) {
          A.brownBuf = ctx.createBuffer(1, sr * 6, sr); const d = A.brownBuf.getChannelData(0); let b = 0, pk = 0;
          for (let i = 0; i < d.length; i++) { b = (b + 0.02 * (Math.random() * 2 - 1)) / 1.02; d[i] = b; pk = Math.max(pk, Math.abs(b)); }
          for (let i = 0; i < d.length; i++) d[i] = d[i] / pk * 0.9;
        }
        return A.brownBuf;
      }
      // pink (Paul Kellet's 3-pole approximation), normalised
      if (!D.pinkBuf) {
        D.pinkBuf = ctx.createBuffer(1, sr * 4, sr); const d = D.pinkBuf.getChannelData(0); let b0 = 0, b1 = 0, b2 = 0, pk = 0;
        for (let i = 0; i < d.length; i++) {
          const w = Math.random() * 2 - 1;
          b0 = 0.99765 * b0 + w * 0.0990460; b1 = 0.96300 * b1 + w * 0.2965164; b2 = 0.57000 * b2 + w * 1.0526913;
          d[i] = b0 + b1 + b2 + w * 0.1848; pk = Math.max(pk, Math.abs(d[i]));
        }
        for (let i = 0; i < d.length; i++) d[i] = d[i] / pk * 0.9;
      }
      return D.pinkBuf;
    };
    const noise = (kind, t, dur) => { const s = A.ctx.createBufferSource(); s.buffer = buf(kind); s.loop = true; s.start(t, rnd(0, 1.5)); s.stop(t + dur + 0.05); return s; };
    // noise through a filter with an envelope; returns { fl, g }
    const nburst = (t, kind, type, f, q, a, peak, d, to) => {
      const n = noise(kind, t, a + d), fl = filt(type, f, q), g = gain(0.0001, to || A.sfx);
      env(g, t, a, peak, d); n.connect(fl); fl.connect(g); return { fl, g, n };
    };
    // sine with a pitch glide and an envelope
    const sub = (t, f0, f1, glide, a, peak, d, to, type) => {
      const o = osc(type || 'sine', f0), g = gain(0.0001, to || A.sfx);
      o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + glide);
      env(g, t, a, peak, d); o.connect(g); o.start(t); o.stop(t + a + d + 0.05); return g;
    };
    // a dark, slow minor-cluster shimmer (sines through a low-pass, mostly reverb); never major
    const shimmer = (t, rootHz, peak, d, wetAmt) => {
      const lp = filt('lowpass', 1800, 0.7), out = gain(1, A.sfx); lp.connect(out); wet(lp, wetAmt == null ? 1 : wetAmt);
      [[1, 1], [1.1892, 0.7], [1.4983, 0.55], [2.3784, 0.3], [2.9966, 0.18]].forEach((p, i) => { // root, m3, 5, m10, 12
        const f = rootHz * p[0] * rnd(0.997, 1.003), o = osc('sine', f), g = gain(0.0001, lp), ta = t + i * 0.035;
        o.frequency.setValueAtTime(f * 1.01, ta); o.frequency.exponentialRampToValueAtTime(f, ta + 0.25);
        env(g, ta, 0.06 + i * 0.02, peak * p[1], d * (1 - i * 0.08)); o.connect(g); o.start(ta); o.stop(ta + d + 0.2);
      });
      return out;
    };

    // ---- bus ------------------------------------------------------------------------------------------------------
    function setupBus() {
      if (D.ready || !have()) return;
      const ctx = A.ctx, sr = ctx.sampleRate;
      // procedural impulse response: 3.2 s of exponentially decaying noise, low-pass sweeping 4 kHz -> 800 Hz, 20 ms fade-in
      const len = Math.floor(sr * 3.2), ir = ctx.createBuffer(2, len, sr), fadeN = Math.floor(sr * 0.02);
      for (let ch = 0; ch < 2; ch++) {
        const d = ir.getChannelData(ch); let lp = 0;
        for (let i = 0; i < len; i++) {
          const k = i / len, fc = 4000 * Math.pow(0.2, k), a = 1 - Math.exp(-6.2831853 * fc / sr);
          lp += a * ((Math.random() * 2 - 1) - lp);
          d[i] = lp * Math.exp(-6.9 * k) * (i < fadeN ? i / fadeN : 1);
        }
      }
      D.verb = ctx.createConvolver(); D.verb.buffer = ir;
      D.verbOut = gain(1, A.master); D.verb.connect(D.verbOut);
      D.send = gain(dB(-12), D.verb); A.sfx.connect(D.send);
      // master: compressor (-18 dB, 4:1, 3 ms, 250 ms) then a rebuilt output stage (sub HP, top shelf, brickwall, trim)
      const comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -18; comp.knee.value = 6; comp.ratio.value = 4; comp.attack.value = 0.003; comp.release.value = 0.25;
      const hp = filt('highpass', 30, 0.7), shelf = filt('highshelf', 4200); shelf.gain.value = -7;
      const lim = ctx.createDynamicsCompressor();
      lim.threshold.value = -6; lim.knee.value = 0; lim.ratio.value = 20; lim.attack.value = 0.001; lim.release.value = 0.15;
      const trim = gain(0.5, ctx.destination);
      try { A.master.disconnect(); } catch (e) { /* nothing connected yet */ }
      A.master.connect(comp); comp.connect(hp); hp.connect(shelf); shelf.connect(lim); lim.connect(trim);
      D.comp = comp; D.limiter = lim; D.trim = trim;
      // analyser tap on the master bus (post-compressor): the Leviathan's bioluminescence reads the 40-120 Hz band from it
      try {
        const an = ctx.createAnalyser();
        an.fftSize = 2048; an.smoothingTimeConstant = 0.55; an.minDecibels = -95; an.maxDecibels = -20;
        lim.connect(an);
        A.analyser = an; D.fft = new Float32Array(an.frequencyBinCount);
      } catch (e) { A.analyser = null; }
      // ambience: low-pass closing with depth (1.2 kHz -> 500 Hz), re-routed between amb and master
      D.ambLP = filt('lowpass', 1200 - (A.level || 0) * 140, 0.7);
      try { A.amb.disconnect(); } catch (e) { /* ignore */ }
      A.amb.connect(D.ambLP); D.ambLP.connect(A.master);
      // per-depth drone: fundamental plus 1.5x partials, very quiet, lives in the ambience so it ducks with it
      D.droneOut = gain(1, A.amb); D.drone = [];
      for (let k = 0; k < 4; k++) {
        const o = osc('sine', 36.7 * Math.pow(1.5, k)), g = gain(0.0001, D.droneOut);
        o.connect(g); o.start(now()); D.drone.push({ o, g });
      }
      D.ready = true;
      applyLevel(A.level || 0, 0.01);
    }

    function applyLevel(L, tc) {
      if (!D.ready) return;
      const t = now(), base = DRONE[clamp(L | 0, 0, 5)], n = Math.min(4, L | 0);
      D.ambLP.frequency.setTargetAtTime(1200 - L * 140, t, tc || 1.5);
      D.drone.forEach((p, k) => {
        if (base) p.o.frequency.setTargetAtTime(base * Math.pow(1.5, k), t, tc || 1.0);
        p.g.gain.setTargetAtTime(k < n ? 0.011 * Math.pow(0.72, k) : 0.0001, t, tc || 1.5);
      });
    }

    // ---- ducking -----------------------------------------------------------------------------------------------
    const ambBase = () => (A.ambBase || 0.32) * (D.hold ? 0.25 : 1);
    const duckAt = (t, db, attackMs, releaseMs) => {
      if (!have()) return;
      const base = ambBase(), lo = base * dB(db == null ? -9 : db), a = (attackMs == null ? 20 : attackMs) / 1000, r = (releaseMs == null ? 600 : releaseMs) / 1000;
      [A.amb, A.ambWet].forEach((g) => {
        if (!g) return;
        g.gain.cancelScheduledValues(t);
        g.gain.setTargetAtTime(lo, t, Math.max(0.001, a / 3));
        g.gain.setTargetAtTime(base, t + a + 0.01, Math.max(0.01, r / 3));
      });
    };
    const oDuck = A.duck;
    // duck(true|false) keeps the game's celebration hold; duck(dB, attackMs, releaseMs[, at]) is the impact dip
    A.duck = (a, b, c, at) => {
      if (!have()) return;
      if (typeof a === 'boolean' || a == null) {
        D.hold = !!a;
        if (oDuck) return oDuck(a);
        const v = ambBase(), t = now();
        A.amb.gain.setTargetAtTime(v, t, 0.3); if (A.ambWet) A.ambWet.gain.setTargetAtTime(v, t, 0.3);
        return;
      }
      duckAt(at == null ? now() : at, a, b, c);
    };
    A.duckImpact = (db, a, r) => A.duck(db == null ? -9 : db, a == null ? 20 : a, r == null ? 600 : r);
    // hush(dB, holdMs[, releaseMs]): the ambience drops in 60 ms and stays down for holdMs (the stillness before a strike)
    A.hush = (db, holdMs, releaseMs) => {
      if (!have()) return;
      const t = now(), base = ambBase(), lo = base * dB(db == null ? -12 : db), hold = (holdMs == null ? 2000 : holdMs) / 1000, r = (releaseMs == null ? 500 : releaseMs) / 1000;
      [A.amb, A.ambWet].forEach((g) => {
        if (!g) return;
        g.gain.cancelScheduledValues(t);
        g.gain.setTargetAtTime(lo, t, 0.02);
        g.gain.setTargetAtTime(base, t + hold, Math.max(0.01, r / 3));
      });
    };
    // 0..1 energy in the 40-120 Hz band of the master bus (0 while the context is not running)
    A.lowBand = () => {
      const an = A.analyser;
      if (!an || !A.ctx || A.ctx.state !== 'running') return 0;
      an.getFloatFrequencyData(D.fft);
      const hz = A.ctx.sampleRate / an.fftSize;
      const i0 = Math.max(1, Math.floor(40 / hz)), i1 = Math.max(i0, Math.ceil(120 / hz));
      let acc = 0;
      for (let i = i0; i <= i1; i++) acc += D.fft[i];
      const db = acc / (i1 - i0 + 1);
      return clamp((db + 72) / 42, 0, 1);
    };

    // ---- init / setLevel hooks ----------------------------------------------------------------------------------
    const oInit = A.init;
    A.init = function () { const r = oInit ? oInit.apply(A, arguments) : undefined; setupBus(); return r; };
    if (have()) setupBus();

    const oSetLevel = A.setLevel;
    A.setLevel = (l) => {
      const prev = A.level || 0, L = clamp((+l || 0) | 0, 0, 5);
      if (oSetLevel) oSetLevel(l); else A.level = L;
      if (!have()) { A.level = L; return; }
      applyLevel(L);
      if (D.levelInit && L > prev) A.levelUp();
      D.levelInit = true;
    };

    // ---- recipes (internal versions take an explicit time) -------------------------------------------------------
    const _dissolve = (t) => {
      const b = nburst(t, 'w', 'bandpass', 900, 3, 0.004, 1.6, 0.075);
      b.fl.frequency.setValueAtTime(900, t); b.fl.frequency.exponentialRampToValueAtTime(250, t + 0.08);
      wet(b.g, 0.35);
      sub(t, 110, 55, 0.12, 0.004, 0.8, 0.12);
      duckAt(t, -5, 20, 400);
    };

    const _land = (t, step) => {
      const s = clamp(step | 0, 0, 6), r = Math.pow(2, -2 * s / 12), w = 1 + 0.1 * s;
      sub(t, 70 * r, 38 * r, 0.2, 0.004, 1.0, 0.2);
      wet(nburst(t, 'w', 'lowpass', 400, 0.8, 0.002, 0.6, 0.12).g, 0.3 * w);
      // FM metal: carrier 180 Hz, modulator 311 Hz, index 4 -> 0 over 150 ms
      const car = osc('sine', 180 * r), mod = osc('sine', 311 * r), mg = gain(4 * 311 * r), lp = filt('lowpass', 2600, 0.7), g = gain(0.0001, A.sfx);
      mg.gain.setValueAtTime(4 * 311 * r, t); mg.gain.linearRampToValueAtTime(0, t + 0.15);
      mod.connect(mg); mg.connect(car.frequency); car.connect(lp); lp.connect(g);
      env(g, t, 0.002, 0.4, 0.16); wet(g, 0.45 * w);
      car.start(t); mod.start(t); car.stop(t + 0.25); mod.stop(t + 0.25);
      duckAt(t, -9, 20, 600);
    };

    const _chomp = (t0, v) => {
      v = v || 1;
      duckAt(t0, -30, 5, 500);                      // the hole before the bite
      const t = t0 + 0.04;                           // 40 ms silence
      nburst(t, 'w', 'highpass', 2000, 0.7, 0.0005, 0.6 * v, 0.008);          // 8 ms click
      const body = nburst(t, 'w', 'lowpass', 3000, 0.8, 0.003, 0.55 * v, 0.5); // noise body 500 ms, LP 3 kHz -> 150 Hz
      body.fl.frequency.setValueAtTime(3000, t); body.fl.frequency.exponentialRampToValueAtTime(150, t + 0.5);
      wet(body.g, 0.5);
      sub(t, 55, 28, 0.6, 0.004, 0.8 * v, 0.6);                                 // sub 55 -> 28 Hz / 600 ms
      nburst(t, 'b', 'lowpass', 90, 0.7, 0.02, 0.7 * v, 1.5);                   // brown rumble 1.5 s
      return t;
    };

    const _impact = (t, v) => {
      v = v || 1;
      const ti = _chomp(t, v * dB(6));
      // ring-mod growl: saw 45 Hz x sine 31 Hz, 900 ms, LP 600 Hz
      const saw = osc('sawtooth', 45), mod = osc('sine', 31), ring = gain(0), lp = filt('lowpass', 600, 0.8), g = gain(0.0001, A.sfx);
      mod.connect(ring.gain); saw.connect(ring); ring.connect(lp); lp.connect(g);
      env(g, ti, 0.01, 0.4 * v, 0.9); wet(g, 0.5);
      saw.start(ti); mod.start(ti); saw.stop(ti + 1.0); mod.stop(ti + 1.0);
      return ti;
    };

    const _riser = (t, d) => {
      d = d || 1.5;
      const n = noise('p', t, d), bp = filt('bandpass', 200, 6), g = gain(0.0001, A.sfx);
      bp.frequency.setValueAtTime(200, t); bp.frequency.exponentialRampToValueAtTime(2500, t + d);
      g.gain.setValueAtTime(0.02, t); g.gain.exponentialRampToValueAtTime(0.9, t + d); g.gain.linearRampToValueAtTime(0.0001, t + d + 0.008);
      n.connect(bp); bp.connect(g); wet(g, 0.4);
      return t + d;
    };

    const _win = (t, x) => {
      const lx = Math.log2(1 + Math.max(0, +x || 0)), w = clamp(0.35 + 0.16 * lx, 0.35, 1);
      sub(t, 90, 40, 0.3, 0.005, 0.6 * w, 0.35 + 0.08 * lx);
      const klp = filt('lowpass', 500, 0.7); klp.connect(A.sfx);
      sub(t, 110, 55, 0.2, 0.003, 0.3 * w, 0.25, klp, 'triangle'); // weighted body
      const ex = nburst(t, 'b', 'lowpass', 1200, 0.7, 0.01, 0.16 * w, 0.25);
      ex.fl.frequency.setValueAtTime(1200, t); ex.fl.frequency.exponentialRampToValueAtTime(300, t + 0.25);
      shimmer(t + 0.02, 146.83, 0.05 * w, 0.8 + 0.3 * lx, 1.0);
      duckAt(t, -9, 20, 600);
    };

    const _levelUp = (t) => {
      sub(t, 110, 36, 2.0, 0.05, 0.45, 2.2);
      const ex = nburst(t, 'b', 'lowpass', 1500, 0.7, 0.03, 0.35, 0.6);
      ex.fl.frequency.setValueAtTime(1500, t); ex.fl.frequency.exponentialRampToValueAtTime(200, t + 0.6);
      wet(ex.g, 0.6);
      duckAt(t, -9, 20, 900);
    };

    const _tick = (t, p) => {
      const f = 400 + 800 * clamp(+p || 0, 0, 1);
      nburst(t, 'w', 'bandpass', f, 8, 0.0005, 1.0, 0.02);
      nburst(t, 'w', 'highpass', 3000, 0.7, 0.0003, 0.15, 0.004);
    };

    const _ui = (t) => {
      sub(t, 420, 180, 0.03, 0.001, 0.7, 0.05);
      nburst(t, 'w', 'lowpass', 1200, 0.7, 0.0005, 0.5, 0.01);
    };

    const _tierStack = (t, n, lv) => {
      lv = lv || 1;
      // T1: sub pulse 45 Hz / 500 ms over a low thud
      const p = osc('sine', 45), pg = gain(0.0001, A.sfx); env(pg, t, 0.01, 0.8 * lv, 0.5); p.connect(pg); p.start(t); p.stop(t + 0.6);
      sub(t, 80, 45, 0.2, 0.004, 0.4 * lv, 0.3);
      if (n >= 2) {
        // FM bell cluster 1:1.41 (G minor: G2, Bb2, D3), long reverb
        [98, 116.54, 146.83].forEach((f, i) => {
          const car = osc('sine', f), mod = osc('sine', f * 1.41), mg = gain(f * 3), lp = filt('lowpass', 2200, 0.7), g = gain(0.0001, A.sfx), ts = t + i * 0.05;
          mg.gain.setValueAtTime(f * 3, ts); mg.gain.exponentialRampToValueAtTime(f * 0.05, ts + 1.5);
          mod.connect(mg); mg.connect(car.frequency); car.connect(lp); lp.connect(g);
          env(g, ts, 0.01, 0.11 * lv, 1.5); wet(g, 1.4);
          car.start(ts); mod.start(ts); car.stop(ts + 1.7); mod.stop(ts + 1.7);
        });
      }
      if (n >= 3) {
        // riser loops + detuned-saw choir through 300-900 Hz formants (D minor: D2, F2, A2)
        _riser(t + 0.1, 0.8); _riser(t + 0.95, 0.8);
        const f1 = filt('bandpass', 300, 4), f2 = filt('bandpass', 600, 4), f3 = filt('bandpass', 900, 4), lp = filt('lowpass', 1500, 0.7), g = gain(0.0001, A.sfx);
        [f1, f2, f3].forEach((f) => f.connect(lp)); lp.connect(g); wet(g, 0.8);
        [73.42, 87.31, 110].forEach((f) => [-7, 0, 7].forEach((c) => { const o = osc('sawtooth', f * Math.pow(2, c / 1200)); o.connect(f1); o.connect(f2); o.connect(f3); o.start(t); o.stop(t + 3.2); }));
        env(g, t, 0.3, 0.09 * lv, 2.6);
      }
    };
    const _tier = (t, n) => {
      n = clamp(n | 0, 1, 4);
      if (n === 4) { duckAt(t, -60, 10, 800); _tierStack(t + 0.5, 4, dB(3)); }
      else { duckAt(t, -9, 20, 600); _tierStack(t, n, 1); }
    };

    // ---- public methods --------------------------------------------------------------------------------------
    A.spin = () => { D.cascade = 0; D.lastLand = -1e9; };
    A.dissolve = () => { if (!live()) return; _dissolve(now()); };
    A.fizz = A.dissolve;
    A.land = (step) => {
      if (!live()) return;
      const t = now();
      if (t - D.lastLand < 0.06) return;
      if (step == null) { D.cascade = (t - D.lastLand > 3.5) ? 0 : D.cascade + 1; step = D.cascade; } else D.cascade = step | 0;
      D.lastLand = t;
      _land(t, step);
    };
    A.chomp = (v) => { if (!live()) return; _chomp(now(), v); };
    A.impact = (v) => { if (!live()) return; _impact(now(), v); };
    A.riser = (dur) => { if (!live()) return; return _riser(now(), dur) - now(); };
    // Leviathan strike: riser (1.5 s) -> 300 ms of total silence -> impact (+6 dB) with the ring-mod growl
    A.roar = (v) => {
      if (!live()) return;
      const t = now(), te = _riser(t, 1.5);
      duckAt(te - 0.01, -60, 10, 600);
      _impact(te + 0.3, v || 1);
      return te + 0.3 - t;
    };
    A.win = (x) => { if (!live()) return; _win(now(), x); };
    A.levelUp = () => { if (!live()) return; _levelUp(now()); };
    A.tier = (n) => { if (!live()) return; _tier(now(), n); };
    A.tierUp = (n) => A.tier(n);
    A.tick = (p) => { if (!live()) return; _tick(now(), p); };
    A.ui = () => { if (!live()) return; _ui(now()); };
    A.shimmer = () => { if (!live()) return; const t = now(); shimmer(t, 110, 0.045, 1.4, 1.2); sub(t, 60, 42, 0.4, 0.05, 0.12, 0.6); };
    // symbols sinking out of the grid: dark whoosh down and a sub drop (no bubbles)
    A.sink = () => {
      if (!live()) return;
      const t = now(), w = nburst(t, 'b', 'lowpass', 520, 0.8, 0.07, 0.45, 0.75);
      w.fl.frequency.setValueAtTime(520, t); w.fl.frequency.exponentialRampToValueAtTime(60, t + 0.8); wet(w.g, 0.5);
      sub(t, 110, 30, 0.56, 0.04, 0.26, 0.8);
      duckAt(t, -6, 20, 500);
    };
    // wild surfacing: rising dark water and a slow minor shimmer (no bubble run)
    A.wildRise = () => {
      if (!live()) return;
      const t = now(), sw = nburst(t, 'b', 'lowpass', 300, 0.8, 0.3, 0.3, 0.6);
      sw.fl.frequency.setValueAtTime(300, t); sw.fl.frequency.exponentialRampToValueAtTime(900, t + 0.8); wet(sw.g, 0.6);
      sub(t, 40, 70, 0.8, 0.3, 0.18, 0.7);
      shimmer(t + 0.15, 146.83, 0.04, 1.8, 1.2);
    };
    // end of a celebration: a low hit sized to the tier and a long dark shimmer
    A.endSting = (tier) => {
      if (!live()) return;
      const t = now(), T = clamp(tier | 0, 1, 4);
      sub(t, 95, 28, 0.77, 0.004, 0.42 * (0.7 + T * 0.12), 1.1);
      const n = nburst(t, 'b', 'lowpass', 800, 0.7, 0.003, 0.3, 0.85);
      n.fl.frequency.setValueAtTime(800, t); n.fl.frequency.exponentialRampToValueAtTime(90, t + 0.8); wet(n.g, 0.7);
      shimmer(t + 0.05, 73.42 * (T >= 3 ? 2 : 1), 0.05, 2.2, 1.3);
      duckAt(t, -9, 20, 600);
    };

    A.darkNames = ['spin', 'dissolve', 'fizz', 'land', 'chomp', 'impact', 'riser', 'roar', 'win', 'levelUp', 'setLevel', 'tier', 'tierUp', 'tick', 'ui', 'shimmer', 'sink', 'wildRise', 'endSting', 'duck', 'duckImpact', 'hush', 'lowBand'];
    return A;
  }

  root.DarkAudio = { install, version: 1 };
})(typeof window !== 'undefined' ? window : this);
