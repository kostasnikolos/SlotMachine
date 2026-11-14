# Moments target: master key frame, the Help, the Win

Target paintings for the rebuild. They show how the screen and its two signature moments should look before anyone
touches the engine. Nothing here is a screenshot of the game.

| Deliverable | File |
| --- | --- |
| Idle game screen, 1920x1080 | `artifacts/targets/keyframe_master.png` |
| Help storyboard H0-H5, 3x2 | `artifacts/targets/storyboard_help.png` |
| Win storyboard W1-W3, 3x1 | `artifacts/targets/storyboard_win.png` |
| Every storyboard panel at full 1920x1080 | `generated/targets/moments/frames/H0..H5.png`, `W1..W3.png` |
| Layers for the rebuild | `generated/targets/moments/layers/` |
| Raw paints, one `.json` provenance sidecar each | `generated/targets/moments/` |
| Symbol cut-outs | `generated/targets/moments/cut/` |
| Scripts (repeatable, no manual steps) | `generated/targets/_scripts/` |

Rebuild everything from the raw paints: `python generated/targets/_scripts/build_master.py`, `build_help.py`,
`build_win.py`. Repaint a missing raw image: `python generated/targets/_scripts/paint_batch.py` (it paints every
entry of `prompts.json` that has no PNG yet; ComfyUI with Z-Image-Turbo must be running).

---

## 1. What the Help actually does in the engine

Source: `slot_engine/core/state_machine.py` (cascade loop), `slot_engine/core/creature.py` (`LeviathansMaw.strike_lifeline`),
`slot_engine/core/progression.py` (`pending_lifeline`), `slot_engine/static/canvas/index.html` (`strikeSeq`).

**When it fires.** Not after every losing spin. Inside a round, when the tumble stalls (an evaluation finds no win), the
engine checks `gauge.pending_lifeline and current_level > LEVEL_0_SUNLIGHT`. `pending_lifeline` is armed by a depth
level-up (`add_points`), by the pearl ascension to level 5, and at the start of an xBet round. It is consumed by one
strike. So the Help is "the board has gone dead at a depth you have just reached, and the creature gives it one more
chance". After the strike the engine `continue`s the cascade loop, so the changed grid is evaluated again; a win is
likely but not guaranteed.

**What it does to the grid** depends on the depth level:

| Level | Name in code | Footprint | Effect |
| --- | --- | --- | --- |
| 1 Twilight | The Lurker | 1x1, random cell | That cell becomes `WILD_MAW`. Each of the four orthogonal neighbours that holds a LOW rune becomes a MID (helmet or compass, random). Neighbours that are not lows are left alone. |
| 2 Midnight | The Stalker | 2 rows x 1 column | Both cells become `WILD_MAW`; adjacent mids are transmuted to high predators. |
| 3 Abyss | The Maelstrom | 2x2 | Injects wild multipliers (x2, x3 or x5 per cell). |
| 4 Hadal | The Tentacles | 3x3 | Cells become wilds and highs (Leviathan, squid). |
| 5 Core | The Awakened | 2x2 | Sticky roaming wild block, x2. |

The event `CREATURE_LIFELINE_STRIKE` carries `position` (top-left cell), `size` (h, w), `transmuted`
(coord, old symbol, new symbol, multiplier), the grid after the strike, `respins_awarded` (always 2 in the event; I found
no reader of it in `slot_engine/core`), and `spins_added`: with `BITE_RETRIGGER_CHANCE` 0.15 a strike during free spins or
with spins banked adds one spin ("second breath", max 3 per round).

**The storyboard paints level 1**, the first Help a player meets: strike cell = centre (row 2, col 2, zero-based), and all
four neighbours happen to be lows, so the result is a cross: Wild Maw in the middle, compass above, helmet left,
compass right, helmet below. The grid was chosen so that H0 is a true dead board (no symbol on reels 1 and 2 together)
and so that after the strike a helmet way exists across reels 1-4 (helmet, helmet, wild/helmet, helmet).

### Where the real `strikeSeq` differs from the shared beat sheet

The numbering H0-H5 is kept. The differences matter for the sound designer:

1. **The stillness is longer.** `levPreStrike(1500 + random*900)`: 1.5 to 2.4 s of hush (ambience down 12 dB, creature
   dark and still) before anything moves. The beat sheet gives DREAD 600 ms.
2. **It is a lunge with jaws, not a shadow pass.** After the hush the whole creature painting (`lev_lunge`) rushes from far
   to near at the strike cell (zoom 0.22 to 1.0), all other cells are dimmed (`engDim`), water churns on the cell
   (`E.rip`). There is no separate "shadow crosses the grid" beat in code; H2 here is a proposal.
