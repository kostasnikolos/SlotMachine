# Symbol set target - what good looks like (round two)

Reference target for art-bible phase P2 (symbol set v2), revised after `docs/targets/review_round1.md` (FAIL, close: G1 4, G2 3, G3 3, G5 4, G6 3). Everything is painted locally with Z-Image-Turbo (Apache 2.0) through `scripts/ai/comfy_tools.py paint` (8 steps, 1024x1024, no negative prompt), cut out with BiRefNet (`comfy_tools.py cutout`) and finished with Pillow/numpy/scipy. Nothing under `slot_engine/` was touched. 104 paint calls in total (88 in round one, 16 in round two).

## Deliverables

- `artifacts/targets/symbols_target.png` - mock 5x5 reels (lows in REST state), 64 px phone row, 8 px blur, rest-vs-win row for the lows, measured tier table, the three low-rune directions.
- `artifacts/targets/symbols_target_grid.png`, `symbols_target_grid_blur8.png` - the mock grid alone, sharp and blurred.
- `artifacts/targets/symbols_before_after.png` - current atlas cell vs new symbol, all 12.
- `generated/targets/symbols/<key>.png` - the 12 RGBA cut-outs, 768 px, same file names as round one. For the lows this file is now the **REST** state.
- `generated/targets/symbols/low_*_emissive.png` - greyscale emissive mask per glyph (groove light only), pixel-aligned with `low_*.png`.
- `generated/targets/symbols/low_*_win.png` - WIN state (groove at 100% plus a small boost; the bloom is additive from the mask and is not baked in). `low_*_full.png` - the levelled paint at 100% emission with no boost.
- `generated/targets/symbols/tier_peaks.json` - the measured numbers printed by `finalize.py`.
- `generated/targets/raw/` - every paint with its provenance `.json`; `generated/targets/cut/` - BiRefNet mattes and check sheets (`_r2_fin.png`, `_r2_low.png`: dark and magenta grounds).
- `generated/targets/_scripts/` - `batch.py`, `jobs*.json` (every prompt and seed run), `picks.json`, `tiers.py` (tier scales, targets, the blurred-peak measurement), `finalize.py`, `build_sheets.py`, `write_doc.py`.

## Rebuild

```
python generated/targets/_scripts/batch.py generated/targets/_scripts/jobs10.json   # any jobs file; skips paints that exist
python scripts/ai/comfy_tools.py cutout generated/targets/raw/<name>.png generated/targets/cut/<name>.png
python generated/targets/_scripts/finalize.py        # prints the measured tier peaks
python generated/targets/_scripts/build_sheets.py
python generated/targets/_scripts/write_doc.py
```

## What changed, per review item

| Review item | Status | How |
| --- | --- | --- |
| 2. Leviathan is the wrong animal | Repainted | New head painted after looking at `lev_eye`, `lev_lunge`, `lev_rise`, `lev_maw`: dark teal-grey plated scales, heavy brow, round cyan eye with a black vertical slit, pale needle fangs, cyan-lit throat, dorsal spines, no horns, no red. The neck runs out of the right edge of the paint and `finalize.py` fades its alpha over the last 22%, so there is no stump. Drawn at 120%, nudged up-right in the mock grid so the neck lies across the neighbouring cells, and drawn last. |
| 3. Lows: emissive mask, rest and win | Done | Mask keyed from the cyan of each paint (min(G,B)-R, flecks closed, stone crystals rejected by component size). REST: groove floor at 38% of the levelled emission and pulled 55% toward Mist; the pale cut rim carries the letter. WIN: 100% plus boost, bloom added from the mask. Base `low_*.png` is REST. |
| 3b. Five identical outlines | Done, matte only | `chip()` in `finalize.py`: per glyph, a noise field seeded by crc32 of the key bites two corners and notches one edge; of 60 seeded attempts it keeps the largest bite that stays 11 px clear of the glyph, and darkens a fracture band inside the new edge. No model call. |
| 5. Tier grade to measured peaks | Done, shortfalls listed below | `finalize.py` solves one gain per symbol by bisection against the blurred-peak measurement in `tiers.py`. Helmet: lights pulled 80% toward a desaturated tarnish, flecks on the collar median-filled, gain 0.73 (a 27% cut, more than the 15% asked, because that is what peak 85 needs), cool rim at 0.70 strength. Wild: the iron ring is darkened 30% and excluded from the lift; throat and teeth lifted x2.2, then a Blood glow keyed from the red of the throat is added until the peak reaches 150. Leviathan: lift capped at x1.45, the rest comes from a Biolume glow keyed from its own eye and throat. |
| K's groove flatter and greyer | Done in the grade | Every glyph's groove floor is scaled to the same mean luminance (150) and mixed 40% toward one Biolume hue before the states are derived. |
| 6. Squid | Repainted | Front view, arms in a radial fan filling the cell, opaque dark wine-red and near-black flesh with pale highlights on the lit side, amber eyes, no iridescence. Saturation cut to 0.70 in the grade so red stays the Wild's. |
| 7. Compass | Repainted (two rounds) | Gimballed bowl in three-quarter view inside a brass ring, one bold arrow needle, wordless black face, tarnished brass. Mids are now drawn at 90% so they stay inside the cell. |
| 8. J | Repainted | Bolder J with a wide curled hook (`low4_a_j_s11_1`), same seed as the other tablets. Rest-state blurred peak 68 against 64 for the 10 and 70 for the K. |
| One light (7 of 12 self-lit) | Partly | All 12 get a thin cool rim where the matte faces the upper left (`rim_light()`); the five grooves are dimmed at rest. Leviathan (eye, throat), Wild (throat) and the angler's lure are still self-lit by design. |
| Viper tail enters the cell below | Done | The viper sprite gets 12% extra canvas so at 112% it stays inside its own cell. |
| Angler stalk too thin | Partly | Thin structures in the stalk zone are dilated 3 px at 768; at a 64 px cell that is still only about 2 px. |

