# Symbol set target - what good looks like (round three)

Reference target for art-bible phase P2 (symbol set v2), revised after `docs/targets/review_round1.md` (FAIL, close: G1 4, G2 3, G3 3, G5 4, G6 3). Everything is painted locally with Z-Image-Turbo (Apache 2.0) through `scripts/ai/comfy_tools.py paint` (8 steps, 1024x1024, no negative prompt), cut out with BiRefNet (`comfy_tools.py cutout`) and finished with Pillow/numpy/scipy. Nothing under `slot_engine/` was touched. 104 paint calls in total (88 in round one, 16 in round two, none in round three). Round two passed review (`docs/targets/review_round2.md`, G1-G6 all 4); round three is fix T4 plus the atlas albedo export.

## Deliverables

- `artifacts/targets/symbols_target.png` - mock 5x5 reels (lows in REST state), 64 px phone row, 8 px blur, rest-vs-win row for the lows, measured tier table, the three low-rune directions.
- `artifacts/targets/symbols_target_grid.png`, `symbols_target_grid_blur8.png` - the mock grid alone, sharp and blurred.
- `artifacts/targets/symbols_before_after.png` - current atlas cell vs new symbol, all 12.
- `generated/targets/symbols/<key>.png` - the 12 RGBA cut-outs, 768 px, same file names as round one. For the lows this file is now the **REST** state.
- `generated/targets/symbols/low_*_emissive.png` - greyscale emissive mask per glyph (groove light only), pixel-aligned with `low_*.png`.
- `generated/targets/symbols/low_*_win.png` - WIN state (groove at 100% plus a small boost; the bloom is additive from the mask and is not baked in). `low_*_full.png` - the levelled paint at 100% emission with no boost.
- `generated/targets/symbols/<key>_albedo.png` - atlas variant of all 12: tier grade removed, shadows lifted, no baked glow.
- `generated/targets/symbols/tier_peaks.json` - the measured numbers printed by `finalize.py`, including every `_albedo` file.
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

## Round three: what changed (fix T4 and the atlas export)

| Item | Status | How |
| --- | --- | --- |
| Helmet over-cut | Done | Gain is fixed at 0.92 instead of the 0.73 solved for peak 85; it stays de-yellowed (lights pulled 70% toward a desaturated tarnish, saturation 0.90) with the cool rim at 0.70. Consequence: its blurred peak is now 106.7, close to the highs' 110. |
| Wild accent pink | Done, peak short of 150 | The additive glow is gone. True Blood #E0314B is mixed (never added) into the throat only: inside the tooth ring, weighted by how red the paint already is, never on the ivory. The lift then goes to the teeth, with the gums getting 60% of it and the iron ring none. Blurred peak is 136.8, not 150: Blood itself has a luminance of 104, so a confined, true-Blood throat cannot carry 150 without bleaching the teeth further. |
| Win peaks uneven (133-176) | Done | Every glyph gets the same lit groove (Biolume boost 0.45); the peak is levelled with a per-glyph bloom gain recorded as `win_bloom_gain` in `tier_peaks.json` (K 0.47, A 0.53, Q 1.39, 10 1.71, J 1.73). All five now measure 149.5-150.0. The engine has to apply that gain to the bloom it draws from the mask. |
| J on a different slab | Done | Re-picked `low4_a_j_s11_0`: same seed and the same slab proportions as the other four, bolder than the round-one J but lighter than the round-two one. Its rest emission is 0.55 instead of 0.38, because with the least groove area its rest peak fell to 56; it now measures 62.3. |
| Chips too alike | Done, matte only | `BREAKS` in `finalize.py` gives each tablet its own fracture planes (the 10 loses its upper right, the J its lower left, the Q is sheared on the left, the K is broken along the bottom, the A is knapped toward a point), each backed off until it clears the glyph by 30 px, wobbled by a noise field seeded from the key, plus one notch. |
| Atlas albedo | Done | `<key>_albedo.png` for all 12: the same matte, repairs, saturation and rim, but no tier gain and no accent glow; a gamma curve lifts the shadows until the painted pixels average 105 (mids, highs, apex, wild) or 65 (lows). Lows use the rest-state groove; win light comes from `low_*_emissive.png`. |