3. **Impact** matches: chomp, `levBite`, `heavyImpact('leviathan', hitStopMs)`, and the name card appears on the hit-stop.
4. **The transformation comes late and the creature is already gone.** After the bite the painting drops away
   (`hero.stop(450)`, "plunge", 850 ms + 250 ms), and only then do the wilds "surface alone out of the churning water",
   one cell every 110 ms (70 ms at levels 4-5), then neighbours transmute 60 ms apart, then an 1100 ms hold. So in code
   H4 starts about 1.1 s after H3, not 80 ms, and the whole sequence is roughly 5-6 s, not 2.4 s.
5. **Order inside H4**: footprint cells (the wild) first, then the transmuted neighbours. The painting shows all five lit
   at once; animate them in that order.

If the 2.4 s beat sheet is the new target, the code needs the hush cut to about 600 ms and the surfacing moved up to the
hit-stop release. That is a design decision, not something these paintings settle.

---

## 2. Frame by frame

Camera, frame, backdrop and HUD text are identical in every panel. Only the state changes.

### Master (idle)
The player should feel they are looking through a bolted viewport into something very deep and not empty. Trench walls
left and right, marine snow drifting, the frame heavy and wet. The grid sits inside the frame on a dark glass-like
backplane. Behind the upper-left of the reels a pale skull-plated head with one lit eye is just visible between the
tiles, and its spined coils show in the water to the right of the frame. That eye is the key light: tiles and frame are
brightest toward the upper centre-left and fall off to the corners. What moves at idle: snow, a slow breathing of the
key light, the gauge level, the coils.

### H0 DEAD SPIN, 0 ms
Feeling: flat, a small loss, quiet. Light is lower than idle, the creature is fainter, nothing glows. Nothing moves except
snow. This is the moment the sound drops.

### H1 DREAD, 0-600 ms
Feeling: being watched. Ambient falls to about a third, the frame goes nearly black, and an eye roughly three cells wide
opens behind the reels, its slit pupil sitting in the gap between reels 2 and 3. Symbols become black silhouettes against
the iris. What moves: the lid opening (bottom to top), the pupil narrowing, tendrils drifting outside the left pillar.

### H2 APPROACH, 600-1100 ms
Feeling: it is coming for one cell. The eye is gone; the creature's body passes between its own light and the reels, so
a serpent-shaped shadow with a thin cyan rim slides in from the left with its head on the strike cell. Tiles under the
shadow go dark. The five cells that will be hit shiver by a few pixels, hairline stress cracks creep in from three frame
corners, grit falls from the lintel, the screen has a 3 px tremor.

### H3 IMPACT, 1100 ms
Feeling: a hit in the chest, then held. The maw comes through the strike cell head-on, needle teeth, the lure lit in its
throat, a ring of pressurised water and bubbles blasting out over the neighbouring cells and the frame. The strike cell's
symbol is gone (it is in the mouth), the four neighbours are knocked outward and lit, the rest are dimmed. Glass cracks
radiate from the cell. Chromatic split of 5 px and a 13 px shake; this frame is the hit-stop frame.

### H4 TRANSFORMATION, 1180-1700 ms
Feeling: relief turning into greed. The strike cell holds the Wild Maw (blood-red throat in an iron ring, the only blood
accent on screen), the four neighbours are brass now and lit cyan, all five scaled up about 10-18% and haloed. Spray is
still in the air, one jet still falls from the centre cell, a cross-shaped crack joins the five cells. The other twenty
cells stay dim. The jaws are only a faint shape sinking below the centre.

### H5 AFTERMATH, 1700-2400 ms
Feeling: it is over and you are better off. Light returns to near H0, the five new symbols keep a low glow, thin sheets
of water run down from them over the lower rows and off the sill, the cross scar is a dim cyan line, and the creature is
a pale shape low on the right, leaving. The board is ready to be evaluated again (the helmet way is there to be found).

### W1 THE WAY IS FOUND, 0-150 ms
Feeling: a click of recognition. Four anglers on reels 1-4 (rows 2, 3, 3, 2) light from behind and a hairline fracture
runs through them left to right, crossing the gaps between cells, with a bright tip still travelling at 93% of the path
and short side cracks. Other cells drop to about 70%.

