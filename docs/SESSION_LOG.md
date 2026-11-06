# Session Log

Read this first on any PC. Newest entry on top. Each entry: date, branch, what changed, what's next.

---

## 2026-11-06 — `visual/ai-studio-pipeline` — pressure package on (B + C), engine recalibrated

**Done**
- `slot_engine/config/features.py`: B pressure multiplier ON (+0.5x per level descended, cap 4x) and C bite retrigger ON (15% per bite during free spins, +1 spin, cap 3 per round). Crush depth stays on.
- Rebalanced so every mode is within +/-2 pts of 96.05% of its cost with both on: thresholds L3 24->32, L4 100->126, L5 200->285 (`symbols.py`); Level-0 table wild 2.09->1.5 units and a highs->mids shift (`weights.py`); Level-5 table wild 1->0, sediment 3->4. Paytable, bought spins, natural spin awards untouched.
- Full gate: base 97.5 (hit 31.1%), xBet 98.1, Standard 95.8, Ultra 95.6, Mystery 97.2; sediment <= 4%. Fast gate re-pinned (`artifacts/math_baseline.json`), full table in `artifacts/math_gate_full.txt`. API gate against a restarted server on 8080: PASS.
- `docs/math_calibration.md` "Pressure package calibration": 38-row attempt table, the levers and their couplings, final weights, win-bucket split, trade-offs (natural Core from the base game ~0%, Standard ascension 12% -> 2%, no table wild at L5).

**Next**
- Front end: `WIN_EVALUATION.pressure_multiplier` and `CREATURE_LIFELINE_STRIKE.spins_added` now carry real values; the depth gauge follows the new thresholds via `/api/slot/paytable`.
- If the owner wants the natural Core back in the base game: L5 threshold 285 -> ~240, recover ~5-8 pts from the L0 wild.

---

## 2026-11-01 → 11-03 — `visual/ai-studio-pipeline` — canvas becomes the front end