## Atlas albedo variants (measured)

Mean is the Rec.601 luminance over pixels with alpha above 0.5. Blurred peak and cell mean use the same method as the ladder below. These files carry no tier ladder on purpose: the helmet's albedo peak is the highest of the set, so the ladder must come from the shader.

| Symbol | Gamma applied | Mean luminance (painted) | Blurred peak | Cell mean |
| --- | --- | --- | --- | --- |
| low_10_albedo | 0.774 | 65.0 | 74.9 | 32.5 |
| low_j_albedo | 0.782 | 65.0 | 78.3 | 30.5 |
| low_q_albedo | 0.75 | 65.0 | 79.8 | 30.9 |
| low_k_albedo | 0.79 | 65.0 | 84.7 | 30.8 |
| low_a_albedo | 0.737 | 65.0 | 82.2 | 28.4 |
| mid_helmet_albedo | 0.575 | 105.0 | 156.7 | 50.6 |
| mid_compass_albedo | 0.5 | 105.0 | 114.1 | 47.3 |
| high_viper_albedo | 0.699 | 105.0 | 129.3 | 50.5 |
| high_angler_albedo | 0.593 | 105.0 | 137.1 | 62.3 |
| high_squid_albedo | 0.632 | 105.0 | 130.2 | 48.9 |
| high_leviathan_albedo | 0.522 | 105.0 | 132.4 | 70.8 |
| wild_maw_albedo | 0.517 | 105.0 | 135.5 | 74.2 |

## Round two: what changed, per review item (kept for the record)

- Leviathan repainted as the hero animal (teal plated scales, cyan slit eye, needle fangs, cyan throat, dorsal spines, no horns, no red); neck fades into the cell edge; drawn at 120% and last.
- Lows: emissive mask keyed from each paint's cyan; REST is the base file, WIN beside it; groove floors levelled to one luminance and hue.
- Squid repainted front-on with fanned arms; compass repainted as a gimballed bowl with one needle; viper padded to stay in its cell; angler stalk thickened.
- Tier gains solved by bisection against `tiers.blurred_peak`; a thin cool upper-left rim on all 12.

## Measured tier ladder

Measurement (`tiers.blurred_peak`): the 768 px sprite is drawn at its tier scale in the middle of a 2x2-cell field of Trench #0B1418 at 150 px per cell and blurred with an 8 px Gaussian. Peak is the maximum Rec.601 luminance (0-255); cell mean is the mean over the central cell. Lows are measured in the REST state; their win peak includes the additive bloom.

| Symbol | Scale | Target peak | Measured peak | Cell mean | Mean (painted) | Win peak | Gain applied |
| --- | --- | --- | --- | --- | --- | --- | --- |
| low_10 | 70% | 70 | 64.4 | 28.0 | 50.3 | 150.0 | 1.6 |
| low_j | 70% | 70 | 62.3 | 26.4 | 49.5 | 149.9 | 1.6 |
| low_q | 70% | 70 | 68.2 | 25.9 | 46.8 | 149.7 | 1.6 |
| low_k | 70% | 70 | 69.7 | 26.6 | 49.6 | 149.5 | 1.348 |
| low_a | 70% | 70 | 60.4 | 23.7 | 43.9 | 149.9 | 1.6 |
| mid_helmet | 90% | 85 | 106.7 | 32.0 | 55.3 |  | 0.92 |
| mid_compass | 90% | 85 | 85.4 | 31.6 | 58.4 |  | 1.58 |
| high_viper | 112% | 110 | 110.0 | 40.4 | 77.9 |  | 1.093 |
| high_angler | 112% | 110 | 110.3 | 41.3 | 64.3 |  | 1.114 |
| high_squid | 112% | 110 | 110.0 | 37.5 | 72.5 |  | 1.223 |
| high_leviathan | 120% | 130 | 129.8 | 49.2 | 68.5 |  | 1.45 + accent 0.49 |
| wild_maw | 100% | 150 | 136.8 | 51.8 | 69.8 |  | 4.5 |

