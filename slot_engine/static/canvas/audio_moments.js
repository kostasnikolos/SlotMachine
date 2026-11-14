/*
 * audio_moments.js - the designed moment cues (the help, the win seam, a voice per symbol) as samples.
 *
 * Usage (after DarkAudio.install):   window.MomentAudio.install(game.aud, 'assets/sfx/')
 *
 * The clips are rendered offline by scripts/ai/assetgen/moments.py and cut to event size by sfx_pack.py; the manifest
 * (assets/sfx/moments.json) carries each clip's length. install(A) adds a small sample player to the audio object and
 * these methods, each of which returns true only if a clip actually started, so callers can fall back to the
 * procedural set when a file is missing, still loading, or the context is not running:
 *
 *   A.helpLead(v)        everything before the bite (dread, targeting, the vacuum dip); v = 'full' | 'short'
 *   A.helpImpact(v)      the bite; fire it from the line that starts the hit-stop, never from a timer
 *   A.helpRecede(v)      the creature leaving and the water draining, under the transformation
 *   A.cellTurn(i, n)     one struck cell turning; the last of n carries the weight
 *   A.seam(step)         crack + jet on a winning way, by cascade step
 *   A.seamImplode(step)  the implosion that follows
 *   A.symLand(sym)       a symbol's own landing voice (three takes, never the same one twice running)
 *   A.symWin(sym)        a symbol's win stinger
 *
 * The clips already contain their own room, so they go to the master bus through a dry trim and skip the shared
 * reverb send. They were mixed on meters, not by ear: MomentAudio.trimDb is the one number to turn first.
 */
(function (root) {
  'use strict';

  const dB = (d) => Math.pow(10, d / 20);
  const SYM = {
    LOW_10: 'low_10', LOW_J: 'low_j', LOW_Q: 'low_q', LOW_K: 'low_k', LOW_A: 'low_a',
    MID_HELMET: 'mid_helmet', MID_COMPASS: 'mid_compass',
    HIGH_VIPER: 'high_viper', HIGH_ANGLER: 'high_angler', HIGH_SQUID: 'high_squid',
    HIGH_LEVIATHAN: 'apex_leviathan', WILD_MAW: 'wild_maw'
  };
  const RANK = { low: 1, mid: 2, high: 3, apex: 4, wild: 5 };
  const nearest = (step) => (step >= 4 ? 5 : step >= 2 ? 3 : 1);

  function install(A, base) {
    if (!A || typeof A !== 'object') return A;
    if (A.__moments) return A;
    A.__moments = true;
    const M = A.moments = { base: base || 'assets/sfx/', buf: {}, man: null, state: 'idle', out: null, take: {}, lastLand: -1e9, played: [] };

    const running = () => !!(A.ctx && A.master && A.ctx.state === 'running');

    // fetch and decode everything once the context exists; any failure just leaves that clip to the procedural fallback
    M.load = async () => {
      if (M.state !== 'idle' || !A.ctx) return;
      M.state = 'loading';
      try {
        const man = await (await fetch(M.base + 'moments.json')).json();
        M.man = man.clips || {};
        await Promise.all(Object.keys(M.man).map(async (name) => {
          try {
            const ab = await (await fetch(M.base + name + '.wav')).arrayBuffer();
            M.buf[name] = await A.ctx.decodeAudioData(ab);
          } catch (e) { /* this clip falls back */ }
        }));
        M.state = 'ready';
      } catch (e) { M.state = 'failed'; }
    };

    const out = () => {
      if (!M.out) { M.out = A.ctx.createGain(); M.out.gain.value = dB(root.MomentAudio.trimDb); M.out.connect(A.master); }
      return M.out;
    };

    // play(name, { db, rate, at }) -> true if it started
    const play = (name, o) => {
      if (M.state === 'idle') M.load();
      const b = M.buf[name];
      if (!b || !running()) return false;
      const O = o || {};
      try {
        const s = A.ctx.createBufferSource(), g = A.ctx.createGain();
        s.buffer = b;
        if (O.rate) s.playbackRate.value = O.rate;
        g.gain.value = dB(O.db || 0);
        s.connect(g); g.connect(out());
        s.start(O.at == null ? A.ctx.currentTime : O.at);
        M.played.push(name); if (M.played.length > 40) M.played.shift();
        return true;
      } catch (e) { return false; }
    };
    M.play = play;

    const ver = (v) => (v === 'short' ? 'short' : 'full');
    A.helpLead = (v) => play('help_' + ver(v) + '_lead');
    A.helpImpact = (v) => {
      const ok = play('help_' + ver(v) + '_impact');
      // the clip's own pre-impact dip only exists in the file: pull the bed down hard under the hit
      if (ok && typeof A.duck === 'function') { try { A.duck(-40, 5, 700); } catch (e) { /* bed stays */ } }
      return ok;
    };
    A.helpRecede = (v) => play('help_' + ver(v) + '_recede');
    // cells climb a minor scale by step; the last one is its own clip (a fifth up, longer, with a low seat under it)
    A.cellTurn = (i, n, v) => {
      // the last cell (or the only one) carries the weight; the short pass uses the shorter ring when it exists
      if (i >= n - 1) return (v === 'short' && play('help_cell_last_short')) || play('help_cell_last');
      const semi = [0, 2, 3, 5, 7, 8, 10, 12][Math.min(7, Math.max(0, i))];
      return play('help_cell', { rate: Math.pow(2, semi / 12) });
    };
    A.seam = (step) => play('seam_s' + nearest(step | 0));
    A.seamImplode = (step) => play('seam_implode_s' + nearest(step | 0), { db: -2 });
    A.symLand = (sym) => {
      const k = SYM[sym];
      if (!k || !running()) return false;
      // same 60 ms rate limit as the procedural land, so a column of stops does not machine-gun
      const t = A.ctx.currentTime, rank = RANK[k.split('_')[0]] || 0;
      // inside one 60 ms window only a MORE valuable symbol may speak over the one that got there first
      if (t - M.lastLand < 0.06) { if (rank <= M.lastRank) return true; }
      M.lastRank = rank;
      let n = 1 + Math.floor(Math.random() * 3);
      if (n === M.take[k]) n = 1 + (n % 3);
      const ok = play('sym_' + k + '_land_v' + n, { db: -3 });
      if (ok) { M.take[k] = n; M.lastLand = t; }
      return ok;
    };
    A.symWin = (sym) => { const k = SYM[sym]; return k ? play('sym_' + k + '_stinger', { db: -2 }) : false; };

    // start loading as soon as the context is created (first user gesture)
    const oInit = A.init;
    if (typeof oInit === 'function') A.init = function () { const r = oInit.apply(this, arguments); M.load(); return r; };
    if (A.ctx) M.load();
    return A;
  }

  root.MomentAudio = { install, trimDb: -8, version: 1 };
})(typeof window !== 'undefined' ? window : this);