**Decision (user):** the Design canvas "The Descent: Abyssal Leviathan" (https://claude.ai/artifact/Qh5cU4RMbQ4KRmAsLPGpvB) is the look. Porting it piece by piece into the old UI was rejected; instead the canvas's own code now runs as the game front end.

**Done**
- `slot_engine/static/canvas/`: the canvas artboard as `index.html` (asset `/_blob/<id>` urls rewritten to `assets/`), `support.js` = the Design runtime (bundles React 18; self-boots on `<x-dc>` and works outside the editor), `assets/` = Three.js r1xx build, 4 PBR symbol atlases (albedo/normal/emissive/aux), Leviathan geo JSON ×3 + PBR jpgs. ~11MB.
- `index.html` spin(): outcome now comes from `POST /api/slot/spin` / `/api/slot/buy-bonus` (same event schema the canvas simulator emitted: SPIN_STARTED, GRID_DROP, WIN_EVALUATION, CASCADE_DROP, LEVEL_UP, CREATURE_LIFELINE_STRIKE, …). `?engine=local` keeps the built-in simulator; it is also the fallback if the API is down. Per-event try/catch so an unknown payload can't kill a round.
- Verified headless: 3 real spins, balance tracks payouts, no page errors. `GET /canvas` route added in `slot_engine/api/app.py` (restart uvicorn to pick it up).
- Earlier the same day: grid alignment + endless-spin bugs fixed in the OLD front end (`WebGLGameEngine.alignToCells`, `game.js`), `?feel=1` game-feel preview, `?look=canvas` step-1 chrome (`look_canvas.css`) — the latter is superseded by the canvas front end and can be removed.

**Open**
- Bonus buy verified through the API (STANDARD_BONUS_100X: 41 events incl. strike + vents, balance 1000 → 956 for a 56 payout, no errors). xBet not yet exercised. API has no UNDERTOW event.
- Director bar: still drives the simulator's levels; with the API, L1–L5 jump buttons only change visuals. Decide whether to keep it behind a flag.
- Portrait mode DONE (2026-11-01): 1080×1920 stage auto-chosen when the window is taller than wide (`?orient=portrait|landscape`); side panels collapse into one instrument strip, footer stacks, Director hidden, cells 187 stage px (≈64px on a 390 phone). Captures: `artifacts/canvas/portrait_*.png`; `scripts/canvas/portrait_capture.py`. Known: ~90px dead space between strip and footer; abyss gauge is a rotated column without zone labels; Leviathan rarely in view in portrait; big-win 3D composition tuned for landscape.
- Dark audio DONE (2026-11-01): `slot_engine/static/canvas/audio_dark.js` patches the game's audio object (`DarkAudio.install`) — procedural reverb bus + compressor + ducking; dissolve/land/chomp/impact/riser/roar/win/levelUp/setLevel/tier/tick replaced per `docs/feel_design_plan.md` §B; bubbles kept for ambience only. `?audio=classic` restores the old set. Lab: `/static/canvas/audio_lab.html`; WAVs in `artifacts/canvas/audio/`. Next from the plan: escalating big-win screens (§C).
- Leviathan presence DONE (2026-11-02, plan §A items 1–6, 9): rationed reveal (idle mean 0.1, never >0.6 in base game), `levPreStrike()` hush + stillness before strikes, look-at (`levAttend`: cascade cells / pointer / near-miss hold), `uBreath` breathing, 3 spring-chain tendrils (merged mesh), `uPulse` from `A.lowBand()` (analyser 40–120Hz), `levReact('loss'|'win')`, camera push-in + idle orbit. 60fps p95 16.8ms. Debug hooks: `window.__levAttention({x,y,hold})`, `__levReact(kind)`, `__levFps()`. Captures `artifacts/canvas/lev_*.png`, `scripts/canvas/lev_capture.py`. Known: at Director L2 the body sits mostly behind the right panel; tendrils hidden by the body during strikes.
- Cascade pacing slowed twice at the user's request (phone test): feel.js highlight 750 / explode 480 / drop 520 (stagger 34) / pause 200 ≈ 1.95s per step; gate window widened to 900–2300ms; PASS (steps 1678–1961ms).
- **Math fix (2026-11-02)** — user report: purged seats showed as empty, esp. in the ultra bonus. Cause: engine weights filled purged mass with `DEAD_SEDIMENT` blockers (110/150/200 at L3–L5 → 48–67% of cells); pre-existing, not caused by the front-end work. Baseline Monte Carlo was also off: base 57%, standard 117%, ultra 40%. Fix (`weights.py`, `symbols.py` paytable rescale, `rtp_profiles.py`, depth thresholds 6/13/24/100/200, L1/L2 natural spins +2): purged lows → mids/highs, sediment ≤3.6%; full gate PASS: base 98.2±2 (seed noise), xBet 92.6, standard 95.8, ultra 95.2, mystery 96.6 (% of each mode's cost). Gate: `python scripts/math_check.py [--full] [--api URL]` → run after EVERY engine change. Details `docs/math_calibration.md`. Front end now reads depth thresholds/natural spins from `/api/slot/paytable` (fallback = canvas defaults). Open: base hit frequency 49% (target ~28%) — needs rows/symbol-count change; base/xBet seed noise ±3pts at 200k.
- **Big-win ladder DONE (2026-11-03, plan §C)** on top of the existing 3D fall (`bwFx.esc`, `bwEscalate/bwEscStep/bwChip/bwStutter` in `index.html`): T1 15× luminance 0.9; T2 40× 0.75 + cool grade + 10 eye pairs (kind-2 glint billboards in camera space) opening 150 ms apart and creeping toward the number, creature density ×2; T3 100× 0.6 + 6% fov push + 4 breachers (viperfish/fish) lunging to the faceplate with a refraction wobble (`uWobble`), glass chips on the overlay, two count stutters (same total duration), number scale 1.0→1.25 (`.bwamtw --as`), cracked-glass text; T4 500× 500 ms blackout + hush, then the Leviathan's eye/face in camera space behind the number, cracks propagating over ~2 s, 8 px/300 ms shake, 1.5× slam (`.slam4`). Post uniforms `uDim/uCool/uWobble`. Kickers renamed per plan. Capture: `python scripts/canvas/bigwin_capture.py [--portrait]` → `artifacts/canvas/bigwin_*.png` + `bigwin_report.json` (drives `__canvasGame.celebrate()` directly; 60 fps p95 17.2 ms during T4, no page errors). Known: the "mouth open" of T4 is the existing face sphere (no mouth geometry); the eye-pair "tracking" is a drift toward the number, not a pupil look-at.
- **Leviathan → 2.5D hero shots (2026-11-03, user's choice: "the Nolimit way", like Beheaded's painted character).** The full procedural body is now a silhouette only in everyday view (`levUpdate` ceiling ≈0.2–0.45 when the hero layer is on); close-ups are painted hero shots played by `slot_engine/static/canvas/hero.js` on its own WebGL canvas (`data-hero`, z `heroZ`): depth-parallax from the pointer + drift, breathing scale, depth fog, chromatic aberration, motes, alpha envelope. Shots: `lev_eye` (loss reaction, replaces the 3D peek), `lev_jaws` (the bite, 3× the strike zone), `lev_rise` (level-up, under the card), `lev_maw` (reserved for max win). `?hero=0` disables. Art pipeline (free route): prompt pack `docs/prompt_packs/p3_leviathan_hero.md` (from `scripts/ai/prompts/p3_leviathan_hero.json`) → save Gemini results to `generated/inbox/p3_leviathan_hero/<id>_<n>.png` → `python scripts/ai/hero_prep.py [--pick lev_eye=2]` → cut-out + pseudo-depth (distance transform + luminance) + `assets/hero/hero.json`. Real paintings landed the same evening (user, Gemini app): all four shots in `assets/hero/` come from `generated/inbox/p3_leviathan_hero/lev_*_1.jpg`; `hero_prep.py` keys `lev_rise` harder (0.07:0.22) and clips everything above 30% of its height (light shaft). While a hero shot is up the 3D body's forced reveal is capped at 0.3. `--placeholder` still regenerates the stand-ins if needed. `lev_maw` is wired into the 500× big-win tier: after the blackout it fills the frame (cover, z 9, between the 3D fall and the number) in place of the procedural face, held until the screen closes (`hero.stop(650)`); the max-win Core keeps the 3D eye. The P1 backdrop set the user generated (trench far/mid, silhouette, frame) is in `generated/inbox/p1_backdrop_frame/` (trench_far_1 needs re-saving: my crop cut its lit top). Capture: `python scripts/canvas/hero_capture.py` → `artifacts/canvas/hero_{idle,eye,jaws,rise}.png`, no page errors. The GLB route was rejected: `custom_leviathan.glb` is 68 MB, unrigged; only `shark.glb` is rigged.
- **Reviewer loop on the Leviathan hero shots (2026-11-03/04): 5 rounds, all five moments PASS** against a Nolimit/Beheaded bar (gates: integration, life, staging, scale, grade; PASS = every gate >= 4). Builder/reviewer were separate agents; evidence = stills + frame-burst contact sheets (`hero_*_seq.png`: 60 ms steps for blinks via the capture-only frozen hero clock `H.freezeAt`, 250 ms for the maw, 1 s for idle). What it took (commits d0a4134 → a2e7be1): one compositing contract (opaque paintings, feathered edges, enter/exit by movement, procedural body hidden during shots); region-level life in one shader with rig uniforms (iris tracking, 310 ms two-layer blink with a membrane lid, jaw-hinge slam on the chomp held through the hit-stop then a 450 ms drop, travelling nodule wave, maw gulp + lure pulse on count ticks + slow closing threat); staging (eye slides in from the right to reel 5 and recedes, name card revealed on the hit-stop opposite the cell, level card moved to the upper third with an 800 px head under it, maw behind the number with Trench water + fog noise in the 16:9 side bands); grade (creature lit cyan only, fog takes the level grade, bite particles are Biolume discs, no outlined rings). Idle silhouette = plated Trench mass hidden behind the HUD panels. flog events: heroPlay/heroChomp/heroDrop/heroEnd. Remaining polish (non-blocking): rise lid seam at 3×; optional 16:9 outpaint of the maw painting; feel gate PASS throughout.
- **Crush depth shipped (2026-11-06)** — `slot_engine/config/features.py` (A on; B pressure multiplier and C bite retrigger implemented in `state_machine.py` but OFF: measured too hot, see `docs/math_calibration.md`). Engine emits `PRESSURE_CRUSH` when a base round never leaves L0 and returns < 1% of the stake; base hit frequency 49% → 30.7%, RTP unchanged, full gate PASS, baseline re-pinned. Front end: the board darkens under a pressure thud and the frame card reads "CRUSHED BY PRESSURE" (`case 'PRESSURE_CRUSH'`), never a celebration. **Math guard**: `python scripts/math_check.py --pin artifacts/math_baseline.json` runs in CI (`.github/workflows/math-gate.yml`) and in the pre-commit hook (`git config core.hooksPath .githooks`); re-pin with `--write-pin` on purpose only. Feature research + options: `docs/feature_ideas_brief.md`. Next: calibrate B+C (rebalance descent frequency: thresholds up, deep weights down) as its own job with the gate; each feature gets a visual beat (multiplier on the depth gauge, retrigger reveal on the bite card).
- LAN test server: `python -m uvicorn slot_engine.api.app:app --host 0.0.0.0 --port 8081` → phone at http://<pc-ip>:8081/canvas (firewall already allows python). TODO: serve the canvas front end at `/` and move the old UI to `/legacy`.
- Game feel applied to the canvas front end (loads `../js/feel.js`; `?profile=mga|ukgc|de`): cycle padding at end, turbo/autoplay off + slam ignored + quiet LDWs under ukgc/de, cascade step ≈1.0–1.2s with chain factor, hit-stop 4–5 frames + 250ms shake on Wild Maw / Leviathan / big cascade / tier, ladder 15/40/100/500× with exact skip. Checker: `python scripts/canvas/feel_check_canvas.py --profiles mga,ukgc` → OVERALL PASS (re-run by the orchestrator). Canvas's own ladder (50/100/500/1000×) and 2.1s cascade step were replaced by the teardown numbers.

---

## 2026-10-29 — `visual/ai-studio-pipeline`

**Decisions (user)**
- The EXISTING game (`slot_engine/static/index.html`, medallion symbols, ocean ambient, current HUD) is the visual baseline. User rejected stage_v2 and the cut-out Gemini symbols in-game ("already state is better"). stage_v2 is paused, kept as an experiment.
- Rule from now on: run the real game, preview changes non-destructively inside it, let the user judge before editing files.

**Done**
- Game feel ported into the live game as an opt-in preview: `slot_engine/static/js/feel.js` + `js/feel_director.js`, loaded only with `?feel=1` (2-line guarded include in `index.html`). Profiles: `&profile=mga|ukgc|de`.
- `scripts/stage_v2/feel_check_live.py`: no-flag visual parity + real spins/bonus buy per profile. Result: OVERALL PASS (parity, G1, G2 under ukgc, G4, G5, G6).
- Local ComfyUI + SDXL + ControlNet Union at `C:\Users\kosta\AI\ComfyUI` (venv, CUDA 12.8). Shape-locked glyphs work (3/3 correct letters vs 0/3 prompt-only); `scripts/ai/comfy_generate.py`. Not used in game.

**Fixed (2026-10-30): broken grid in the live game** (both with and without `?feel=1`)
- `WebGLGameEngine.js`: camera was placed by a formula (`max(72, …)`), so at narrow/mobile widths the 3D symbols overflowed the HTML cells. New `alignToCells()` measures `#cell-0-0` and the last cell and positions the camera so the 3D grid lands on them (±1px measured at 600 and 390 wide); re-aligns on ResizeObserver and every 10 idle frames (banner show/hide moves the grid without a resize).
- `game.js`: after the result landed, `animateGridDrop` called `webglEngine.startSpin()` again, leaving the 3D layer spinning forever over the finished board. Spin now starts on the button/bonus press; landing only plays the squash bounce.
- Cache tags bumped (`WebGLGameEngine.js?v=48817`, `game.js?v=48816`). Desktop look unchanged (side-by-side checked); `feel_check_live.py` parity baseline `artifacts/current_game_desktop.png` predates the fix, so its grid-region diff now reads high — re-capture the baseline.

**Open**
- Hit-stop sometimes freezes only 2 frames (gate says 3–6); skip jumps straight to the final tier.
- Gate items 3 (audio sync) and 7 (honest anticipation) not checked yet.
- Next candidate: medallion-style low symbols to replace the RUNESTONE tiles (preview first).

---

## 2026-10-28 (later) — `visual/ai-studio-pipeline`

**Done**
- Gemini API: key works but free tier has 0 image quota → user chose free route. `scripts/ai/prompt_pack.py` turns manifests into copy-paste packs (`docs/prompt_packs/`) for the Gemini app; save results to `generated/inbox/<manifest>/`, then `designer_pass.py` on that folder. Default API model now `gemini-nano-banana-2.1` (if billing is ever enabled).
- Research saved to `docs/ai_tooling_research.md` (Playground can't export 3D; Imagen 4 shut down; adopted techniques: depth-map parallax, AI normal maps, AI GLSL, Omni clips for hero moments).
- Stage v2 prototype: `slot_engine/static/stage_v2/` (Three.js r128, `manifest.js` maps art → `assets/v2/<category>/<id>.png` with placeholder fallback). Capture: `python scripts/stage_v2/capture.py` → `artifacts/stage_v2/`. Existing game untouched; plan is to port once art lands.
- Reviewer loop, 3 rounds: FAIL → FAIL → **PASS on stage-owned gates** (G1 4, G3 4, G4 4, G7 payload 4 at ~9.3MB). G2/G5/G6 capped by placeholder art.

**Open follow-ups (stage)**: measure fps on mid-range phone / 4× CPU throttle; rebuild frame on rotation; bigger depth plaque + seals on mobile; deeper seams on desktop.

**Next**
- P1 art via Gemini app prompt pack (user) → designer pass → reviewer.
- Optional: local ComfyUI + SDXL on the RTX 5060 for outline-locked glyphs, depth-guided frame painting, and a style LoRA (awaiting user OK; ~10–15GB download).
- Then port stage v2 into the real game, wired to engine events.

---

## 2026-10-28 — `visual/ai-studio-pipeline`

**Done**
- Visual direction canvas: https://claude.ai/artifact/MJBDSJaq9nRTzifJ7B92ns
- Locked: 2.5D layered rendering, Nolimit grit feel, Gemini via local `GEMINI_API_KEY`.
- Added `docs/art_bible.md` (palette, light, tiers, stage layers, reviewer gates G1–G7, phases P1–P4).
- Added `.agents/skills/studio-designer/` (cleanup pass for generated art).
- Added `scripts/ai/gemini_generate.py` + `scripts/ai/prompts/` manifests.

**Baseline review of the original symbols** (designer_pass sheets): FAIL G2 — under 8px blur every symbol collapses into an identical brass ring; tiers can't be told apart. Also baked text ("PHANTOM SQUID", "DEEP SEA RICHES") and baked UI (spin button, bet pill) inside `sym_high_angler.jpg`. P2 replaces the whole set.

**Next**
- Set `GEMINI_API_KEY`, run `python scripts/ai/gemini_generate.py --list-models` to confirm the image model id.
- P1: generate trench backdrop + frame (`scripts/ai/prompts/p1_backdrop_frame.json`), designer pass, reviewer gate.

**Working across PCs**
- Commit + push at the end of every session; pull at the start. Update this log before pushing.
- Generated raw images go to `generated/` (git-ignored). Only approved, cleaned assets are committed.