### W2 BREACH, 150-500 ms
Feeling: the hull gives, on exactly the line you are paid on. The fracture tears into a dark gap of uneven width with a
lit upper lip, water forces through along its whole length, and needle jets fire up and down from each symbol on the way
(long ones at the nodes, shorter opposing ones between). Spray reaches the left pillar. Winners at full brightness,
others at half, a 4 px shake.

### W3 IMPLOSION + SCAR, 500-900 ms
Feeling: the win is taken, not exploded. Each winner is crushed to a third of its size toward its own centre, short
streaks and a bubble or two show the suction, the cell behind it is dark. The seam has closed to a thin glowing scar that
stays. The win amount sits above the seam in Bone.

---

## 3. How the images were made

All paints: Z-Image-Turbo through `scripts/ai/comfy_tools.py paint`, 8 steps, no negative prompt. 36 paint calls in total,
13 BiRefNet cut-outs. No studio, game or artist is named in any prompt. Exact prompts, seeds and sizes are in
section 5 (generated from `generated/targets/_scripts/prompts.json`).

**Frame layer.** `frame_green_d` was painted on a green screen at 1024x1024. `key_frame.py` keys every large connected
green area (outside and opening), keeps small greenish specks on the metal, despills, and writes
`layers/frame_cut.png` (RGBA, opening fully transparent). Opening in painting pixels: bbox 207,195 to 818,837; safe inner
box 216,207 to 809,827. The raw green-screen painting is kept as `layers/frame_greenscreen_raw.png`.

**Symbols.** Mids, highs and specials: painted one per image on black, cut out with BiRefNet. Lows: painted as basalt
slabs on black; BiRefNet kept only the glyph of the Q, so `key_lows.py` keys all five by luminance instead (closing,
hole fill, largest component). The compositor desaturates and darkens lows so they recede.

**The stage** (`stage.py`, one `render(state)` for every image, 1920x1080):
1. Backdrop `backdrop_a`, cover-fit, desaturated a little, top 260 px faded (the paint had a bright surface).
2. Key light: two cyan radial glows at (860, 300), screen-blended.
3. Marine snow: 520 procedural specks, brighter near the key.
4. Frame shadow on the world, then the reel backplane inside the opening (Trench colour at 34-62% over the backdrop) and
   four soft reel separators.
5. Creature layer, screen-blended over the backplane and the world, under the symbols (black level lifted out, picture
   edges feathered, tinted toward teal). Idle: `creature_sil_d` at 1900 px with its eye placed on a reel gap at (892, 333).
6. Symbols: scale by tier (low 0.80, mid 0.98, high 1.16, special 1.04 of the cell), contact shadow away from the key,
   rim light on the edge facing the key, brightness falling off with distance from the key.
7. FX between symbols and frame (cracks, jets, jaws, scar), frame inner shadow, the frame itself relit with a radial light
   map from the key position, gauge level glow.
8. FX in front of the frame, large out-of-focus snow, vignette, HUD text (Bahnschrift), optional chromatic split and
   shake, film grain.

**Frame is 1024 px scaled 1.14 and centred**, so the grid box on screen is x 622-1298, y 192-899 (cell 135x141).

**Help sheet** (`build_help.py`): six states of the same stage. H1 uses `creature_eye_a` at 1900 px, gamma 1.45. H2 uses
`shadow_serpent_b` (black on white, inverted to a mask, 1000 px, rotated 12 degrees, clipped to the opening) to darken the
backplane and symbols, plus a rim glow from the blurred mask. H3 uses `fx_breach_jaws_a` at 640 px with a hole-filled
occlusion mask so it hides what is behind it, `fx_cracks_a` under it, `fx_burst_a` under and over the frame. H4 swaps the
five symbols, adds the procedural cross scar, `fx_burst_a` mist per cell and one `fx_jet_single`. H5 uses `fx_drain_a`
four times and the scar at lower strength. The sheet is 3x2 panels at 1280x720 with a label band (`sheet_util.py`).

**Win sheet** (`build_win.py`): the seam is procedural (`stage.seam`): a polyline through the four cell centres, displaced
by a coarse and a fine jag, drawn as a 2 px core with three blur radii of cyan halo and side branches; in W2 it is opened
into a variable-width dark gap whose upper lip is lit. Painted sprites on top: `fx_jets_a` laid along each segment and
rotated to it, `fx_jet_single` (cropped to drop the pool it lands in, saved as `fx_jet_single_crop.png`) at each node.
W3 scales and squashes the four winners, adds `fx_implode_a` debris tinted cyan, procedural suction streaks and bubbles.

