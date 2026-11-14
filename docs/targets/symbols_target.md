# Symbol set target - what good looks like

Reference target for art-bible phase P2 (symbol set v2). Everything here was painted locally with Z-Image-Turbo (Apache 2.0) through `scripts/ai/comfy_tools.py paint` (8 steps, 1024x1024, no negative prompt), cut out with BiRefNet (`comfy_tools.py cutout`) and finished with Pillow/numpy. Nothing under `slot_engine/` was touched. 88 paint calls were used in total.

## Deliverables

- `artifacts/targets/symbols_target.png` - mock 5x5 reels, 64 px phone row, 8 px blur tier test, the three low-rune directions.
- `artifacts/targets/symbols_target_grid.png` - the mock reel grid alone.
- `artifacts/targets/symbols_before_after.png` - current atlas cell vs new symbol, all 12.
- `generated/targets/symbols/<key>.png` - 12 RGBA cut-outs, 768 px, subject cropped tight and centred.
- `generated/targets/raw/` - every paint with its provenance `.json`, rejected ones included; `generated/targets/cut/` - raw BiRefNet mattes and the halo check sheets `_fin1.png`, `_fin2.png` (dark and magenta grounds).
- `generated/targets/_scripts/` - `batch.py` (paint a job list), `jobs*.json` (every prompt and seed that was run), `picks.json` (which paint became which key), `finalize.py` (matte clean-up, grade, crop, 768 px), `build_sheets.py` (both sheets), `write_doc.py` (this file).

## Rebuild

```
python generated/targets/_scripts/batch.py generated/targets/_scripts/jobs05.json   # any jobs file; skips paints that exist
python scripts/ai/comfy_tools.py cutout generated/targets/raw/<name>.png generated/targets/cut/<name>.png
python generated/targets/_scripts/finalize.py
python generated/targets/_scripts/build_sheets.py
```

## Low runes: three directions, one pick

All three directions came out with five correct letterforms on the first seed, so **no hybrid carving was needed: the glyphs are pure paint**. One seed is used for all five glyphs of a direction, which is what makes the slabs share one construction.

| | Direction | Verdict |
| --- | --- | --- |
| **A (pick)** | Roman glyph chiselled into a broken black basalt tablet, cyan light lying in the trench of the cut | Matches art bible section 4 (carved basalt, no frame, no colour fill). Darkest of the three, so it recedes under blur while the cyan groove keeps the letter legible at 45 px. Reads as painted stone, not a UI token. |
| B | Raised foundry stamp on a rusted cast-iron hull plate with rivets | Legible and well made, but the orange rust is a second chromatic accent on most of the grid (breaks the one-chromatic-light palette rule), the square plate with four rivets reads as a framed tile again, and it competes with the brass mids. |
| C | Glyph built from whale bone with barnacles | The most characterful, but bone is the brightest value in the palette: on the reels it would out-shout the creatures and invert the tier order. Better kept for a special use. |

Direction A went through three prompt passes. The first (`low1_a_*`) looked like a 3D-rendered app icon with a dark-on-dark glyph. The second (`low2_a_*`, oil-paint style block and a glowing trench floor) fixed the look, but J and Q were dimmer than K. The third (`low3_a_*`, "glowing evenly along every stroke") evened them out. Final set: 10, J, Q, A from pass three, K from pass two, all seed 11.

## Exact prompts

All 1024x1024, 8 steps. Final file is `generated/targets/symbols/<key>.png` (768x768 after crop).

### low_10

- source paint: `generated/targets/raw/low3_a_10_s11.png`
- seed: `11`, size: `1024x1024`, steps: `8`
- prompt:

> A flat irregular shard of black basalt, a broken ancient stone tablet with chipped uneven edges, hairline cracks and a little pale barnacle crust. Carved into it, very large and bold, filling almost the whole tablet, is the number "10": a wide deep chiselled trench with thick strokes, its floor glowing evenly along every stroke with clear cyan bioluminescent light, its cut rim worn pale grey. Matte wet dark stone. Lit by one hard cold cyan light from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, front view, isolated on a plain flat mid-grey background

### low_j

- source paint: `generated/targets/raw/low3_a_j_s11.png`
- seed: `11`, size: `1024x1024`, steps: `8`
- prompt:

> A flat irregular shard of black basalt, a broken ancient stone tablet with chipped uneven edges, hairline cracks and a little pale barnacle crust. Carved into it, very large and bold, filling almost the whole tablet, is the capital letter "J": a wide deep chiselled trench with thick strokes, its floor glowing evenly along every stroke with clear cyan bioluminescent light, its cut rim worn pale grey. Matte wet dark stone. Lit by one hard cold cyan light from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, front view, isolated on a plain flat mid-grey background

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

