/* Spin / cascade / win-ladder director for Stage v2. Uses FEEL (feel.js) for every timing and STAGE (stage.js) hooks.
   Outcomes are fixed scripts (?demo=cascade|bigwin|loss; no param cycles all three). No game math.
   Director time stops during hit-stop; logs (window.__FEEL_LOG) are in real performance.now() ms. */
(function () {
  'use strict';
  var F = window.FEEL, T = F.T, P = F.profile, S, G, pitch, Q = new URLSearchParams(location.search);
  var $ = function (id) { return document.getElementById(id); };
  var DEMOS = {
    loss:    { seed: 11, wild: false, steps: [0.6] },                            // return below stake (LDW): no celebration under ukgc/de
    cascade: { seed: 7,  wild: true,  steps: [0.4, 0.6, 0.9, 1.2, 1.6, 2.1] },  // 6-step chain, small win
    bigwin:  { seed: 3,  wild: true,  steps: [4, 18, 90] }                       // 112x -> Big, Mega, Epic
  };
  var demoOrder = Q.get('demo') ? [Q.get('demo')] : ['loss', 'cascade', 'bigwin'], demoIdx = 0;
  var bet = function () { return parseFloat($('bet').textContent.replace(/,/g, '')) || 1; };
  function fmt(v) { return v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }

  // ---------- director clock (frozen during hit-stop) ----------
  var dnow = 0, lastReal = null, freezeUntil = 0, freeze = null, waiters = [], anims = [], shake = null;
  function wait(ms) { return new Promise(function (res) { waiters.push({ at: dnow + ms, res: res }); }); }
  function waitReal(ms) { return new Promise(function (res) { setTimeout(res, ms); }); }
  function hook() {
    var real = performance.now(), dt = lastReal === null ? 0 : Math.min(100, real - lastReal); lastReal = real;
    if (real < freezeUntil) { freeze.frames++; dt = 0; }
    else if (freeze) { F.log('hitStopEnd', { kind: freeze.kind, actualMs: Math.round(real - freeze.t0), frames: freeze.frames }); freeze = null; }
    dnow += dt;
    anims = anims.filter(function (a) { return !a(dnow); });
    waiters = waiters.filter(function (w) { if (dnow >= w.at) { w.res(); return false; } return true; });
    if (shake) {
      var u = (real - shake.t0) / T.shakeMs;
      if (u >= 1) { S.shake.set(0, 0, 0); F.log('shakeEnd', { kind: shake.kind, ms: Math.round(real - shake.t0) }); shake = null; }
      else { var a = T.shakePx * S.worldPerPx * Math.exp(-4 * u) * (1 - u); S.shake.set((Math.random() * 2 - 1) * a, (Math.random() * 2 - 1) * a, 0); }
    }
  }
  function heavyImpact(kind, ms) { // contact frame: sound hook + hit-stop + decaying shake (shake runs in real time)
    F.onImpact(kind, { heavy: true });
    var real = performance.now();
    freezeUntil = real + ms; freeze = { kind: kind, t0: real, frames: 0 };
    F.log('hitStopStart', { kind: kind, plannedMs: ms });
    shake = { kind: kind, t0: real }; F.log('shakeStart', { kind: kind, px: T.shakePx });
  }

  // ---------- strips (5 columns x 6 meshes: row -1 above the grid + 5 visible) ----------
  var strips = [], fillers;
  function rowY(k) { return G.HALF - G.CELL / 2 - (k - 1) * pitch; }
  function colX(c) { return -G.HALF + G.CELL / 2 + c * pitch; }
  function rnd() { return fillers[Math.floor(Math.random() * fillers.length)]; }
  function setMesh(m, id) {
    var d = S.symMats[id]; m.material = d.mat; m.userData.id = id; m.userData.base = d.scale; m.visible = true;
    m.scale.set(d.scale, d.scale, 1); m.position.z = d.tier === 'high' ? 0.14 : d.tier === 'special' ? 0.12 : 0.1;
    if (S.decorate) S.decorate(m, id);
  }
  function layout(s) {
    for (var k = 0; k < 6; k++) {
      var m = s.meshes[k], b = m.userData.base;
      m.position.set(colX(s.c), rowY(k) - (s.o - s.wraps) * pitch, m.position.z);
      m.scale.set(b, b * (1 + 0.28 * s.blur), 1);
    }
  }
  function buildStrips() {
    S.clearSymbols();
    fillers = Object.keys(S.symMats).filter(function (id) { return id !== 'wild' && id !== 'scatter'; });
    for (var c = 0; c < G.N; c++) {
      var s = { c: c, meshes: [], o: 0, wraps: 0, blur: 0, phase: 'stopped' };
      for (var k = 0; k < 6; k++) { var m = new THREE.Mesh(S.quad, S.symMats.A.mat); S.scene.add(m); setMesh(m, k === 0 ? rnd() : S.board[k - 1][c]); s.meshes.push(m); }
      layout(s); strips.push(s);
    }
  }

  // ---------- scripted outcome (seeded; object identity lets later steps fix the winning ids retroactively) ----------
  function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function buildOutcome(def) {
    var R = rng(def.seed), pick = function () { return { id: fillers[Math.floor(R() * fillers.length)] }; }, g = [], r, c;
    for (r = 0; r < G.N; r++) { g.push([]); for (c = 0; c < G.N; c++) g[r].push(pick()); }
    if (def.wild) g[2][1] = { id: 'wild' };
    var final = g.map(function (row) { return row.slice(); }), steps = [];
    def.steps.forEach(function (amount) {
      var W = fillers[Math.floor(R() * fillers.length)], k = 5 + Math.floor(R() * 3), wins = [], used = {};
      while (wins.length < k) { r = Math.floor(R() * G.N); c = Math.floor(R() * G.N); if (used[r + ',' + c] || g[r][c].id === 'wild') continue; used[r + ',' + c] = 1; g[r][c].id = W; wins.push([r, c]); }
      var refill = [];
      for (c = 0; c < G.N; c++) {
        var keep = [], n = 0; for (r = 0; r < G.N; r++) if (used[r + ',' + c]) n++; else keep.push(g[r][c]);
        var fresh = []; for (var i = 0; i < n; i++) fresh.push(pick());
        var col = fresh.concat(keep); for (r = 0; r < G.N; r++) g[r][c] = col[r];
        refill.push(fresh);
      }
      steps.push({ amount: amount, wins: wins, used: used, refill: refill });
    });
    return { final: final, steps: steps, mult: def.steps.reduce(function (a, b) { return a + b; }, 0) };
  }

  // ---------- reels ----------
  function reelPos(t, s) { // kick-back -> ease-in accel -> constant speed (cells)
    var v = T.spinSpeed / 1000, K = T.kickbackCells;
    if (t < T.kickbackMs) { var u = t / T.kickbackMs; return -K * (1 - (1 - u) * (1 - u)); }
    var t1 = t - T.kickbackMs;
    if (t1 < T.accelMs) { var w = t1 / T.accelMs; return -K + v * T.accelMs * w * w / 2; }
    return -K + v * T.accelMs / 2 + v * (t1 - T.accelMs);
  }
  function runReels(out, cyc) {
    var d0 = dnow, done = 0;
    strips.forEach(function (s) { s.phase = 'spin'; s.o = 0; s.wraps = 0; s.stopAt = T.firstStopMs + s.c * T.stopStaggerMs; });
    cyc.slam = function () {
      var t = dnow - d0, n = 0;
      strips.forEach(function (s) { if (s.phase === 'spin' && t < s.stopAt - T.decelMs) s.stopAt = Math.min(s.stopAt, t + T.decelMs + n++ * T.slamStaggerMs); });
    };
    return new Promise(function (resolve) {
      anims.push(function () {
        var t = dnow - d0;
        strips.forEach(function (s) {
          var ds = s.stopAt - T.decelMs, ovs = T.overshootCells;
          if (s.phase === 'spin') {
            if (t < ds) { s.o = reelPos(t, s); s.blur = Math.min(1, Math.max(0, (t - T.kickbackMs) / T.accelMs)); }
            else {
              s.phase = 'decel'; s.os = reelPos(ds, s); s.ofin = Math.floor(s.os) + 6; s.D = s.ofin + ovs - s.os;
              s.queue = [4, 3, 2, 1, 0].map(function (r) { return out.final[r][s.c].id; }).concat([rnd()]);
            }
          }
          if (s.phase === 'decel') {
            var u = Math.min(1, (t - ds) / T.decelMs); s.o = s.os + s.D * (1 - (1 - u) * (1 - u)); s.blur = 1 - u;
            if (t >= s.stopAt) { // contact frame
              s.phase = 'settle'; s.o = s.ofin + ovs; s.blur = 0;
              F.log('reelStop', { col: s.c, plannedMs: Math.round(s.stopAt), atMs: Math.round(t) }); F.onImpact('reelStop', { col: s.c });
              if (out.final.some(function (row) { return row[s.c].id === 'wild'; })) heavyImpact('wildMaw', T.hitStopMs);
            }
          } else if (s.phase === 'settle') {
            var e = Math.min(1, (t - s.stopAt) / T.settleMs); s.o = s.ofin + ovs * (1 - e) * (1 - e);
            if (e >= 1) { s.o = s.ofin; s.phase = 'stopped'; done++; }
          }
          while (s.o - s.wraps >= 1) {
            s.wraps++; var m = s.meshes.pop(); s.meshes.unshift(m);
            setMesh(m, s.phase !== 'spin' && s.queue.length ? s.queue.shift() : rnd());
          }
          layout(s);
        });
        if (done === G.N) { resolve(); return true; }
        return false;
      });
    });
  }

  // ---------- cascade ----------
  var glowTex = (function () { var c = document.createElement('canvas'); c.width = c.height = 64; var x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,.9)'); g.addColorStop(0.5, 'rgba(255,255,255,.25)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
  function runStep(step, i, cyc) {
    var f = F.chainFactor(i), E = T.explodeMs * f, Dr = T.dropMs * f, St = T.dropColStaggerMs * f, Pa = T.pauseMs * f, t0 = performance.now();
    F.log('stepStart', { step: i, factor: Math.round(f * 100) / 100 });
    cyc.won = Math.round((cyc.won + step.amount * cyc.bet) * 100) / 100;
    $('win').textContent = fmt(cyc.won); F.log('stepWin', { step: i, total: cyc.won });
    var meshes = step.wins.map(function (rc) { return strips[rc[1]].meshes[rc[0] + 1]; });
    var glows = meshes.map(function (m) {
      var g = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0x3FE0D0, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.0, clippingPlanes: S.clip }));
      g.position.set(m.position.x, m.position.y, 0.3); g.scale.set(1.6, 1.6, 1); S.scene.add(g); return g;
    });
    var h0 = dnow;
    anims.push(function () { var u = Math.min(1, (dnow - h0) / T.highlightMs), p = Math.sin(u * Math.PI * 3);
      meshes.forEach(function (m, j) { var b = m.userData.base * (1 + 0.08 * Math.abs(p)); m.scale.set(b, b, 1); glows[j].material.opacity = 0.35 + 0.35 * Math.abs(p); });
      return u >= 1; });
    return wait(T.highlightMs).then(function () {
      F.onImpact('explode', { step: i }); var e0 = dnow;
      anims.push(function () { var u = Math.min(1, (dnow - e0) / E);
        meshes.forEach(function (m, j) { var b = m.userData.base * (1 + 0.35 * u) * (1 - u * u * u); m.scale.set(b, b, 1); glows[j].material.opacity = 0.7 * (1 - u); glows[j].scale.setScalar(1.6 + u); });
        return u >= 1; });
      return wait(E);
    }).then(function () {
      glows.forEach(function (g) { S.scene.remove(g); g.material.dispose(); });
      var d0 = dnow;
      strips.forEach(function (s, c) {
        var keep = [], gone = [];
        for (var r = 0; r < G.N; r++) (step.used[r + ',' + c] ? gone : keep).push(s.meshes[r + 1]);
        var n = gone.length; if (!n) return;
        gone.forEach(function (m, j) { setMesh(m, step.refill[c][j].id); m.position.y = rowY(j + 1) + n * pitch; });
        var col = gone.concat(keep), from = col.map(function (m) { return m.position.y; }), landed = false;
        s.meshes = [s.meshes[0]].concat(col);
        anims.push(function () {
          var u = Math.min(1, Math.max(0, (dnow - d0 - c * St) / (Dr - (G.N - 1) * St))); // stagger lives inside the drop budget
          col.forEach(function (m, r) {
            var to = rowY(r + 1), b = m.userData.base;
            if (from[r] === to) return;
            if (u < 0.8) { var w = u / 0.8; m.position.y = from[r] + (to - from[r]) * w * w; m.scale.set(b, b, 1); }
            else { var v = (u - 0.8) / 0.2, sq = Math.sin(Math.PI * v); m.position.y = to + T.dropBounceCells * pitch * sq; m.scale.set(b * (1 + 0.08 * sq), b * (1 - 0.12 * sq), 1); }
          });
          if (!landed && u >= 0.8) { landed = true; F.onImpact('drop', { step: i, col: c }); }
          return u >= 1;
        });
      });
      S.setRitual(Math.min(1, S.state.ritual + 0.05));
      return wait(Dr);
    }).then(function () { return wait(Pa); }).then(function () {
      F.log('stepEnd', { step: i, ms: Math.round(performance.now() - t0) });
    });
  }

  // ---------- win ladder ----------
  function celebrate(cyc) {
    var total = cyc.won, b = cyc.bet, mult = total / b;
    if (total <= 0) return Promise.resolve();
    if (total <= b && !P.celebrateAtOrBelowStake) { // RTS 14F: show the amount, no celebration
      $('win').textContent = fmt(total); F.log('win', { celebrate: false, total: total, mult: mult }); return Promise.resolve();
    }
    var top = F.tierFor(mult), dur = top ? top.countMs : T.smallWinCountMs, next = 0, c0 = dnow, ov = $('winOverlay');
    ov.className = 'on'; $('winTier').textContent = ''; $('winValue').textContent = fmt(0); $('spin').textContent = 'SKIP';
    F.log('countStart', { target: total, mult: mult, durMs: dur, tier: top ? top.id : null });
    function reachTier(t, skipped) {
      $('winTier').textContent = t.label; F.log('tier', { id: t.id, threshold: t.mult, mult: Math.round(cyc.shown / b * 100) / 100, skipped: !!skipped });
      heavyImpact('tier', T.tierHitStopMs);
      var fl = $('flash'); fl.style.opacity = '0.55'; setTimeout(function () { fl.style.opacity = '0'; }, T.flashMs);
    }
    return new Promise(function (resolve) {
      function finish(skipped) {
        cyc.shown = total; $('winValue').textContent = fmt(total); $('win').textContent = fmt(total);
        while (next < T.tiers.length && T.tiers[next].mult <= mult) { if (T.tiers[next] === top) reachTier(top, skipped); next++; }
        F.log('countEnd', { value: total, shownText: $('winValue').textContent, skipped: !!skipped });
        cyc.skip = null; wait(T.holdAfterCountMs).then(function () { ov.className = ''; resolve(); });
      }
      cyc.skip = function (ev) { // lands on the exact final value immediately (same task -> next painted frame)
        if (dnow - c0 < T.skipAfterMs) { F.log('skipTooEarly'); return; }
        F.log('skipInput', { inputF: cyc.inputF }); anims = anims.filter(function (a) { return a !== count; });
        finish(true); F.log('skipLanded', { value: total });
      };
      function count() {
        var u = Math.min(1, (dnow - c0) / dur), v = 1 - Math.pow(1 - u, T.countEaseExp);
        cyc.shown = total * v; $('winValue').textContent = fmt(cyc.shown);
        while (next < T.tiers.length && cyc.shown / b >= T.tiers[next].mult) reachTier(T.tiers[next++]);
        if (u >= 1) { finish(false); return true; }
        return false;
      }
      anims.push(count);
    });
  }

  // ---------- cycle ----------
  var cyc = null;
  function onPress(ev) {
    if (ev) ev.preventDefault();
    if (!cyc) return startCycle();
    cyc.inputF = F.frame();
    if (cyc.skip) return cyc.skip(ev);
    if (cyc.phase === 'reels') { if (P.allowSlamStop) { F.log('slam'); cyc.slam(); } else F.log('slamIgnored', { profile: P.id }); return; }
    F.log('inputIgnored', { phase: cyc.phase });
  }
  function startCycle() {
    var name = demoOrder[demoIdx++ % demoOrder.length], def = DEMOS[name] || DEMOS.cascade, b = bet();
    var bal = parseFloat($('balance').textContent.replace(/,/g, '')); $('balance').textContent = fmt(bal - b); $('win').textContent = '0.00';
    var out = buildOutcome(def), pressReal = performance.now();
    cyc = { phase: 'reels', won: 0, bet: b, shown: 0 }; var me = cyc;
    $('spin').classList.add('busy');
    F.log('press', { demo: name, profile: P.id, bet: b, scriptedMult: out.mult });
    runReels(out, me).then(function () {
      me.phase = 'cascade';
      return out.steps.reduce(function (p, st, i) { return p.then(function () { return runStep(st, i + 1, me); }); }, Promise.resolve());
    }).then(function () { me.phase = 'celebrate'; return celebrate(me); }).then(function () {
      me.phase = 'pad'; var el = performance.now() - pressReal, pad = Math.max(0, P.minCycleMs - el);
      F.log('pad', { ms: Math.round(pad), beforePadMs: Math.round(el) });
      return waitReal(pad);
    }).then(function () {
      var bal2 = parseFloat($('balance').textContent.replace(/,/g, '')); $('balance').textContent = fmt(bal2 + me.won);
      F.log('cycleEnd', { demo: name, cycleMs: Math.round(performance.now() - pressReal), won: me.won, minCycleMs: P.minCycleMs });
      cyc = null; $('spin').classList.remove('busy'); $('spin').textContent = 'SPIN';
      window.__FEEL_CYCLE_DONE = (window.__FEEL_CYCLE_DONE || 0) + 1;
    });
  }

  // ---------- boot (after the stage intro has landed) ----------
  (function boot() {
    if (!window.__RENDER_READY || !window.STAGE) return setTimeout(boot, 50);
    S = window.STAGE; G = S.geo; pitch = G.CELL + G.GAP;
    buildStrips(); S.hooks.push(hook);
    $('spin').onclick = onPress;
    window.addEventListener('keydown', function (e) { if (e.code === 'Space' && !e.repeat) onPress(e); });
    window.__FEEL_READY = true; F.log('ready', { profile: P.id, demos: demoOrder });
  })();
})();