Painted but not used: `backdrop_b`, `frame_green_a/b/c`, `frame_mag_a`, `creature_sil_a/b/c`, `sym_lows` (tablets too
narrow for a cell), `fx_breach_jaws_b`, `shadow_serpent_a`.

---

## 4. What these targets do not yet nail

1. **The Leviathan is not one consistent creature.** The idle silhouette (bone skull, serpent coils), the H1 eye, the H3
   maw (rounder, fish-like head, no bony plates) and the H2 shadow (smooth eel with a fin) are four separate paintings
   that agree on eel body, needle teeth, cyan eye and lure, but not on anatomy. They are also not matched to the existing
   `lev_eye` / `lev_lunge` / `lev_maw` paintings beyond those traits. A text-to-image model with no reference input
   cannot hold a character; the rebuild should use the existing hero paintings for H1 and H3.
2. **The idle silhouette reads as a pale ghost, not a mass.** You can find the skull and the eye behind reels 1-3 if you
   look, but 25 tiles cover most of it and it does not read at storyboard size. The coils to the right of the frame carry
   more of the "it is there" than the head does.
3. **H1: the eye is hard to read small.** At 1920 the iris and slit are clear in the reel gap; in the sheet it is a cyan
   glow with dark tiles on it. It needs motion (the lid opening) to work, or tiles that go translucent during dread.
4. **H2 is the weakest frame.** The shadow reads as a dark limb entering from the left; its head is hidden under tiles,
   and the "frame strains" part is three faint cracks and some grit. No bending metal, no popped rivet. It is also the
   one beat that has no counterpart in the current code.
5. **H3 is centred and symmetrical.** The maw is head-on and sits politely inside the frame. The engine's lunge comes
   from far to near with a body behind it; this frame has no body and breaks the frame only with spray.
6. **The frame has no sonar, no ritual bar, no rune seals.** The art bible asks for a sonar top-right and five seals in
   the bottom lintel. The painted frame has a depth gauge in the left pillar and round brass bosses; the three small
   discs in the sill could become seals but are not five and are not designed.
7. **The gauge is a tube with a procedural glow**, no numerals, no needle animation design. Zone and depth are plain text
   in the corner, which is exactly the web-UI habit the bible wants gone.
8. **No spin button, bet controls or win meter are designed.** The HUD is four lines of text placed outside the frame.
9. **The frame is a square in a 16:9 screen**, so a third of the width is empty trench. That is honest to a 5x5 grid but
   the side space has no job yet. Portrait is not addressed at all.
10. **Seam and scars are procedural lines.** They are better than the first pass (which looked like lightning) but W1 and
    W3 can still read as electricity rather than a crack in glass. There is no refraction of the symbols under the seam
    and no silt current along it, both of which the ideation brief asks for.
11. **W2 jets are vertical only.** The brief wants them perpendicular to the path and spraying toward the viewer. The
    painted jet sprite is a small waterfall, slightly soft when stretched over 1.75 cells.
12. **W3 implosion is a scale-down.** No folding metal, no crushed slug. The brief's six-frame crush strip was not painted.
13. **Lows are slabs, not bare glyphs.** The bible says carved glyphs on transparent ground, about 70% of the cell, no
    fill. A slab reads better against a busy backplane, but it is a deviation, and 14 slabs on a board is a lot of the
    same grey square.
14. **Style drift between layers.** Backdrop is slightly graphic (hard-edged shapes), symbols are soft oil paint, the frame
    is closer to a 3D render. Grain, vignette and one light pull them together at a glance, not under scrutiny (gate G5).
15. **The angler symbol has no lure and the "leviathan" high symbol is a bone-headed fish.** Fine as stand-ins.
16. **Depth grade.** Everything is painted at the cyan tier. No sulfur or blood grade variants of either moment.
17. **Phone-size readability (gate G1) was not tested.**
18. **Stills only.** Timing, easing, hit-stop length and shake curves are described in words, not shown.

---

## 5. Prompts, seeds, sizes

Suffix appended to every prompt except the two `shadow_serpent` ones:

> Dark painterly digital concept art, gritty horror-industrial mood, desaturated, visible brushwork, film grain, cold cyan bioluminescent light, near-black teal shadows, premium game key art.

