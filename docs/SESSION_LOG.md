# Session Log

Read this first on any PC. Newest entry on top. Each entry: date, branch, what changed, what's next.

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
