# Session Log

Read this first on any PC. Newest entry on top. Each entry: date, branch, what changed, what's next.

---

## 2026-11-01 — `visual/ai-studio-pipeline` — canvas becomes the front end

**Decision (user):** the Design canvas "The Descent: Abyssal Leviathan" (https://claude.ai/artifact/Qh5cU4RMbQ4KRmAsLPGpvB) is the look. Porting it piece by piece into the old UI was rejected; instead the canvas's own code now runs as the game front end.

**Done**
- `slot_engine/static/canvas/`: the canvas artboard as `index.html` (asset `/_blob/<id>` urls rewritten to `assets/`), `support.js` = the Design runtime (bundles React 18; self-boots on `<x-dc>` and works outside the editor), `assets/` = Three.js r1xx build, 4 PBR symbol atlases (albedo/normal/emissive/aux), Leviathan geo JSON ×3 + PBR jpgs. ~11MB.
- `index.html` spin(): outcome now comes from `POST /api/slot/spin` / `/api/slot/buy-bonus` (same event schema the canvas simulator emitted: SPIN_STARTED, GRID_DROP, WIN_EVALUATION, CASCADE_DROP, LEVEL_UP, CREATURE_LIFELINE_STRIKE, …). `?engine=local` keeps the built-in simulator; it is also the fallback if the API is down. Per-event try/catch so an unknown payload can't kill a round.
- Verified headless: 3 real spins, balance tracks payouts, no page errors. `GET /canvas` route added in `slot_engine/api/app.py` (restart uvicorn to pick it up).
- Earlier the same day: grid alignment + endless-spin bugs fixed in the OLD front end (`WebGLGameEngine.alignToCells`, `game.js`), `?feel=1` game-feel preview, `?look=canvas` step-1 chrome (`look_canvas.css`) — the latter is superseded by the canvas front end and can be removed.

**Open**
- Bonus buy verified through the API (STANDARD_BONUS_100X: 41 events incl. strike + vents, balance 1000 → 956 for a 56 payout, no errors). xBet not yet exercised. API has no UNDERTOW event.
- Director bar: still drives the simulator's levels; with the API, L1–L5 jump buttons only change visuals. Decide whether to keep it behind a flag.
- Mobile/portrait layout for the canvas front end (it is a fixed 1920×1080 artboard; needs a scale-to-fit wrapper at minimum).
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