Two rows miss their target on purpose after round three: the helmet (106.7 against 85, gain fixed at 0.92 as the review asked) and the Wild (136.8 against 150, true Blood confined to the throat). The Wild is still the highest peak on the grid.

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

- source paint: `generated/targets/raw/low4_a_j_s11_0.png`
- seed: `11`, size: `1024x1024`, steps: `8`
- prompt:

> A flat irregular shard of black basalt, a broken ancient stone tablet with chipped uneven edges, hairline cracks and a little pale barnacle crust. Carved into it, very large and bold, filling almost the whole tablet, is the capital letter "J" drawn in very thick heavy bold strokes with a wide heavy hook: a wide deep chiselled trench with thick strokes, its floor glowing evenly along every stroke with clear cyan bioluminescent light, its cut rim worn pale grey. Matte wet dark stone. Lit by one hard cold cyan light from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, front view, isolated on a plain flat mid-grey background

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

## Self-scores after round three

| Gate | Score | Why |
| --- | --- | --- |
| G1 readable at 64 px | 4 | All 12 identifiable. A is the weakest low (rest peak 60, smallest tablet after knapping). |
| G2 tier hierarchy under blur | 3-4 | Lows 60-70, compass 85, highs 110, Leviathan 130, Wild 137 hold. The helmet at 107 now sits with the highs, and the Wild leads the Leviathan by 7 rather than 20. On the base files the ladder is weaker than in round two; it is meant to be applied in the shader from the albedo set. |
| G3 one light | 3 | Unchanged: an upper-left rim overlay on all 12, no relighting. |
| G5 cohesion | 4 | The Wild's glow is no longer airbrushed pink and the helmet is no longer muddy. The chipped tablets have cut, not painted, fracture edges. |
| G6 reference parity | not scored | Not judged against reference frames here. |

## What still falls short

- **Wild peak is 136.8, not 150.** A true-Blood throat confined to the throat cannot reach it; the remaining lift is on the teeth (gain 4.5 on ivory), which are close to white.
- **Helmet ties the highs under blur** (106.7) on the base files. This follows from the requested gain; the ladder for mids now depends on the shader.
- **Albedo files have no hierarchy at all** by design (helmet albedo peak 156.7 is the highest). If the shader does not apply the ladder, the helmet will lead.
- **The albedo lift is a global gamma**, so it flattens deep shadows a little and greys the Wild's iron ring and the lows' basalt; it is not a relight.
- **Albedo lows carry the rest-state groove**, lifted with everything else, so the groove reads paler than in `low_*.png`. The engine review asked for the rest emissive to be halved; that is a shader value, not baked here.
- **Win levelling needs per-glyph bloom gain** (0.47 to 1.73) in the engine; with one global bloom the peaks return to an uneven spread.
- **Chips are matte-only**: dark fracture band, no painted broken face. The A's tablet is visibly the smallest of the five and the J's rest emission is higher than the others (0.55).
- **Leviathan matches the hero in kind, not in detail** (smaller eye, shorter fangs, throat lure only a glow); its peak still leans on added Biolume glow in the base file (not in the albedo).
- **Squid** has two eyes, is seen from the front and is the dimmest-looking high; **compass** keeps a chain link on top and an arrow needle.
- **Not covered**: Pearl/scatter, Dead Sediment, WILD lettering, atlas packing, any in-engine check, the art-bible wording change. Sheets are Pillow composites, not game captures.