## Measured tier ladder

Measurement (`tiers.blurred_peak`): the 768 px sprite is drawn at its tier scale in the middle of a 2x2-cell field of Trench #0B1418 at 150 px per cell and blurred with an 8 px Gaussian. Peak is the maximum Rec.601 luminance (0-255); cell mean is the mean over the central cell. Lows are measured in the REST state; their win peak includes the additive bloom.

| Symbol | Scale | Target peak | Measured peak | Cell mean | Win peak | Gain applied |
| --- | --- | --- | --- | --- | --- | --- |
| low_10 | 70% | 70 | 64.4 | 28.8 | 132.6 | 1.6 |
| low_j | 70% | 70 | 67.7 | 27.8 | 146.5 | 1.6 |
| low_q | 70% | 70 | 68.2 | 27.9 | 140.3 | 1.6 |
| low_k | 70% | 70 | 69.7 | 27.6 | 175.8 | 1.348 |
| low_a | 70% | 70 | 60.4 | 26.4 | 168.8 | 1.6 |
| mid_helmet | 90% | 85 | 84.9 | 27.7 |  | 0.734 |
| mid_compass | 90% | 85 | 85.4 | 31.6 |  | 1.58 |
| high_viper | 112% | 110 | 110.0 | 40.4 |  | 1.093 |
| high_angler | 112% | 110 | 110.3 | 41.3 |  | 1.114 |
| high_squid | 112% | 110 | 110.0 | 37.5 |  | 1.223 |
| high_leviathan | 120% | 130 | 129.8 | 49.2 |  | 1.45 + accent 0.49 |
| wild_maw | 100% | 150 | 149.9 | 49.5 |  | 2.2 + accent 1.05 |

Lows land at 60-70, not all at 70: the lift is applied to the stone and the cut rim only (never to the groove floor, which would undo the rest state) and is capped at x1.6, past which the basalt crystals start to sparkle. For comparison the same tablets at 100% emission measure 87-103 by this method.

## Low runes: three directions, one pick (unchanged from round one)

All three directions produced five correct letterforms as pure paint; no Pillow carving was used. **A (pick): Roman glyph chiselled into a broken black basalt tablet.** B (rusted cast-iron plate stamp) adds a second chromatic accent to most of the grid and reads as a framed tile. C (whale bone) is the brightest value in the palette and would out-shout the creatures. The reviewer confirmed A and asked for the bible line to change from "transparent ground" to "carved basalt tablet"; that edit to `docs/art_bible.md` is outside this task's write scope and has not been made.

## Exact prompts

All 1024x1024, 8 steps. Final file is `generated/targets/symbols/<key>.png` (768x768).

### low_10

- source paint: `generated/targets/raw/low3_a_10_s11.png`
- seed: `11`, size: `1024x1024`, steps: `8`
- prompt:

> A flat irregular shard of black basalt, a broken ancient stone tablet with chipped uneven edges, hairline cracks and a little pale barnacle crust. Carved into it, very large and bold, filling almost the whole tablet, is the number "10": a wide deep chiselled trench with thick strokes, its floor glowing evenly along every stroke with clear cyan bioluminescent light, its cut rim worn pale grey. Matte wet dark stone. Lit by one hard cold cyan light from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, front view, isolated on a plain flat mid-grey background

### low_j

- source paint: `generated/targets/raw/low4_a_j_s11_1.png`
- seed: `11`, size: `1024x1024`, steps: `8`
- prompt:

> A flat irregular shard of black basalt, a broken ancient stone tablet with chipped uneven edges, hairline cracks and a little pale barnacle crust. Carved into it, very large and bold, filling almost the whole tablet, is a very bold heavy capital letter "J" with a thick stem and a broad curling hook: a wide deep chiselled trench with thick strokes, its floor glowing evenly along every stroke with clear cyan bioluminescent light, its cut rim worn pale grey. Matte wet dark stone. Lit by one hard cold cyan light from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, front view, isolated on a plain flat mid-grey background

### low_q

- source paint: `generated/targets/raw/low3_a_q_s11.png`
- seed: `11`, size: `1024x1024`, steps: `8`
- prompt:

> A flat irregular shard of black basalt, a broken ancient stone tablet with chipped uneven edges, hairline cracks and a little pale barnacle crust. Carved into it, very large and bold, filling almost the whole tablet, is the capital letter "Q": a wide deep chiselled trench with thick strokes, its floor glowing evenly along every stroke with clear cyan bioluminescent light, its cut rim worn pale grey. Matte wet dark stone. Lit by one hard cold cyan light from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, front view, isolated on a plain flat mid-grey background

### low_k

- source paint: `generated/targets/raw/low2_a_k_s11.png`
- seed: `11`, size: `1024x1024`, steps: `8`
- prompt:

> A flat irregular shard of black basalt, a broken ancient stone tablet with chipped uneven edges, hairline cracks and a little pale barnacle crust. Carved into it, very large and bold, filling almost the whole tablet, is the capital letter "K": a wide deep chiselled trench with thick strokes, its floor glowing with soft dim cyan bioluminescent light, its cut rim worn pale grey. Matte wet dark stone. Lit by one hard cold cyan light from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, front view, isolated on a plain flat mid-grey background

### low_a

- source paint: `generated/targets/raw/low3_a_a_s11.png`
- seed: `11`, size: `1024x1024`, steps: `8`
- prompt:

> A flat irregular shard of black basalt, a broken ancient stone tablet with chipped uneven edges, hairline cracks and a little pale barnacle crust. Carved into it, very large and bold, filling almost the whole tablet, is the capital letter "A": a wide deep chiselled trench with thick strokes, its floor glowing evenly along every stroke with clear cyan bioluminescent light, its cut rim worn pale grey. Matte wet dark stone. Lit by one hard cold cyan light from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, front view, isolated on a plain flat mid-grey background

### mid_helmet

- source paint: `generated/targets/raw/mid_helmet_v2_s202.png`
- seed: `202`, size: `1024x1024`, steps: `8`
- prompt:

> An antique brass deep-sea diving helmet, three-quarter view, heavy riveted copper and brass with a round glass faceplate and side ports, dented, darkly tarnished and streaked with verdigris, a few barnacles, the glass black with a faint cyan reflection. Lit by one hard cold cyan light coming from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. The whole subject is in view, centered, floating in empty space, isolated on a plain flat mid-grey background

### mid_compass

- source paint: `generated/targets/raw/mid_compass_v7_s631.png`
- seed: `631`, size: `1024x1024`, steps: `8`
- prompt:

> An antique ship's gimbal-mounted bearing instrument seen obliquely from above and from the side in three-quarter view, so its round face appears as a tilted ellipse: a deep heavy brass bowl with thick walls hanging on two pivot pins inside a wide flat brass gimbal ring, which hangs on two more pins inside a second larger brass ring. Darkly tarnished dull brown brass, dented and scratched, green verdigris in the seams, a few barnacles. Under the cracked glass the face is bare blackened enamel, wordless, with fine pale tick marks round the edge, and lying across the whole face one single long thick pale steel needle shaped like an arrow. A single cool highlight on the upper-left of the glass. Lit by one hard cold cyan light coming from the upper left that draws a bright pale rim along the upper-left silhouette, the lower right side falling into shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, floating in empty space, isolated on a plain flat evenly lit mid-grey background

### high_viper

- source paint: `generated/targets/raw/high_viper_v4_s402.png`
- seed: `402`, size: `1024x1024`, steps: `8`
- prompt:

> A realistic deep-sea viperfish, grotesque and menacing, whole body in side view coiled in an S-curve, long slender eel-like body covered in gleaming tarnished-silver and gunmetal scales with wet glistening highlights, a large head, gaping hinged jaws with glassy needle fangs so long they reach past the eye, a blank white eye, a bright row of cyan glowing photophores along its belly, thin spined translucent fins. Lit by one hard cold cyan light coming from the upper left that draws a bright pale rim along the upper-left silhouette, the lower right side falling into shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. The whole subject is in view, centered, floating in empty space, isolated on a plain flat evenly lit mid-grey background

### high_angler

- source paint: `generated/targets/raw/high_angler_v4_s402.png`
- seed: `402`, size: `1024x1024`, steps: `8`
- prompt:

> A realistic deep-sea humpback anglerfish, grotesque and menacing, three-quarter front view, globular warty body of dark umber-brown and bruised violet skin with wet glistening highlights, tiny blind white eye, a huge underslung gaping jaw full of long thin curved glassy fangs, the inside of the mouth lit warm amber from within, a long thin stalk rising from its forehead and arcing forward over the mouth, ending in a solid round pearl-like lure bulb glowing bright cyan, ragged torn translucent fins. Lit by one hard cold cyan light coming from the upper left that draws a bright pale rim along the upper-left silhouette, the lower right side falling into shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. The whole subject is in view, centered, floating in empty space, isolated on a plain flat evenly lit mid-grey background

### high_squid

- source paint: `generated/targets/raw/high_squid_v6_s612.png`
- seed: `612`, size: `1024x1024`, steps: `8`
- prompt:

> A phantom squid, a menacing deep-sea squid seen from slightly below and in front, its eight thick arms and two long tentacles spread wide toward the viewer in a radial fan that fills the picture, rows of pale suckers on the undersides, the pointed mantle foreshortened behind them, one large glaring amber eye in the centre as the focal point. Opaque matte flesh of bruised dark wine-red and near-black, turning bone-white only on the upper-left surfaces where the light hits. Lit by one hard cold cyan light coming from the upper left that draws a bright pale rim along the upper-left silhouette, the lower right side falling into shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, floating in empty space, isolated on a plain flat evenly lit mid-grey background

### high_leviathan

- source paint: `generated/targets/raw/high_leviathan_v6_s602.png`
- seed: `602`, size: `1024x1024`, steps: `8`
- prompt:

> The head of a colossal deep-sea serpent-fish, a leviathan, in three-quarter view facing the lower left, filling the picture. A smooth hornless reptilian head armoured in dark teal-grey overlapping plated scales with a heavy scaled brow ridge. One huge round glowing pale-cyan eye with a thin black vertical slit pupil is the brightest point of the picture. The jaws hang part open, lined with long pale curved needle fangs like the bars of a cage, and a cold cyan glow shines from deep inside the throat. A row of short dark dorsal spines runs along the back of its thick scaled serpent neck, and the neck continues out of the upper right corner of the picture, cut off by the picture edge. Wet glistening highlights. Lit by one hard cold cyan light coming from the upper left that draws a bright pale rim along the upper-left silhouette, the lower right side falling into shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, floating in empty space, isolated on a plain flat evenly lit mid-grey background

### wild_maw

- source paint: `generated/targets/raw/wild_maw_v5_s501.png`
- seed: `501`, size: `1024x1024`, steps: `8`
- prompt:

> A lamprey-like circular monster mouth seen straight from the front: a perfect ring of raw wet blood-red flesh with dozens of long thin sharp ivory fangs arranged radially in two concentric circles, all pointing inward to a black hole in the centre, a strong blood-red glow rising from deep in the throat and lighting the inner teeth, the mouth set inside a heavy round riveted dark iron ring crusted with barnacles. Lit by one hard cold cyan light coming from the upper left that draws a bright pale rim along the upper-left silhouette, the lower right side falling into shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. The whole subject is in view, centered, floating in empty space, isolated on a plain flat evenly lit mid-grey background

### Directions not picked

- **B (cast-iron plate), not picked** - `low1_b_k.png`, seed `21`:

> A single thick corroded cast-iron ship hull plate, roughly square with torn rusted edges and four worn rivets, with one large capital letter "K" as a bold raised embossed foundry stamp filling most of the plate, dark pitted iron, muted brown rust, verdigris streaks, a small barnacle crust in one corner, hard cold cyan rim light from the upper left, deep shadow on the lower right, dark desaturated hand-painted horror concept art, loose visible brush strokes, gritty film grain, game icon, centered, front view, isolated on a plain flat mid-grey background