| Image (`generated/targets/moments/<name>.png`) | Seed | Size | Used for |
| --- | --- | --- | --- |
| `backdrop_a` | 11 | 1344x768 | master + every panel: backdrop |
| `backdrop_b` | 23 | 1344x768 | not used |
| `frame_green_a` | 5 | 1152x896 | not used |
| `frame_mag_a` | 6 | 1152x896 | not used |
| `creature_sil_a` | 31 | 1344x768 | not used |
| `frame_green_b` | 41 | 1152x896 | not used |
| `frame_green_c` | 42 | 1152x896 | not used |
| `frame_green_d` | 43 | 1024x1024 | the frame (keyed) |
| `creature_sil_b` | 52 | 1344x768 | not used |
| `creature_sil_c` | 53 | 1344x768 | not used |
| `creature_eye_a` | 61 | 1344x768 | H1 eye |
| `sym_lows` | 71 | 1344x768 | not used |
| `sym_helmet` | 72 | 768x768 | symbol |
| `sym_compass` | 73 | 768x768 | symbol |
| `sym_angler` | 74 | 768x768 | symbol |
| `sym_squid` | 75 | 768x768 | symbol |
| `sym_viper` | 76 | 768x768 | symbol |
| `sym_leviathan` | 77 | 768x768 | symbol |
| `sym_wild` | 78 | 768x768 | symbol |
| `sym_scatter` | 79 | 768x768 | symbol |
| `fx_breach_jaws_a` | 81 | 1024x1024 | H3 maw, H4 receding |
| `fx_breach_jaws_b` | 82 | 1024x1024 | not used |
| `fx_burst_a` | 83 | 1024x1024 | H3 burst, H4 mist, W2 spray |
| `fx_jets_a` | 84 | 1344x768 | W2 torn seam strips |
| `fx_jet_single` | 85 | 768x768 | W2 jets, H4 jet |
| `fx_drain_a` | 86 | 1024x1024 | H5 drains, W3 drips |
| `fx_cracks_a` | 87 | 1024x1024 | H3 glass cracks |
| `fx_implode_a` | 88 | 768x768 | W3 debris |
| `creature_sil_d` | 54 | 1344x768 | idle silhouette (master, H0, H5, W1-W3) |
| `sym_low_10` | 91 | 768x768 | symbol |
| `sym_low_j` | 92 | 768x768 | symbol |
| `sym_low_q` | 93 | 768x768 | symbol |
| `sym_low_k` | 94 | 768x768 | symbol |
| `sym_low_a` | 95 | 768x768 | symbol |
| `shadow_serpent_a` | 101 | 1344x768 | not used |
| `shadow_serpent_b` | 102 | 1344x768 | H2 shadow |

Prompts as sent (before the suffix):

**`backdrop_a`** (seed 11, 1344x768)

> Wide view straight into a bottomless deep-sea trench at crushing depth. Towering black basalt cliff walls on the far left and far right recede into darkness, hexagonal basalt columns, hydrothermal chimneys with faint smoke far below. The centre is open black water falling away into the abyss. A soft cold cyan glow hangs in the water in the upper centre-left, like something huge and luminous is far behind the murk. Drifting marine snow particles, faint light shafts, silt haze. No creatures, no text, very dark, colours near black with teal and cyan only.

**`backdrop_b`** (seed 23, 1344x768)

> Matte painting of an abyssal ocean trench seen from inside it, looking along the canyon. Jagged black basalt rock walls and broken pillars frame the left and right edges, a wrecked rusted chain hangs from above, the middle distance dissolves into blue-black fog. One diffuse cyan bioluminescent glow in the upper centre-left of the water. Marine snow drifting everywhere, tiny specks. No creatures, no text, extremely dark, teal and cyan only.

**`frame_green_a`** (seed 5, 1152x896)

> Front-on, perfectly symmetrical, flat orthographic view of a massive square doorway frame built from rough black basalt blocks clad with corroded riveted submarine steel plates and tarnished brass fittings. Thick heavy pillars on the left and right, a heavy lintel beam across the top and a heavy sill across the bottom, big rivets, weld seams, barnacles, wet metal with cold cyan rim light from the upper left. Embedded in the left pillar is a tall vertical brass depth gauge: a glass tube with tick marks and a small needle. The large square opening in the middle of the frame is completely empty and filled with flat solid pure bright green, and the background outside the frame is the same flat solid pure bright green. Game asset on a green screen.

**`frame_mag_a`** (seed 6, 1152x896)

> Front-on, perfectly symmetrical, flat orthographic view of a massive square doorway frame built from rough black basalt blocks clad with corroded riveted submarine steel plates and tarnished brass fittings. Thick heavy pillars on the left and right, a heavy lintel beam across the top and a heavy sill across the bottom, big rivets, weld seams, barnacles, wet metal with cold cyan rim light from the upper left. Embedded in the left pillar is a tall vertical brass depth gauge: a glass tube with tick marks and a small needle. The large square opening in the middle of the frame is completely empty and filled with flat solid pure magenta, and the background outside the frame is the same flat solid pure magenta. Game asset on a flat magenta background.