- source paint: `generated/targets/raw/mid_compass_v4_s402.png`
- seed: `402`, size: `1024x1024`, steps: `8`
- prompt:

> An antique brass nautical bearing instrument, a thick heavy round bowl of darkly tarnished dented brass with a wide riveted bezel, seen from the front at a slight tilt, cracked domed glass. Its face is bare blackened enamel, wordless, carrying only a ring of fine pale tick marks at the edge and one large pale eight-point star in the middle, with a single sharp steel needle. Green verdigris in the seams, a few barnacles on the rim. Lit by one hard cold cyan light coming from the upper left that draws a bright pale rim along the upper-left silhouette, the lower right side falling into shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. The whole subject is in view, centered, floating in empty space, isolated on a plain flat evenly lit mid-grey background

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

- source paint: `generated/targets/raw/high_squid_v2_s201.png`
- seed: `201`, size: `1024x1024`, steps: `8`
- prompt:

> A phantom squid, a pale ghostly half-translucent deep-sea squid, side view on a diagonal, long pointed mantle with fins, one large glaring amber eye, eight curling arms and two long tentacles with suckers spreading outward, bone-white flesh with dull blood-red mottling, faint cyan glowing spots along the arms. Lit by one hard cold cyan light coming from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. The whole subject is in view, centered, floating in empty space, isolated on a plain flat mid-grey background

### high_leviathan

- source paint: `generated/targets/raw/high_leviathan_v5_s501.png`
- seed: `501`, size: `1024x1024`, steps: `8`
- prompt:

> The severed-looking head of a colossal abyssal sea monster, a leviathan, facing the viewer and seen slightly from below, a compact armoured skull of gunmetal-black scales crowned with pale horn-like spines and crusted with barnacles, jaws wide open with rows of huge ivory fangs, the throat lit from within by a furnace-orange glow, two burning red-orange eyes, bright cyan bioluminescent veins glowing in the cracks of its hide, wet glistening highlights, head only. Lit by one hard cold cyan light coming from the upper left that draws a bright pale rim along the upper-left silhouette, the lower right side falling into shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. The whole subject is in view, centered, floating in empty space, isolated on a plain flat evenly lit mid-grey background

### wild_maw

- source paint: `generated/targets/raw/wild_maw_v5_s501.png`
- seed: `501`, size: `1024x1024`, steps: `8`
- prompt:

> A lamprey-like circular monster mouth seen straight from the front: a perfect ring of raw wet blood-red flesh with dozens of long thin sharp ivory fangs arranged radially in two concentric circles, all pointing inward to a black hole in the centre, a strong blood-red glow rising from deep in the throat and lighting the inner teeth, the mouth set inside a heavy round riveted dark iron ring crusted with barnacles. Lit by one hard cold cyan light coming from the upper left that draws a bright pale rim along the upper-left silhouette, the lower right side falling into shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. The whole subject is in view, centered, floating in empty space, isolated on a plain flat evenly lit mid-grey background

### Directions not picked

One example each; the other four glyphs only swap the glyph phrase (`the number "10"`, `the capital letter "J"`, and in the first pass `one large capital letter "K"`, `the large number "10"`).

- **B (cast-iron plate), not picked** - `low1_b_k.png`, seed `21`:

> A single thick corroded cast-iron ship hull plate, roughly square with torn rusted edges and four worn rivets, with one large capital letter "K" as a bold raised embossed foundry stamp filling most of the plate, dark pitted iron, muted brown rust, verdigris streaks, a small barnacle crust in one corner, hard cold cyan rim light from the upper left, deep shadow on the lower right, dark desaturated hand-painted horror concept art, loose visible brush strokes, gritty film grain, game icon, centered, front view, isolated on a plain flat mid-grey background

- **C (whale bone), not picked** - `low1_c_k.png`, seed `31`:

> One large capital letter "K" built out of pale weathered whale bone, thick bold simple strokes, encrusted with barnacles and small dead coral growths, a free-standing bone glyph with a clear bold silhouette, dull grey-white bone with dark stained cracks, hard cold cyan rim light from the upper left, deep shadow on the lower right, dark desaturated hand-painted horror concept art, loose visible brush strokes, gritty film grain, game icon, centered, front view, isolated on a plain flat mid-grey background

- **A dim idle variant (10/J/Q/A exist at this prompt), not picked** - `low2_a_q_s11.png`, seed `11`:

> A flat irregular shard of black basalt, a broken ancient stone tablet with chipped uneven edges, hairline cracks and a little pale barnacle crust. Carved into it, very large and bold, filling almost the whole tablet, is the capital letter "Q": a wide deep chiselled trench with thick strokes, its floor glowing with soft dim cyan bioluminescent light, its cut rim worn pale grey. Matte wet dark stone. Lit by one hard cold cyan light from the upper left, the lower right side falling into black shadow. Dark moody realistic oil painting, grim deep-sea horror concept art, muted desaturated colours, heavy visible brushwork, gritty film grain. Centered, front view, isolated on a plain flat mid-grey background

## Post-processing (all in `finalize.py`, deterministic)

- BiRefNet alpha, values under 4% dropped, stray specks removed, matte pulled in about 1 px and softened by 0.8 px to kill the grey paint-ground rim.
- `wild_maw`: holes inside the ring are filled so the throat is opaque black rather than see-through.
- Grade, the only colour change: lows brightness x0.90 / saturation x0.85, mids brightness x0.86 / saturation x0.85, to push them under the highs. Highs and Wild are untouched paint.
- Crop to the alpha box, pad square with a 4% margin, Lanczos to 768.
- No upscaler was used: the 1024 px paint is already above the 768 px target.

## Prompt lessons

- Never write "key light": Z-Image painted a literal glowing cyan key beside every creature. "Lit by one hard cold cyan light coming from the upper left" works.
- "game icon" pulls creatures toward cute cartoon fish; "dark moody realistic oil painting, grim deep-sea horror concept art" gives the grit and one shared brush.
- Black creatures vanish on the Trench backplane. Naming a lighter body material (tarnished-silver scales, umber and violet skin) plus "wet glistening highlights" is what made the viperfish and angler pop.
- "compass" produces garbled N/E/S/W lettering and pocket-watch loops; calling it a "nautical bearing instrument" with a "wordless" face removed both.
- A lure described as a "solid round pearl-like bulb" survives the cut-out; a pure glow does not.

## Self-scores (art-bible gates)

| Gate | Score | Why |
| --- | --- | --- |
| G1 readable at 64 px | 4 | All 12 identifiable in the phone row. Weakest: J (thin strokes at 45 px), and the viperfish and squid, which are thin diagonal shapes that use little of the cell. |
| G2 tier hierarchy under blur | 4 | Lows collapse to dim teal smudges; squid, maw, leviathan, angler and viper keep shape. But the helmet (a mid) pops about as hard as the highs even after the grade, and the Leviathan is not clearly the loudest symbol: the pale squid and the red maw beat it. |
| G3 one light | 3 | The cyan upper-left rim is visible on the tablets' top-left edges, the maw ring, the leviathan and the viper. The helmet and compass are lit more frontally and warmly, the maw and leviathan carry their own inner red/orange light (allowed by the bible, but it dilutes the single-source read), and the low glyphs are self-lit. |
| G5 cohesion | 4 | Same oil-paint brush, grain and desaturated palette across lows, mids, highs and wild; no frames except Wild, no text anywhere. The lows are slightly smoother than the creatures, and the helmet is cleaner than the rest. |

## What still falls short

- **Lows glow all the time.** The bible says "glow only on win". The even-glow set was chosen for 64 px legibility; a dimmer idle set exists for 10/J/Q/A (`low2_a_*_s11`) but its J and Q nearly disappear under blur. The engine should dim the groove at idle and raise it on win, which needs a separate emissive mask that was not made here.
- **The five tablets are close to identical in outline** (same seed). Good for construction, but 15 or more on screen may look stamped; a second slab seed per glyph would help.
- **Leviathan is not a convincing apex.** It reads as a horned demon-fish head, is the darkest high, ends in a floating neck stump, and was not matched to the existing hero Leviathan art. It needs a design pass against the hero creature.
- **Mid/high separation relies partly on a post grade**; the brass helmet is still nearly as bright as the creatures.
- **Viperfish and squid silhouettes are thin diagonals**, so at 112% the viper's tail enters the cell below while both still read smaller than the angler.
- **Angler lure**: the bulb survived, but its glow halo was removed by the cut-out and the stalk is a 1 px line at 64 px. The glow should be added back in engine as an additive sprite.
- **Squid** lost its translucency in the cut-out (opaque matte) and has a rainbow sheen that is slightly off-palette.
- **Wild has no WILD lettering** (not attempted; the brief allowed text only if perfect) and it is not animated.
- **Compass** is a star-rose bowl seen from above; the needle is weak and it could be read as a porthole at 64 px.
- **Not covered**: Pearl/scatter, Dead Sediment, win-state variants, normal maps, atlas packing, any in-engine check. The sheets are Pillow composites, not game captures.
- Light direction was requested in every prompt but not enforced; no relighting was done.
