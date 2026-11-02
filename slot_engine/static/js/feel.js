/* Game-feel config + timeline log for the LIVE game (opt-in preview: loaded by index.html only with ?feel=1).
   Source of numbers: docs/game_feel_teardown.md. Presentation only: never changes server outcomes.
   Every timing is a named, tunable value. Override any of them from the URL: ?feel.highlightMs=500
   Jurisdiction profile: ?profile=mga (default) | ukgc | de. Minimum cycles are met by padding the END of the cycle. */
(function () {
  'use strict';
  var Q = new URLSearchParams(location.search);

  var T = {
    // base spin (5 columns, reel-style)
    kickbackMs: 80, kickbackCells: 0.15,          // wind-up before the spin, in symbol heights
    accelMs: 150,                                 // ease-in quad to full speed
    spinSpeed: 25,                                // symbols / second at full speed
    firstStopMs: 900,                             // press -> first column contact
    stopStaggerMs: 160,                           // between column stops
    decelMs: 480,                                 // ease-out into the stop (velocity-matched to spinSpeed)
    overshootCells: 0.12, settleMs: 120,          // stop overshoot + back-out settle
    anticipationExtraMs: 900, anticipationSpeed: 0.4, // reserved: only for real near-feature states
    // turbo / slam (only where the profile allows them)
    slamStaggerMs: 40, turboFirstStopMs: 300, turboStaggerMs: 40,
    // cascade step (~1.95 s; slowed twice 2026-11-02 at the user's request: hits and refills read too fast)
    highlightMs: 750,                             // win highlight + running total shown (never compressed)
    explodeMs: 480,
    dropMs: 520, dropColStaggerMs: 34, dropBounceCells: 0.06, // per-column fall = dropMs - 4*stagger (220 ms)
    pauseMs: 200,
    chainAccelAfter: 3, chainAccelPerStep: 0.08, chainFloor: 0.7, // speeds explode/drop/pause only
    minWinVisibleMs: 300,
    // impacts
    hitStopMs: 67,                                // ~4 frames @60 (gate: 3-6 frames)
    tierHitStopMs: 83,                            // ~5 frames on tier change
    shakePx: 6, shakeMs: 250,                     // exponential decay, hard zero at shakeMs (gate: <= 300 ms)
    flashMs: 33,                                  // <= 2 frames white flash on tier change
    // win ladder (thresholds are bet multiples)
    tiers: [
      { id: 'big', label: 'BIG WIN', mult: 15, countMs: 3000 },
      { id: 'mega', label: 'MEGA WIN', mult: 40, countMs: 5000 },
      { id: 'epic', label: 'EPIC WIN', mult: 100, countMs: 8000 },
      { id: 'abyssal', label: 'ABYSSAL WIN', mult: 500, countMs: 12000 }
    ],
    smallWinCountMs: 1200,                        // count-up for wins above stake but below the first tier
    countEaseExp: 1.756,                          // 1-(1-u)^p : 80% of the value at 60% of the time
    skipAfterMs: 500, holdAfterCountMs: 1000,
    // features (not wired in the prototype yet)
    featureIntroMs: 4000, featureSkipAfterMs: 1500, depthLevelUpMs: 2500
  };
  Object.keys(T).forEach(function (k) { if (Q.has('feel.' + k) && typeof T[k] === 'number') T[k] = parseFloat(Q.get('feel.' + k)); });

  var PROFILES = {
    mga:  { id: 'mga',  minCycleMs: 0,    allowTurbo: true,  allowSlamStop: true,  allowAutoplay: true,  celebrateAtOrBelowStake: true },
    ukgc: { id: 'ukgc', minCycleMs: 2600, allowTurbo: false, allowSlamStop: false, allowAutoplay: false, celebrateAtOrBelowStake: false }, // RTS 14D/E/F, 8C
    de:   { id: 'de',   minCycleMs: 5100, allowTurbo: false, allowSlamStop: false, allowAutoplay: false, celebrateAtOrBelowStake: false }  // GlueStV 2021 s22a
  };
  PROFILES['default'] = PROFILES.mga;
  var profile = PROFILES[(Q.get('profile') || 'mga').toLowerCase()] || PROFILES.mga;

  // frame counter (for "within N frames" checks) + timeline log
  var frame = 0;
  (function tick() { frame++; requestAnimationFrame(tick); })();
  var LOG = window.__FEEL_LOG = [];
  function log(type, data) {
    var e = { t: Math.round(performance.now() * 10) / 10, f: frame, type: type };
    if (data) for (var k in data) e[k] = data[k];
    LOG.push(e); return e;
  }

  // Sound hook: fires on the contact frame of every impact. Register with FEEL.impactListeners.push(fn).
  var impactListeners = [];
  function onImpact(type, data) {
    log('impact', Object.assign({ kind: type }, data || {}));
    for (var i = 0; i < impactListeners.length; i++) try { impactListeners[i](type, data); } catch (e) { console.error(e); }
  }

  function chainFactor(step) { // step is 1-based
    if (step <= T.chainAccelAfter) return 1;
    return Math.max(T.chainFloor, 1 - T.chainAccelPerStep * (step - T.chainAccelAfter));
  }
  function tierFor(mult) { var r = null; T.tiers.forEach(function (t) { if (mult >= t.mult) r = t; }); return r; }

  window.FEEL = { T: T, profiles: PROFILES, profile: profile, log: log, onImpact: onImpact, impactListeners: impactListeners,
    chainFactor: chainFactor, tierFor: tierFor, frame: function () { return frame; } };
  log('profile', { profile: profile.id, minCycleMs: profile.minCycleMs, tiers: T.tiers.map(function (t) { return t.mult; }), hitStopMs: T.hitStopMs, tierHitStopMs: T.tierHitStopMs, shakeMs: T.shakeMs });
})();