**`creature_sil_a`** (seed 31, 1344x768)

> An enormous eel-like sea serpent leviathan barely visible in pitch black deep water, its armoured head facing the viewer in the upper left of the picture, long thin needle teeth, pale bony plates on the skull, one glowing cyan eye with a vertical slit pupil, thin trailing barbels, its coiling spined body fading away to the right into darkness. Only faint cyan rim light picks out its outline; most of it is lost in black. Pure black background, no rocks, no text.

**`frame_green_b`** (seed 41, 1152x896)

> Front-on flat orthographic elevation, no perspective, no floor, of a huge square picture-frame-like bulkhead surround: a thick border made of rough black basalt blocks bound with corroded riveted submarine steel plates, girders and tarnished brass fittings, big rivets, weld seams, barnacles, rust streaks, wet metal catching a cold cyan rim light from the upper left. The border is thick but the square opening is very large and takes up most of the picture. The left side of the border is a wider pillar with a tall vertical brass depth gauge set into it: a glass tube with engraved tick marks and a small needle. The top beam is a heavy lintel, the bottom beam a heavy sill with five small round stone seals. The big square opening in the middle is completely empty, filled with flat solid pure bright green, and everything outside the frame is the same flat solid pure bright green. Isolated game asset on a green screen, realistic gritty oil painting, muted colours, dark.

**`frame_green_c`** (seed 42, 1152x896)

> Front-on flat orthographic elevation, no perspective, no floor, of a huge square picture-frame-like bulkhead surround: a thick border made of rough black basalt blocks bound with corroded riveted submarine steel plates, girders and tarnished brass fittings, big rivets, weld seams, barnacles, rust streaks, wet metal catching a cold cyan rim light from the upper left. The border is thick but the square opening is very large and takes up most of the picture. The left side of the border is a wider pillar with a tall vertical brass depth gauge set into it: a glass tube with engraved tick marks and a small needle. The top beam is a heavy lintel, the bottom beam a heavy sill with five small round stone seals. The big square opening in the middle is completely empty, filled with flat solid pure bright green, and everything outside the frame is the same flat solid pure bright green. Isolated game asset on a green screen, realistic gritty oil painting, muted colours, dark.

**`frame_green_d`** (seed 43, 1024x1024)

> Front-on flat orthographic elevation, no perspective, no floor, of a huge square picture-frame-like bulkhead surround: a thick border made of rough black basalt blocks bound with corroded riveted submarine steel plates, girders and tarnished brass fittings, big rivets, weld seams, barnacles, rust streaks, wet metal catching a cold cyan rim light from the upper left. The border is thick but the square opening is very large and takes up most of the picture. The left side of the border is a wider pillar with a tall vertical brass depth gauge set into it: a glass tube with engraved tick marks and a small needle. The top beam is a heavy lintel, the bottom beam a heavy sill with five small round stone seals. The big square opening in the middle is completely empty, filled with flat solid pure bright green, and everything outside the frame is the same flat solid pure bright green. Isolated game asset on a green screen, realistic gritty oil painting, muted colours, dark.

**`creature_sil_b`** (seed 52, 1344x768)

> A colossal deep-sea leviathan looming out of total darkness, seen head-on and very large, filling the frame: an armoured eel-like head with pale bony skull plates, rows of long thin translucent needle teeth in a slightly open jaw, two cold cyan eyes with vertical slit pupils glowing, thin trailing barbels, a small glowing cyan lure hanging in front of its mouth, spined serpent body curling away behind into the black. Almost everything is lost in black murk; only faint cyan rim light and the glowing eyes read. Pure black background, underexposed, no rocks, no text.

**`creature_sil_c`** (seed 53, 1344x768)

> A colossal deep-sea leviathan looming out of total darkness, seen head-on and very large, filling the frame: an armoured eel-like head with pale bony skull plates, rows of long thin translucent needle teeth in a slightly open jaw, two cold cyan eyes with vertical slit pupils glowing, thin trailing barbels, a small glowing cyan lure hanging in front of its mouth, spined serpent body curling away behind into the black. Almost everything is lost in black murk; only faint cyan rim light and the glowing eyes read. Pure black background, underexposed, no rocks, no text.

**`creature_eye_a`** (seed 61, 1344x768)

