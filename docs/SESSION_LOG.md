# Session Log

Read this first on any PC. Newest entry on top. Each entry: date, branch, what changed, what's next.

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
