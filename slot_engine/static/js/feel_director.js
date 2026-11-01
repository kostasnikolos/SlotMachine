/* Game-feel director for the LIVE game — opt-in preview, only loaded with ?feel=1 (see index.html).
   Patches SlotGame.prototype at runtime (game.js is untouched) and drives the existing WebGLGameEngine planes:
   - reel kick-back, constant spin, staggered column stops with ease-out + overshoot, landing on the real server grid
   - cascade step pacing (WIN_EVALUATION + CASCADE_DROP = one step, ~1.1 s, later steps faster, total shown >= 300 ms)
   - hit-stop + decaying camera shake on heavy hits (Wild Maw landing, big cascade, Leviathan strike, tier change)
   - win-tier ladder (bet multiples) with count-up + exact-value skip, reusing the existing big-win banner
   - jurisdiction profile rules (min cycle padded at the END, turbo / slam stop, no celebration at or below stake)
   Logs to window.__FEEL_LOG; FEEL.onImpact(type) fires on contact frames and is wired to sound.js. */
(function () {
  'use strict';
  if (!window.FEEL || typeof SlotGame === 'undefined') return;
  var F = window.FEEL, T = F.T, P = F.profile, SG = SlotGame.prototype;
  var orig = { triggerSpin: SG.triggerSpin, triggerBonusBuy: SG.triggerBonusBuy, animateGridDrop: SG.animateGridDrop,
    highlightWins: SG.highlightWins, animateCreatureStrike: SG.animateCreatureStrike };
  var eng = null, cycle = null;
  var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };

  // ---------- director clock (frozen during hit-stop), driven from the engine's own render loop ----------
  var dnow = 0, last = null, freezeUntil = 0, freeze = null, waiters = [], anims = [], shake = null;
  function wait(ms) { return new Promise(function (res) { waiters.push({ at: dnow + ms, res: res }); }); }
  function tick() {
    var real = performance.now(), dt = last === null ? 0 : Math.min(100, real - last); last = real;
    if (real < freezeUntil) { freeze.frames++; dt = 0; }
    else if (freeze) { F.log('hitStopEnd', { kind: freeze.kind, actualMs: Math.round(real - freeze.t0), frames: freeze.frames }); freeze = null; }
    dnow += dt;
    anims = anims.filter(function (a) { return !a(dnow); });
    waiters = waiters.filter(function (w) { if (dnow >= w.at) { w.res(); return false; } return true; });
    if (shake) {
      var u = (real - shake.t0) / T.shakeMs, cam = eng.camera;
      if (u >= 1) { cam.position.x = 0; cam.position.y = 0; F.log('shakeEnd', { kind: shake.kind, ms: Math.round(real - shake.t0) }); shake = null; }
      else {
        var wpp = 2 * cam.position.z * Math.tan(cam.fov * Math.PI / 360) / Math.max(1, eng.canvas.clientHeight);
        var a = T.shakePx * wpp * Math.exp(-4 * u) * (1 - u);
        cam.position.x = (Math.random() * 2 - 1) * a; cam.position.y = (Math.random() * 2 - 1) * a;
      }
    }
  }
  function heavyImpact(kind, ms) {
    F.onImpact(kind, { heavy: true });
    var real = performance.now();
    freezeUntil = real + ms; freeze = { kind: kind, t0: real, frames: 0 };
    F.log('hitStopStart', { kind: kind, plannedMs: ms });
    shake = { kind: kind, t0: real }; F.log('shakeStart', { kind: kind, px: T.shakePx });
  }

  // ---------- sounds on contact frames (existing sound.js voices) ----------
  F.impactListeners.push(function (type) {
    if (typeof audio === 'undefined') return;
    if (type === 'reelStop') audio.playReelStop();
    else if (type === 'wildMaw' || type === 'bigCascade' || type === 'leviathan') audio.playJawChomp();
    else if (type === 'explode') audio.playWaterPlunge();
    else if (type === 'tier') audio.playWin();
  });

  // ---------- reels on the engine planes ----------
  function mat(id) { var m = eng.materials[id]; if (m) m.emissiveIntensity = 2.0; return m; }
  function rndId() { var k = Object.keys(eng.materials); return k[Math.floor(Math.random() * k.length)]; }
  function spinReels(game) {
    var rows = eng.rows || 5, cols = eng.cols || 5, sp = eng.symbolSpacing, d0 = dnow, turbo = P.allowTurbo && game.turbo;
    var first = turbo ? T.turboFirstStopMs : T.firstStopMs, stag = turbo ? T.turboStaggerMs : T.stopStaggerMs;
    var base = []; for (var r = 0; r < rows; r++) base.push(eng.planes[r * cols].userData.baseY);
    var strips = [];
    for (var c = 0; c < cols; c++) {
      var pl = []; for (r = 0; r < rows; r++) pl.push(eng.planes[r * cols + c]);
      strips.push({ c: c, planes: pl, o: 0, wraps: 0, phase: 'spin', stopAt: Infinity, queue: [], blur: 0 });
    }
    var ctl = { grid: null, done: false };
    function pos(t) { // kick-back -> ease-in accel -> constant speed (cells)
      var v = T.spinSpeed / 1000, K = T.kickbackCells;
      if (t < T.kickbackMs) { var u = t / T.kickbackMs; return -K * (1 - (1 - u) * (1 - u)); }
      var t1 = t - T.kickbackMs;
      if (t1 < T.accelMs) { var w = t1 / T.accelMs; return -K + v * T.accelMs * w * w / 2; }
      return -K + v * T.accelMs / 2 + v * (t1 - T.accelMs);
    }
    var landed;
    var finished = new Promise(function (res) { landed = res; });
    anims.push(function () {
      var t = dnow - d0, stopped = 0;
      strips.forEach(function (s) {
        var ds = s.stopAt - T.decelMs, ovs = T.overshootCells;
        if (s.phase === 'spin') {
          if (t < ds) { s.o = pos(t); s.blur = Math.min(1, Math.max(0, (t - T.kickbackMs) / T.accelMs)); }
          else {
            s.phase = 'decel'; s.os = pos(ds); s.ofin = Math.floor(s.os) + rows; s.D = s.ofin + ovs - s.os;
            for (var r2 = rows - 1; r2 >= 0; r2--) s.queue.push(ctl.grid[r2][s.c]);
          }
        }
        if (s.phase === 'decel') {
          var u = Math.min(1, (t - ds) / T.decelMs); s.o = s.os + s.D * (1 - (1 - u) * (1 - u)); s.blur = 1 - u;
          if (t >= s.stopAt) { // contact frame
            s.phase = 'settle'; s.o = s.ofin + ovs; s.blur = 0;
            F.log('reelStop', { col: s.c, plannedMs: Math.round(s.stopAt), atMs: Math.round(t), turbo: turbo });
            F.onImpact('reelStop', { col: s.c });
            if (ctl.grid.some(function (row) { return row[s.c] === 'WILD_MAW'; })) heavyImpact('wildMaw', T.hitStopMs);
          }
        } else if (s.phase === 'settle') {
          var e = Math.min(1, (t - s.stopAt) / T.settleMs); s.o = s.ofin + ovs * (1 - e) * (1 - e);
          if (e >= 1) { s.o = s.ofin; s.phase = 'stopped'; }
        }
        while (s.o - s.wraps >= 1) {
          s.wraps++; var p = s.planes.pop(); s.planes.unshift(p);
          var id = s.phase !== 'spin' && s.queue.length ? s.queue.shift() : rndId(), m = mat(id); if (m) p.material = m;
        }
        for (var k = 0; k < rows; k++) {
          var pl = s.planes[k]; pl.position.x = pl.userData.baseX;
          pl.position.y = base[k] - (s.o - s.wraps) * sp; pl.scale.set(1, 1 + 0.6 * s.blur, 1);
        }
        if (s.phase === 'stopped') stopped++;
      });
      if (ctl.grid && stopped === cols) { eng.updateGrid(ctl.grid); ctl.done = true; landed(); return true; }
      return false;
    });
    ctl.land = function (grid) { // schedule stops once the server grid is known
      ctl.grid = grid; var t = dnow - d0, b = Math.max(first, t + T.decelMs + 40);
      strips.forEach(function (s) { s.stopAt = b + s.c * stag; });
      return finished;
    };
    ctl.slam = function () {
      var t = dnow - d0, n = 0;
      strips.forEach(function (s) { if (s.phase === 'spin' && isFinite(s.stopAt) && t < s.stopAt - T.decelMs) s.stopAt = Math.min(s.stopAt, t + T.decelMs + n++ * T.slamStaggerMs); });
    };
    return ctl;
  }

  // DOM cells (frames + coordinates for FX) without the per-cell drop tween/sounds of the default path
  function buildDom(game, gridData) {
    game.gridEl.innerHTML = ''; game.updateGridColumnSizes(gridData.cols);
    var pearls = new Set((gridData.pearl_tokens || []).map(function (pt) { return pt[0] + ',' + pt[1]; }));
    for (var r = 0; r < gridData.rows; r++) for (var c = 0; c < gridData.cols; c++) {
      var cell = document.createElement('div'); cell.className = 'symbol-cell'; cell.id = 'cell-' + r + '-' + c;
      cell.appendChild(game.createSymbolElement(gridData.grid[r][c], pearls.has(r + ',' + c))); game.gridEl.appendChild(cell);
    }
  }

  SG.animateGridDrop = async function (gridData, speed) {
    if (!eng || !eng.planes.length || !gridData.grid) return orig.animateGridDrop.call(this, gridData, speed);
    var dims = gridData.rows === eng.rows && gridData.cols === eng.cols;
    if (!dims) { eng.updateGrid(gridData.grid); buildDom(this, gridData); return; } // grid resized (6x5): land directly
    var reels = cycle && cycle.reels && !cycle.reels.grid ? cycle.reels : spinReels(this); // free spins start their own reels
    if (cycle) cycle.phase = 'reels';
    buildDom(this, gridData);
    await reels.land(gridData.grid);
    if (cycle) { cycle.reels = null; cycle.phase = 'timeline'; }
  };

  // ---------- cascade step ----------
  function cellRectCenter(game, r, c) {
    var cell = document.getElementById('cell-' + r + '-' + c); if (!cell || !game.fx.canvas) return null;
    var cr = game.fx.canvas.getBoundingClientRect(), b = cell.getBoundingClientRect();
    return { cell: cell, x: b.left + b.width / 2 - cr.left, y: b.top + b.height / 2 - cr.top };
  }
  function pulse(coords, ms) {
    var t0 = dnow, cols = eng.cols, pl = coords.map(function (rc) { return eng.planes[rc[0] * cols + rc[1]]; }).filter(Boolean);
    anims.push(function () { var u = Math.min(1, (dnow - t0) / ms), s = 1 + 0.12 * Math.abs(Math.sin(u * Math.PI * 3));
      pl.forEach(function (p) { p.scale.set(s, s, 1); }); if (u >= 1) pl.forEach(function (p) { p.scale.set(1, 1, 1); }); return u >= 1; });
  }
  async function cascadeStep(game, data, f, heavy) {
    var E = T.explodeMs * f, Dr = T.dropMs * f, St = T.dropColStaggerMs * f, cols = eng.cols, sp = eng.symbolSpacing;
    audio.playCascade();
    var removed = data.removed_coords || [], rp = removed.map(function (rc) { return eng.planes[rc[0] * cols + rc[1]]; }).filter(Boolean);
    if (heavy) heavyImpact('bigCascade', T.hitStopMs); else F.onImpact('explode', { n: removed.length });
    removed.forEach(function (rc) { var q = cellRectCenter(game, rc[0], rc[1]); if (q) { q.cell.classList.remove('burning'); q.cell.classList.add('diving'); game.fx.spawnWaterSplash(q.x, q.y, 14); } });
    var e0 = dnow;
    anims.push(function () { var u = Math.min(1, (dnow - e0) / E), s = (1 + 0.3 * u) * (1 - u * u * u); rp.forEach(function (p) { p.scale.set(s, s, 1); }); return u >= 1; });
    await wait(E / 2);
    audio.playSteamHiss();
    removed.forEach(function (rc) { var q = cellRectCenter(game, rc[0], rc[1]); if (q) { q.cell.classList.remove('diving'); q.cell.classList.add('evaporating'); game.fx.spawnSteamCloud(q.x, q.y, 10); } });
    await wait(E / 2);
    if (window.oceanAmbient) window.oceanAmbient.scatterFish();
    var g = data.grid; if (!g || !g.grid) return;
    if (g.rows !== eng.rows || g.cols !== eng.cols) { eng.updateGrid(g.grid); buildDom(game, g); return; }
    eng.updateGrid(g.grid); // canonical materials; then offset start positions and let them fall
    var start = {}, nRemoved = {};
    removed.forEach(function (rc) { nRemoved[rc[1]] = (nRemoved[rc[1]] || 0) + 1; });
    (data.shifted_cells || []).forEach(function (sc) { start[sc.to[0] + ',' + sc.to[1]] = (sc.to[0] - sc.from[0]) * sp; });
    var moving = [];
    for (var c = 0; c < cols; c++) {
      var n = nRemoved[c] || 0; if (!n) continue;
      for (var r = 0; r < eng.rows; r++) {
        var p = eng.planes[r * cols + c], key = r + ',' + c, dy = r < n ? n * sp : start[key];
        if (dy) { p.position.y = p.userData.baseY + dy; moving.push({ p: p, c: c, dy: dy }); }
      }
    }
    buildDom(game, g);
    var d0 = dnow, fall = Dr - (eng.cols - 1) * St, hit = {};
    anims.push(function () {
      var all = true;
      moving.forEach(function (m) {
        var u = Math.min(1, Math.max(0, (dnow - d0 - m.c * St) / fall)), b = m.p.userData.baseY;
        if (u < 1) all = false;
        if (u < 0.8) { var w = u / 0.8; m.p.position.y = b + m.dy * (1 - w * w); m.p.scale.set(1, 1, 1); }
        else { var v = (u - 0.8) / 0.2, sq = Math.sin(Math.PI * v); m.p.position.y = b + T.dropBounceCells * sp * sq; m.p.scale.set(1 + 0.08 * sq, 1 - 0.12 * sq, 1);
          if (!hit[m.c]) { hit[m.c] = 1; F.onImpact('drop', { col: m.c }); } }
        if (u >= 1) { m.p.position.y = b; m.p.scale.set(1, 1, 1); }
      });
      return all;
    });
    await wait(Dr);
    game.clearVents();
  }

  // ---------- win ladder ----------
  var flash = null;
  function doFlash() {
    if (!flash) { flash = document.createElement('div'); flash.style.cssText = 'position:fixed;inset:0;background:#fff;opacity:0;pointer-events:none;z-index:99999'; document.body.appendChild(flash); }
    flash.style.opacity = '0.5'; setTimeout(function () { flash.style.opacity = '0'; }, T.flashMs);
  }
  function celebrate(game, total, cyc) {
    var b = game.bet, mult = total / b, stake = cyc.stake;
    if (total <= 0) return Promise.resolve();
    if (total <= stake && !P.celebrateAtOrBelowStake) { F.log('win', { celebrate: false, total: total, stake: stake }); return Promise.resolve(); }
    var top = F.tierFor(mult), dur = top ? top.countMs : T.smallWinCountMs, c0 = dnow, next = 0, shown = 0;
    var banner = document.getElementById('big-win-banner'), amt = document.getElementById('big-win-amount');
    var titleEl = banner && banner.querySelector('.big-win-title'), oldTitle = titleEl && titleEl.textContent;
    var out = top && banner ? amt : game.winEl;
    if (top && banner) { titleEl.textContent = ''; banner.classList.add('active'); }
    F.log('countStart', { target: total, mult: Math.round(mult * 100) / 100, durMs: dur, tier: top ? top.id : null });
    function reach(t, skipped) {
      if (titleEl) titleEl.textContent = t.label;
      F.log('tier', { id: t.id, threshold: t.mult, mult: Math.round(shown / b * 100) / 100, skipped: !!skipped });
      heavyImpact('tier', T.tierHitStopMs); doFlash();
    }
    return new Promise(function (resolve) {
      function finish(skipped) {
        shown = total; out.textContent = '$' + total.toFixed(2);
        while (next < T.tiers.length && T.tiers[next].mult <= mult) { if (T.tiers[next] === top) reach(top, skipped); next++; }
        F.log('countEnd', { value: total, shownText: out.textContent, skipped: !!skipped });
        cyc.skip = null; game.spinBtn.disabled = true;
        wait(T.holdAfterCountMs).then(function () {
          if (top && banner) { banner.classList.remove('active'); if (titleEl) titleEl.textContent = oldTitle; }
          game.winEl.textContent = '$' + total.toFixed(2); resolve();
        });
      }
      function count() {
        var u = Math.min(1, (dnow - c0) / dur), v = 1 - Math.pow(1 - u, T.countEaseExp);
        shown = total * v; out.textContent = '$' + shown.toFixed(2);
        while (next < T.tiers.length && shown / b >= T.tiers[next].mult) reach(T.tiers[next++]);
        if (u >= 1) { finish(false); return true; }
        return false;
      }
      cyc.skip = function () {
        if (dnow - c0 < T.skipAfterMs) { F.log('skipTooEarly'); return; }
        F.log('skipInput', { inputF: cyc.inputF }); anims = anims.filter(function (a) { return a !== count; });
        finish(true); F.log('skipLanded', { value: total });
      };
      game.spinBtn.disabled = false; // the spin button acts as SKIP during the count-up
      anims.push(count);
    });
  }

  // ---------- timeline (same events/handlers as game.js, feel pacing) ----------
  SG.playbackTimeline = async function (outcome) {
    var game = this, cyc = cycle, turbo = P.allowTurbo && game.turbo, speed = turbo ? 0.35 : 1.0;
    var stake = cyc ? cyc.stake : game.bet, total = outcome.total_payout || 0;
    var quiet = total <= stake && !P.celebrateAtOrBelowStake; // RTS 14F: show amounts/lines, no celebration
    var step = 0, open = null, totalSpins = 0, spinNum = 1;
    for (const ev of outcome.events) {
      var d = ev.data, ti = performance.now();
      switch (ev.event_type) {
        case 'FEATURE_ACTIVATED': {
          if (game.freeSpinsHud) {
            game.freeSpinsHud.style.display = 'flex';
            var title = 'ABYSSAL EXPEDITION';
            if (d.type === 'STANDARD_BONUS_AWARDED') title = 'ABYSSAL DESCENT (100X)';
            if (d.type === 'ULTRA_BONUS_AWARDED') title = 'LEVIATHAN AWAKENING (350X)';
            if (d.type === 'MYSTERY_STANDARD_AWARDED') title = 'MYSTERY: ABYSSAL DESCENT';
            if (d.type === 'MYSTERY_ULTRA_AWARDED') title = 'MYSTERY: LEVIATHAN ULTRA!';
            game.hudModeTitle.textContent = title; totalSpins = d.spins || 6;
            game.hudSpinCounter.textContent = 'BANKED: ' + totalSpins + ' FREE SPINS';
          }
          audio.playSonarPing(); await sleep(600 * speed); break;
        }
        case 'SPIN_STARTED':
          game.currentDepthLevel = d.depth_level; audio.playMeterAbsorb();
          game.updateDepthProgress(d.depth_level, d.depth_meters, d.accumulated_points); game.updatePurgedRunes(d.purged_symbols || []);
          if (d.is_free_spin && game.freeSpinsHud) {
            game.freeSpinsHud.style.display = 'flex';
            game.hudSpinCounter.textContent = 'FREE SPIN ' + spinNum + ' (' + d.spins_remaining + ' LEFT)'; spinNum++;
            if (game.hudMultiplier) game.hudMultiplier.textContent = (d.spin_multiplier || 1) + 'X BOOST';
          }
          step = 0; break;
        case 'GRID_EXPANSION_6X5':
          game.gridEl.classList.add('grid-6x5');
          if (game.ventsEl) { game.ventsEl.classList.add('grid-6x5'); var v5 = document.getElementById('vent-5'); if (v5) v5.style.display = 'flex'; }
          game.cols = 6; audio.playCreatureRoar(); if (window.oceanAmbient) window.oceanAmbient.scatterFish();
          await sleep(450 * speed); break;
        case 'GRID_DROP':
          await game.animateGridDrop(d, speed); break;
        case 'VENTS_ERUPTED':
          game.showVents(d.active_vents); audio.playVentEruption(); await sleep(350 * speed); break;
        case 'WIN_EVALUATION': {
          step++; var f = F.chainFactor(step);
          open = { step: step, f: f, t0: performance.now(), inter: 0, pay: d.step_payout || 0 };
          F.log('stepStart', { step: step, factor: Math.round(f * 100) / 100 });
          game.currentWin = d.cumulative_payout; game.updateStats(); // running total visible from the first highlight frame
          F.log('stepWin', { step: step, total: d.cumulative_payout });
          pulse([].concat.apply([], d.wins.map(function (w) { return w.coords; })), T.highlightMs);
          var saved = null;
          if (quiet) { // keep the lines + amount, drop celebratory sound/VFX
            saved = [audio.playWin, audio.playSoulBurn, game.fx.spawnBurnEmbers, game.fx.spawnSoulFlight];
            audio.playWin = audio.playSoulBurn = function () {}; game.fx.spawnBurnEmbers = game.fx.spawnSoulFlight = function () {};
            audio.playReelStop();
          }
          try { await orig.highlightWins.call(game, d.wins, d.cumulative_payout, T.highlightMs / 650); }
          finally { if (saved) { audio.playWin = saved[0]; audio.playSoulBurn = saved[1]; game.fx.spawnBurnEmbers = saved[2]; game.fx.spawnSoulFlight = saved[3]; } }
          if (d.accumulated_points !== undefined) { audio.playMeterAbsorb(); game.updateDepthProgress(d.depth_level, d.depth_meters, d.accumulated_points); }
          break;
        }
        case 'LEVEL_UP':
          audio.playLevelUp(); audio.playSonarPing();
          game.showLevelUpSplash(d.new_level, d.name, d.depth, d.spins_added);
          game.updateDepthProgress(d.new_level, d.depth, d.accumulated_points || 0);
          if (d.purged && d.purged.length > 0) game.updatePurgedRunes(d.purged);
          await sleep(T.depthLevelUpMs * speed); break;
        case 'CASCADE_DROP': {
          var fc = open ? open.f : 1;
          // heavy only when the step really is big: >= 5x bet paid or >= 14 symbols cleared
          await cascadeStep(game, d, fc, (open && open.pay >= 5 * game.bet) || (d.removed_coords || []).length >= 14);
          await wait(T.pauseMs * fc);
          if (open) { F.log('stepEnd', { step: open.step, ms: Math.round(performance.now() - open.t0 - open.inter), interMs: Math.round(open.inter) }); open = null; }
          break;
        }
        case 'CREATURE_LIFELINE_STRIKE': {
          var lv = game.leviathan3D, rd = lv && lv.riseAndDevour;
          if (lv) lv.riseAndDevour = function (cells, cb) { return rd.call(lv, cells, function () { heavyImpact('leviathan', T.hitStopMs); if (cb) cb.apply(this, arguments); }); };
          try { await orig.animateCreatureStrike.call(game, d, speed); } finally { if (lv) lv.riseAndDevour = rd; }
          break;
        }
        case 'PEARLS_COLLECTED':
          audio.playSoulAbsorb(); await sleep(250 * speed); break;
        case 'MAX_WIN_CAP_TRIGGERED':
        case 'SPIN_COMPLETE': {
          game.balance += outcome.total_payout; game.currentWin = outcome.total_payout; game.updateStats();
          var resetDelay = (outcome.feature_type && outcome.feature_type !== 'NONE') ? 3500 : 1200;
          setTimeout(function () {
            if (game.freeSpinsHud) game.freeSpinsHud.style.display = 'none';
            if (game.cols === 6) {
              game.gridEl.classList.remove('grid-6x5');
              if (game.ventsEl) { game.ventsEl.classList.remove('grid-6x5'); var v = document.getElementById('vent-5'); if (v) v.style.display = 'none'; }
              game.cols = 5;
            }
            if (game.xbetActive) { game.updatePurgedRunes(['LOW_10']); game.updateDepthProgress(1, 500, 15); }
            else { game.updatePurgedRunes([]); game.updateDepthProgress(0, 0, 0); }
          }, resetDelay);
          break;
        }
      }
      // time spent in non-cascade beats inside an open step is excluded from the step duration
      if (open && ev.event_type !== 'WIN_EVALUATION' && ev.event_type !== 'CASCADE_DROP') open.inter += performance.now() - ti;
    }
    if (cyc) {
      cyc.phase = 'count'; await celebrate(game, total, cyc);
      cyc.phase = 'pad';
      var el = performance.now() - cyc.pressT, pad = Math.max(0, P.minCycleMs - el);
      F.log('pad', { ms: Math.round(pad), beforePadMs: Math.round(el) });
      if (pad) await sleep(pad); // never slows the reels: the minimum cycle is padded at the END
    }
  };

  // ---------- cycle bookkeeping (press -> start re-enabled) ----------
  function begin(game, kind, pressT) {
    var stake = kind === 'spin' ? (game.xbetActive ? game.bet * 2 : game.bet) : game.__feelBuyCost;
    cycle = { game: game, kind: kind, pressT: pressT, stake: stake, phase: 'reels' };
    F.log('press', { kind: kind, profile: P.id, bet: game.bet, stake: stake, turbo: !!(P.allowTurbo && game.turbo) });
    if (kind === 'spin' && eng && eng.planes.length) cycle.reels = spinReels(game);
  }
  function end(game) {
    if (!cycle) return;
    F.log('cycleEnd', { kind: cycle.kind, cycleMs: Math.round(performance.now() - cycle.pressT), won: game.currentWin, stake: cycle.stake, minCycleMs: P.minCycleMs });
    cycle = null; window.__FEEL_CYCLE_DONE = (window.__FEEL_CYCLE_DONE || 0) + 1;
  }
  SG.triggerSpin = async function () {
    var was = this.isSpinning, t = performance.now(), p = orig.triggerSpin.call(this);
    if (!was && this.isSpinning) begin(this, 'spin', t);
    await p; if (!was) end(this);
  };
  SG.triggerBonusBuy = async function (type) {
    var was = this.isSpinning, t = performance.now();
    this.__feelBuyCost = this.bet * (type === 'ULTRA_BONUS_350X' ? 350 : type === 'MYSTERY_BUY_200X' ? 200 : 100);
    var p = orig.triggerBonusBuy.call(this, type);
    if (!was && this.isSpinning) begin(this, 'bonus', t);
    await p; if (!was) end(this);
  };

  // input during a cycle: skip (count-up), slam stop (reels; only where allowed)
  function onInput(e) {
    if (!cycle) return;
    cycle.inputF = F.frame();
    if (cycle.skip) { e.preventDefault(); e.stopImmediatePropagation(); cycle.skip(); return; }
    if (cycle.phase === 'reels' && cycle.reels) {
      e.preventDefault();
      if (P.allowSlamStop) { F.log('slam'); cycle.reels.slam(); } else F.log('slamIgnored', { profile: P.id });
    }
  }
  window.addEventListener('keydown', function (e) { if (e.code === 'Space' && !e.repeat) onInput(e); }, true);
  document.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('#btn-spin, #big-win-banner')) onInput(e); }, true);

  // ---------- boot: hook the engine's render loop, apply profile restrictions ----------
  (function boot() {
    if (!window.webglEngine || !window.__RENDER_READY || !window.slotGame) return setTimeout(boot, 50);
    eng = window.webglEngine;
    var r = eng.render; eng.render = function (time) { tick(); return r.call(eng, time); };
    if (!P.allowTurbo) {
      window.slotGame.turbo = false;
      var tb = document.getElementById('btn-turbo'); if (tb) { tb.disabled = true; tb.classList.remove('active'); tb.title = 'Turbo unavailable (' + P.id + ')'; }
    }
    if (typeof audio !== 'undefined') { // tag celebratory voices so the gate can audit LDW spins
      var pw = audio.playWin; audio.playWin = function () { F.log('celebrationSound', { voice: 'playWin' }); return pw.apply(audio, arguments); };
    }
    window.FEEL_DIRECTOR = { heavyImpact: heavyImpact, state: function () { return cycle; } };
    window.__FEEL_READY = true; F.log('ready', { profile: P.id });
  })();
})();