> Extreme close-up of one enormous reptilian eye of a deep-sea leviathan opening in pitch black water: a glowing cyan iris with a thin vertical slit pupil, surrounded by dark wet teal scales and pale bony ridge plates, thin barbels drifting. The eye is the only light source and glows strongly; everything around falls off quickly to pure black. Pure black background, no text.

**`sym_lows`** (seed 71, 1344x768)

> Five separate rough carved black basalt stone tablets in one horizontal row, evenly spaced, each with one large deeply chiselled glyph: the first reads 10, the second J, the third Q, the fourth K, the fifth A. Chipped edges, wet stone, the carved grooves catch a faint cyan light from the upper left. Isolated on a pure flat black background. Realistic gritty oil painting, muted colours, game symbols.

**`sym_helmet`** (seed 72, 768x768)

> An antique tarnished brass deep-sea diving helmet with a round glass porthole, barnacles and verdigris. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted colours, game symbol icon.

**`sym_compass`** (seed 73, 768x768)

> An antique tarnished brass ship's compass with a cracked glass and engraved dial, verdigris and barnacles. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted colours, game symbol icon.

**`sym_angler`** (seed 74, 768x768)

> A monstrous deep-sea anglerfish with needle teeth and a glowing cyan lure, side three-quarter view, dark wet skin. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted colours, game symbol icon.

**`sym_squid`** (seed 75, 768x768)

> A sinister deep-sea vampire squid with curling tentacles and one pale eye, dark crimson-black skin, faint cyan glowing spots. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted colours, game symbol icon.

**`sym_viper`** (seed 76, 768x768)

> A deep-sea viperfish coiled like a snake, huge fangs, silver-black scales, tiny glowing cyan photophores along its belly. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted colours, game symbol icon.

**`sym_leviathan`** (seed 77, 768x768)

> The head of an armoured eel-like sea leviathan with pale bony skull plates, long needle teeth and one glowing cyan slit-pupil eye, emerging from darkness, three-quarter view. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted colours, game symbol icon.

**`sym_wild`** (seed 78, 768x768)

> A round gaping lamprey-like maw seen head-on, concentric rings of long needle teeth around a deep blood-red glowing throat, set inside a heavy round riveted black iron ring like a porthole, blood red glow from inside. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted colours, game symbol icon.

**`sym_scatter`** (seed 79, 768x768)

> A large luminous pearl held in a black iron claw setting shaped like a sonar ring, the pearl glowing cyan-white from within, small bubbles. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted colours, game symbol icon.

**`fx_breach_jaws_a`** (seed 81, 1024x1024)

> Seen head-on: the gaping jaws of an armoured eel-like deep-sea leviathan bursting straight toward the viewer out of total darkness, mouth wide open, rings of long thin translucent needle teeth, pale bony skull plates, a glowing cyan throat and a small cyan lure, thin barbels whipping, and an explosive ring of white-cyan pressurised water spray and bubbles blasting outward around the head. Dramatic cold cyan backlight. Isolated on a pure flat black background, nothing else in the picture, no text. Realistic gritty oil painting, high contrast, overlay effect sprite.

**`fx_breach_jaws_b`** (seed 82, 1024x1024)

> Seen head-on: the gaping jaws of an armoured eel-like deep-sea leviathan bursting straight toward the viewer out of total darkness, mouth wide open, rings of long thin translucent needle teeth, pale bony skull plates, a glowing cyan throat and a small cyan lure, thin barbels whipping, and an explosive ring of white-cyan pressurised water spray and bubbles blasting outward around the head. Dramatic cold cyan backlight. Isolated on a pure flat black background, nothing else in the picture, no text. Realistic gritty oil painting, high contrast, overlay effect sprite.

**`fx_burst_a`** (seed 83, 1024x1024)

> A violent radial burst of pressurised seawater exploding outward from a central point toward the viewer: white-cyan spray, foam, fine mist, droplets and bubbles flying in all directions, brightest at the centre, lit cold cyan. Isolated on a pure flat black background, nothing else in the picture, no text. Realistic gritty oil painting, high contrast, overlay effect sprite.

**`fx_jets_a`** (seed 84, 1344x768)

> A long horizontal jagged crack torn open across the picture from the left edge to the right edge, glowing bright cyan from inside, and from it several thin high-pressure needle jets of seawater spraying up and down, atomising into fine white-cyan mist and droplets. Isolated on a pure flat black background, nothing else in the picture, no text. Realistic gritty oil painting, high contrast, overlay effect sprite.

**`fx_jet_single`** (seed 85, 768x768)

