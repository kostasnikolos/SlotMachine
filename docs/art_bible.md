# Art Bible — The Descent: Abyssal Leviathan

Single source of truth for every generated, cleaned or built visual. The Planner owns this file; Builder and Reviewer read it before every phase.

**Decisions locked (2026-10-28):**
- **Rendering:** 2.5D layered. AI-painted 2D layers composited in a Three.js stage with depth, light and shaders. The GLB Leviathan is not on the critical path.
- **Art feel:** Nolimit City grit — dark, painterly, desaturated, horror-industrial. References for scoring only; never trace or copy their art.
- **Generation:** Gemini via `GEMINI_API_KEY` (local env var), orchestrated by `scripts/ai/gemini_generate.py`.
- **Design canvas:** https://claude.ai/artifact/MJBDSJaq9nRTzifJ7B92ns (key frame direction + pipeline).

---

## 1. Why the current build reads cheap

1. Every symbol carries its own ornate brass frame, glow and background. 25 framed tiles = noise; tiers don't separate.
2. No world: black void around a thin teal box. Trench art and the Leviathan never share the screen with the reels.
3. HUD is web UI — neon pills, rounded borders, separate boxes.
4. Low symbols are placeholder "RUNESTONE" cards in five hues.

## 2. Palette

| Role | Hex | Use |
| --- | --- | --- |
| Abyss | `#02060A` | Deepest background, vignette |
| Trench | `#0B1418` | Reel backplane, panels |
| Silt | `#1E2C31` | Hairlines, inactive |
| Bone | `#F2E6CF` | Titles, high-value highlights |
| Mist | `#C3D1D4` | Body text |
| Biolume | `#3FE0D0` | Primary light source, active meter, wins at 0–2,000m |
| Brass | `#B8874A` / `#D9B77E` | Frame metal, mid-tier metals |
| Sulfur | `#E8B04A` | Multipliers, 2,000–5,000m grade |
| Blood | `#E0314B` | Purges, Wild Maw, 5,000m+ grade |

Rule: **one chromatic light per depth tier.** Everything else is desaturated toward Trench. No rainbow tile backgrounds.

## 3. Light

- Single key light: bioluminescent, from the creature behind the reels (upper-centre, slightly left). Every symbol's rim light comes from that direction.
- Ambient: cold teal, low. No white top-light.
- Depth grade LUT: 0m teal → 2,000m sulfur → 11,000m blood.

## 4. Symbol tiers (silhouette first)

| Tier | Symbols | Treatment |
| --- | --- | --- |
| Low | 10 J Q K A | Carved basalt glyphs on transparent ground, no frame, no colour fill; glow only on win. ~70% of the cell. |
| Mid | Helmet, Compass | Brass objects, full-cell, cut out from background, cool rim light. |
| High | Angler, Squid, Viper, Leviathan | Creatures breaking the cell edge (overscan 110–120%), painted, warm inner glow. |
| Special | Wild Maw, Scatter | Only symbols allowed a frame; animated; blood or biolume accent. |

Nothing has a baked background. The reel backplane and the world supply the background.

## 5. Stage layers (back → front)

0. Trench backdrop (painted, 3 parallax planes, caustics shader)
1. Leviathan silhouette + key light (2D layered rig, depth fog)
2. Frame: basalt + submarine steel. Depth gauge in the left pillar, sonar in top-right, ritual bar + 5 rune seals in the bottom lintel
3. Symbols (quads, normal-lit from layer 1 light)
4. Foreground particles, strike breach, embers
5. Post: shockwave refraction, chromatic aberration on big hits, depth LUT
6. DOM: only regulatory controls (spin, bet, balance, menu)

## 6. Reviewer gates (every phase)

Score 1–5 per line. **PASS requires ≥4 on every line.** Reviewer compares our snapshot side by side with the reference board.

| # | Criterion | How to check |
| --- | --- | --- |
| G1 | Readable at phone size | Downscale snapshot so a cell is 64px. Every symbol identifiable. |
| G2 | Tier hierarchy | Blur test (8px Gaussian): highs and specials still pop, lows recede. |
| G3 | One light | Rim lights, shadows and glows agree with the key light direction. |
| G4 | Integrated HUD | No meter lives in a floating box; all are part of the frame. |
| G5 | Cohesion | Symbols, frame and backdrop look painted by one hand (palette, brush, grain). |
| G6 | Reference parity | Next to 3 reference frames, a stranger cannot pick ours as the cheap one. |
| G7 | Budget | Total texture payload ≤ 15MB; 60fps on a mid-range phone. |

Reference board (descriptive, for scoring): Nolimit City *Mental*, *Das xBoot*, *Tombstone RIP*; Push Gaming *Razor Returns*; Pragmatic Play *Gates of Olympus* (for readability only).

## 7. Phases

| Phase | Output | Gate focus |
| --- | --- | --- |
| P1 Backdrop + frame | Trench layers, frame with built-in meters | G3 G4 G5 |
| P2 Symbol set v2 | 5 lows, 2 mids, 4 highs, 2 specials, cut out | G1 G2 G5 |
| P3 Stage assembly | Three.js stage, all layers, 8 state snapshots | G3 G4 G6 |
| P4 Creature + FX | Layered Leviathan, strike breach, post FX | G5 G6 G7 |