- **C (whale bone), not picked** - `low1_c_k.png`, seed `31`:

> One large capital letter "K" built out of pale weathered whale bone, thick bold simple strokes, encrusted with barnacles and small dead coral growths, a free-standing bone glyph with a clear bold silhouette, dull grey-white bone with dark stained cracks, hard cold cyan rim light from the upper left, deep shadow on the lower right, dark desaturated hand-painted horror concept art, loose visible brush strokes, gritty film grain, game icon, centered, front view, isolated on a plain flat mid-grey background

## Prompt lessons

- Never write "key light": Z-Image paints a literal glowing key. "Lit by one hard cold cyan light coming from the upper left" works.
- "game icon" makes cartoon fish; "dark moody realistic oil painting, grim deep-sea horror concept art" gives the shared brush.
- "compass" brings garbled N/E/S/W lettering, a star rose and a pocket-watch loop. "Gimbal-mounted bearing instrument", a "wordless" face and "one single long thick pale steel needle shaped like an arrow" gave the needle and no letters.
- For the Leviathan, describing the hero animal feature by feature (plated scales, brow ridge, slit eye as the brightest point, fangs like cage bars, neck cut off by the picture edge) and the word "hornless" worked.
- Asking for a bolder glyph by comparison ("the same strokes as a bold letter K") produced a K/J hybrid; describing the J itself worked.

## Self-scores after round two

| Gate | Score | Why |
| --- | --- | --- |
| G1 readable at 64 px | 4 | All 12 identifiable. Rest-state lows are dimmer than round one by design; they still read at 45 px but with less margin (A is the weakest, peak 60). The compass is now a ring with a needle, clearer than the bowl but small. |
| G2 tier hierarchy under blur | 4 | The measured ladder is ordered: lows 60-70, mids 85, highs 110, Leviathan 130, Wild 150. By eye the Wild is clearly loudest and the lows recede. The squid meets its peak number but has the lowest cell mean of the highs (37.5) and looks dimmer than the helmet's warm blob under blur. |
| G3 one light | 3 | Upper-left cool rim on all 12 and the grooves are quiet at rest. The rim is a matte-edge effect, not relighting: interior forms keep the light they were painted with, and the helmet is still lit fairly frontally. |
| G5 cohesion | 4 | One brush and grain. The new squid and Leviathan sit better with the angler and viper than the old ones. The Leviathan's and the Wild's added glow is composited light and looks slightly airbrushed against the oil paint. |
| G6 reference parity | 3 | The demon head and the top-down bowl are gone, but this was not judged against real reference frames here, so no higher claim is made. |

## What still falls short

- **Leviathan matches the hero in kind, not in detail.** It is a teal scaled serpent with a cyan slit eye and fangs, but the hero's eye is larger with a heavier lid, its fangs are longer rib-like needles, and the lure hanging in the throat is only a glow here. The head is a long diagonal, not the largest mass on the grid; its apex status rests on the eye and throat light and the 120% overlap.
- **The 130 and 150 peaks are reached with added glow**, not with paint alone (Leviathan lift capped at x1.45 plus a Biolume accent; Wild x2.2 plus a Blood accent). The Wild's glow reads pinkish rather than blood red.
- **Lows do not all reach 70** at rest (60-70), and their **win peaks are uneven** (133 for the 10 to 176 for the K): the floor is levelled, but glyph area and stroke width differ.
- **Chipped outlines are matte-only.** The new edges get a dark fracture band but no painted broken face; at 768 px the J's right side shows a ragged cut and a small detached speck. A second slab seed per glyph would be the proper fix.
- **The J sits on a different slab** (taller, narrower) from the other four, because the bolder prompt changed the paint.
- **Squid**: two amber eyes rather than one focal eye, seen from the front rather than from below, and dark enough to be the weakest high under blur.
- **Compass** keeps a short chain link at the top, and its arrow needle leans toward a gauge.
- **Helmet** was cut 27% and desaturated to hit 85; it reads slightly muddy at full size.
- **One light is a rim overlay**; no normal maps or relighting.
- **Angler lure** still needs its glow halo as an additive sprite in the engine.
- **Not covered**: Pearl/scatter, Dead Sediment, WILD lettering, atlas packing, any in-engine check, and the art-bible wording change. The sheets are Pillow composites, not game captures.