> One thin high-pressure needle jet of seawater spraying straight down from a small bright point at the top centre, widening into a cone of fine white-cyan mist and droplets at the bottom, lit cold cyan. Isolated on a pure flat black background, nothing else in the picture, no text. Realistic gritty oil painting, high contrast, overlay effect sprite.

**`fx_drain_a`** (seed 86, 1024x1024)

> Thin streams and sheets of seawater running straight down and dripping, a few falling droplets and rising bubbles, faintly lit cyan from above, sparse, mostly empty black. Isolated on a pure flat black background, nothing else in the picture, no text. Realistic gritty oil painting, high contrast, overlay effect sprite.

**`fx_cracks_a`** (seed 87, 1024x1024)

> A network of thin jagged fracture cracks spreading outward from the centre like cracked thick glass, the crack lines glowing faint cyan, thin and sharp, sparse. Isolated on a pure flat black background, nothing else in the picture, no text. Realistic gritty oil painting, high contrast, overlay effect sprite.

**`fx_implode_a`** (seed 88, 768x768)

> A small crumpled knot of crushed black stone and torn brass at the centre, imploding: a ring of dark dust and a few bright cyan flecks and short streaks all being sucked inward toward the centre, one small air bubble rising. Isolated on a pure flat black background, nothing else in the picture, no text. Realistic gritty oil painting, high contrast, overlay effect sprite.

**`creature_sil_d`** (seed 54, 1344x768)

> A colossal armoured eel-like sea serpent leviathan seen head-on and far away in pitch black water, its head in the upper left looking straight at the viewer, pale bony skull plates, a closed mouth with long needle teeth showing, two small cold cyan slit-pupil eyes glowing, thin barbels, and its very long spined serpent body coiling away behind it to the right and downward into darkness. Underexposed, almost a silhouette, only thin cyan rim light. Pure black background, no rocks, no text.

**`sym_low_10`** (seed 91, 768x768)

> One rough square slab of black basalt stone, chipped irregular edges, wet, with a single large deeply chiselled glyph carved into its face that reads "10" in a heavy serif letterform. The carved grooves are dark with a very faint cyan glint. No frame, no metal. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted grey-teal colours, game symbol icon.

**`sym_low_j`** (seed 92, 768x768)

> One rough square slab of black basalt stone, chipped irregular edges, wet, with a single large deeply chiselled glyph carved into its face that reads "J" in a heavy serif letterform. The carved grooves are dark with a very faint cyan glint. No frame, no metal. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted grey-teal colours, game symbol icon.

**`sym_low_q`** (seed 93, 768x768)

> One rough square slab of black basalt stone, chipped irregular edges, wet, with a single large deeply chiselled glyph carved into its face that reads "Q" in a heavy serif letterform. The carved grooves are dark with a very faint cyan glint. No frame, no metal. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted grey-teal colours, game symbol icon.

**`sym_low_k`** (seed 94, 768x768)

> One rough square slab of black basalt stone, chipped irregular edges, wet, with a single large deeply chiselled glyph carved into its face that reads "K" in a heavy serif letterform. The carved grooves are dark with a very faint cyan glint. No frame, no metal. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted grey-teal colours, game symbol icon.

**`sym_low_a`** (seed 95, 768x768)

> One rough square slab of black basalt stone, chipped irregular edges, wet, with a single large deeply chiselled glyph carved into its face that reads "A" in a heavy serif letterform. The carved grooves are dark with a very faint cyan glint. No frame, no metal. Single object centred, isolated on a pure flat black background, lit by one cold cyan light from the upper left, rest in deep shadow. Realistic gritty oil painting, muted grey-teal colours, game symbol icon.

**`shadow_serpent_a`** (seed 101, 1344x768)

> A solid pure black silhouette of a huge eel-like sea serpent leviathan seen from the side, swimming diagonally down from the upper left corner toward the lower right, its head at the lower right with jaws wide open showing long needle teeth, spines along its back, thin trailing barbels, long body trailing off the upper left edge of the picture. Completely flat black shape with no interior detail, on a plain flat white background. Clean cut-out silhouette.

**`shadow_serpent_b`** (seed 102, 1344x768)

> A solid pure black silhouette of a huge eel-like sea serpent leviathan seen from the side, swimming diagonally down from the upper left corner toward the lower right, its head at the lower right with jaws wide open showing long needle teeth, spines along its back, thin trailing barbels, long body trailing off the upper left edge of the picture. Completely flat black shape with no interior detail, on a plain flat white background. Clean cut-out silhouette.

