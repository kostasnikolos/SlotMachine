# Moments target: master key frame, the Help, the Win (round 3)

Round 3 answers `docs/targets/review_round2.md` (T1, T2, T3, T5) and adds the game-ready frame pack. The round-2 notes
follow below; where they disagree with this section, this section is current.

## Round 3: what changed

**New and changed files**

| File | What |
| --- | --- |
| `generated/targets/moments/game_frame/` | The game pack: 33 WebP files + `frame_layout.json`, 0.48 MB on disk |
| `artifacts/targets/keyframe_master_from_pack.png` | Landscape master rebuilt from the pack + JSON only (`assemble_from_pack.py`) |
| `artifacts/targets/game_frame_assembled.png` | The pack alone, assembled on transparency, unlit |
| `artifacts/targets/keyframe_master_390.png` | Portrait master at 390 px wide (legibility proof) |
| `artifacts/targets/keyframe_master.png`, `keyframe_master_portrait.png`, `storyboard_win.png`, `storyboard_help.png` | Rebuilt |
| `generated/targets/_scripts/hud.py` | Everything the game draws live (labels, values, lit states), driven by `frame_layout.json` |
| `generated/targets/_scripts/measure.py` | The 8 px blur tier-ladder check |
| `generated/targets/_scripts/make_cone.py` | Builds the head-on jet sprite |

Build order: `frame.py` (layers + pack), `build_master.py`, `assemble_from_pack.py`, `build_help.py`, `build_win.py`, `measure.py`.

**T1, frame parts.**
- The generator's nonsense engraving is removed from the brass scale (a tall vertical blur of the strip keeps the brass
  shading) and `frame.py` cuts a real scale: 50 even ticks with 0 / 1K / 2K / 5K / 11K on the depth gauge, 25 ticks
  with 1-5 on the ritual bar.
- Five distinct rune seals: one painted blank basalt disc (`r3_seal_blank`) with five different runes cut in code, each
  in an off and a lit state (the whole cut fills with sulfur light and the iron ring catches it).
- Plates are blank in the layers and in the pack. No label, value or lit state is baked anywhere.
- Four different corner plates (four separate paintings). Two different pillars (two paintings). Lintel and sill use
  the same girder painting, the sill rotated 180 degrees and offset: the second girder paint came out too thin to use.
- The basalt outline fades into the water over about 7 px instead of ending in a hard cut, and is darker.

**T2, HUD.** Read-only instruments stay painted (gauge, sonar, ritual bar, seals, zone plate). Controls:
- Balance, bet and win: Bone values in a dark window let into the brass plate, drawn live by `hud.py`.
- Bet steppers: minus and plus buttons either side of BET (landscape 70x88, portrait 180x104 stage px).
- Spin: the wheel with a hub in three states (`spin_hub_idle`, `_ready`, `_spinning`). Ready is lit sulfur with a
  circular-arrow glyph; spinning is a cyan stop square.
- xBet and bonus buy: hull-plate buttons with the label and the price on the face (`button_blank`, `button_blank_on`).
- Autoplay and turbo: two separate small buttons with a knob lamp; `hud.draw(..., auto_turbo=False)` omits them.
- A reserved DOM rectangle top right (`place.dom_reserved`): 404x92 in landscape, 376x94 in portrait. Nothing is drawn there.
- Portrait was laid out again: sonar and zone plate moved up into the world band; the console holds balance, bet,
  steppers, wheel, price buttons, auto and turbo.
- Measured on the 390 px render: digit height is about 7 px for balance, bet, win and prices. The reviewer's bar was
  14 px. See weaknesses.

**T3, tier ladder.** `stage.sym_gain()` grades every symbol by measurement: it blurs the scaled symbol by 8 px and sets
the gain that puts its peak on its tier's target (low 46, mid 92, high 116, apex 190, wild 195), so the ladder no
longer depends on how a file happens to be graded. The key falloff on symbols is limited to 0.94-1.07 (narrower than
the 0.85-1.15 asked for; at 0.90-1.10 a top-row low still beat a far-corner helmet). The glow on the backplane behind
the top-left cells was cut from 0.30 to 0.13 because it was adding to the lows there. `measure.py` on the final masters
(8 px blur, peak in the inner 56% of each cell):

| Tier | Landscape | Portrait |
| --- | --- | --- |
| lows (17) | 43-79 | 39-80 |
| mids (4) | 88-95 | 87-92 |
| highs (3) | 100-119 | 94-98 |
| Leviathan | 139 | 141 |

No low beats a mid, no mid beats a high, nothing ties the Leviathan. The check uses the inner 56% of each cell because
with the whole cell a high's overflow into a neighbouring low's cell is counted as that low (measured that way, the top-left
low reads 111 from the viper's head beside it).

**T5, win.**
- The seam is `stage.fracture()`: it wanders (two scales of displacement), its width varies along its length, its edge
  is chipped, and two faint secondary fractures leave it. It no longer turns a right angle: it runs along the row 2/3
  joint and then cuts diagonally through the third winner down to the joint under the fourth. It does not box the viper.
- W2 jets are hard head-on cones (`r3_fx_cone_headon`): dense radial spray, a broken spray ring on the glass, droplets
  thrown outward, one per winner, composited as lit refracting water; two jets then fall. Z-Image painted a side-view
  fountain for both head-on prompts (`r3_fx_cone_a/b`, unused), so the cone is built in code by `make_cone.py`.
- The lens-flare star and the dash marks are gone.
- W3b: the winners are folded, not shrunk. `stage.crumple()` squeezes the real angler file sideways into accordion
  folds with dark creases and lit ridges (100%, 82%, 58%, 28% along the way) in a soft cloud of silt. It is a warp of
  the real symbol, not a painted strip: three painted crush frames were tried (`r3_crush_1..3`) and rejected because
  the model painted a different, intact fish each time.

## The game pack: `generated/targets/moments/game_frame/`

Authored at 1x for a 1920x1080 stage (and 1080x1920 portrait). 0.48 MB on disk. As RGBA8 on the GPU: landscape
pieces 3.4 MB + shared sprites 1.4 MB = 4.9 MB; portrait pieces 3.4 MB instead of the
landscape ones (load one orientation at a time). The round-2 sheet was about 33 MB.

`frame_layout.json` has, per layout: `stage`, `grid` (x, y, 5x5, cell), `opening` (the transparent rect: grid + margin),
`pieces` (file, x, y, w, h in stage px, and `cells`: the same rect in units of one cell from the opening's top-left),
and `place`: a rect for every sprite and live element (`win`, `balance`, `bet`, `zone`, `seals[5]`, `sonar`,
`sonar_glass` as centre + radius, `gauge_tube`, `ritual_bar`, `wheel`, `hub`, `xbet`, `buy`, `auto`, `turbo`,
`auto_knob`, `turbo_knob`, `bet_minus`, `bet_plus`, `dom_reserved`). `sprites` maps each shared sprite to its file and use.

Frame pieces: top lintel and bottom sill (each with its two corner plates), left pillar (with the gauge housing and
its scale), right pillar, plus the left and right outriggers (landscape) or the console (portrait). The opening is
transparent in every piece and is the 5x5 grid of square cells plus a margin (12 px landscape, 8 px portrait). Each
piece carries its own shadow and its share of the basalt, so they are drawn in file order with no further work. For a
different cell size, multiply every `cells` rect by the new cell. The pieces are four fixed pieces, not a 9-slice
(the left pillar holds the gauge), so far from 146 px (landscape) or 184 px (portrait) cells they will soften.

| File | Size | Disk | Used by |
| --- | --- | --- | --- |
| `button_blank.webp` | 364x100 | 8 KB | shared |
| `button_blank_on.webp` | 364x100 | 9 KB | shared |
| `console_portrait.webp` | 1080x351 | 66 KB | portrait |
| `lintel.webp` | 1056x167 | 43 KB | landscape |
| `lintel_portrait.webp` | 1080x144 | 41 KB | portrait |
| `outrigger_l.webp` | 348x215 | 16 KB | landscape |
| `outrigger_r.webp` | 322x635 | 13 KB | landscape |
| `pillar_l.webp` | 182x763 | 30 KB | landscape |
| `pillar_l_portrait.webp` | 106x945 | 21 KB | portrait |
| `pillar_r.webp` | 125x763 | 27 KB | landscape |
| `pillar_r_portrait.webp` | 47x945 | 14 KB | portrait |
| `plate_blank.webp` | 380x92 | 9 KB | shared |
| `seal_1_lit.webp` | 68x68 | 3 KB | shared |
| `seal_1_off.webp` | 68x68 | 3 KB | shared |
| `seal_2_lit.webp` | 68x68 | 3 KB | shared |
| `seal_2_off.webp` | 68x68 | 3 KB | shared |
| `seal_3_lit.webp` | 68x68 | 3 KB | shared |
| `seal_3_off.webp` | 68x68 | 3 KB | shared |
| `seal_4_lit.webp` | 68x68 | 3 KB | shared |
| `seal_4_off.webp` | 68x68 | 3 KB | shared |
| `seal_5_lit.webp` | 68x68 | 3 KB | shared |
| `seal_5_off.webp` | 68x68 | 3 KB | shared |
| `sill.webp` | 1056x199 | 52 KB | landscape |
| `sill_portrait.webp` | 1080x192 | 50 KB | portrait |
| `sonar_housing.webp` | 267x249 | 15 KB | shared |
| `spin_hub_idle.webp` | 120x120 | 3 KB | shared |
| `spin_hub_ready.webp` | 120x120 | 5 KB | shared |
| `spin_hub_spinning.webp` | 120x120 | 4 KB | shared |
| `spin_wheel.webp` | 300x300 | 31 KB | shared |
| `stepper_minus.webp` | 72x72 | 0 KB | shared |
| `stepper_plus.webp` | 72x72 | 0 KB | shared |
| `switch_knob.webp` | 67x67 | 2 KB | shared |
| `switch_knob_on.webp` | 67x67 | 2 KB | shared |

`assemble_from_pack.py` rebuilds the landscape master from these files and the JSON only, over
`layers/master_plate_noframe.png` (the scene with no frame: backdrop, creature, reels, symbols). Its lighting is a
ten-line radial multiply. The result matches `keyframe_master.png` apart from small differences in sprite shadows and
the absence of film grain.

## Round 3: what is still not right

1. **Money text is about 7 px tall at 390 px wide**, half the reviewer's 14 px bar. It is readable in the render but
   does not meet the number. Meeting it needs balance and bet plates about twice as tall, so a taller console and a
   smaller grid in portrait. Not done.
2. **Landscape on a phone was not proved.** The right column (prices, auto, turbo) is small there; only portrait was
   rendered at 390.
3. **The W2 cones are procedural** and look it up close: straight streaks, slightly firework-like. A painted head-on
   jet would be better; the model would not give one.
4. **W3b is a warp, not a painting.** It reads as crushed at full size; at sheet size the first winner is a small dark
   crumple that is hard to identify as an angler.
5. **The seam's first third is still a fairly straight run** along the row 2/3 joint (it wanders by about 8 px). At
   sheet size that part can still read as a line.
6. **Help panels show the spin hub as "ready"** during the strike; it should be idle or spinning there. The help
   storyboard was rebuilt on the new frame and symbols and not otherwise touched.
7. **Lintel and sill share one girder painting** (rotated); outriggers and console use it too.
8. **Runes are drawn in code** with straight strokes: distinct, but mechanical next to the paint.
9. **Buttons are a 9-sliced corner plate.** They read as hull plates more than as buttons; there is no pressed or
   disabled state, and no confirm step is designed for xBet or bonus buy.
10. **Highs in portrait sit at 94-98**, just above the mids (87-92): the ladder holds there by a small margin.
11. **The pack is 1x.** Right for a 1920x1080 stage as asked; on a high-density phone the frame will be softer than
    the symbols.
12. Backdrop (and its stretch in portrait), reuse of one creature painting, cyan tier only, stills only: unchanged.

---

## Round 2 notes

| Deliverable | File |
| --- | --- |
| Idle screen, landscape 1920x1080 | `artifacts/targets/keyframe_master.png` |
| Idle screen, portrait 1080x1920 | `artifacts/targets/keyframe_master_portrait.png` |
| Help storyboard H0-H5 | `artifacts/targets/storyboard_help.png` |
| Win storyboard W1, W2, W3a, W3b | `artifacts/targets/storyboard_win.png` |
| Every panel at 1920x1080 | `generated/targets/moments/frames/` |
| Frame layers (2x) and metadata | `generated/targets/moments/layers/frame_cut.png` (3840x2160), `frame_cut_portrait.png` (2160x3840), `frame_meta_*.json` |
| Frame parts | `generated/targets/moments/layers/parts/` (girder, pillar, corner, basalt, gauge, sonar, valve, plate, switches, seal_1..5) |
| Backdrop layer | `generated/targets/moments/layers/backdrop.png` |
| Raw paints with provenance sidecars | `generated/targets/moments/` |
| Scripts | `generated/targets/_scripts/` |

Rebuild, in order (each is cheap to re-run and reads the symbol files that are on disk at that moment):

```
python generated/targets/_scripts/frame.py          # only if a frame part or the layout changed
python generated/targets/_scripts/build_master.py   # landscape + portrait
python generated/targets/_scripts/build_help.py
python generated/targets/_scripts/build_win.py
```

---

## 1. What changed, per review item

**Item 1, symbol set.** `stage.py` now reads `generated/targets/symbols/<key>.png` (low_10 ... wild_maw) at build time.
The second set (`sym_*` paints and `moments/cut/`) is no longer referenced and `cut/` was deleted. Sizes: lows 70% of
the cell, mids 90%, highs 110%, Leviathan 120%, Wild 100%. The lows' grooves sit at about 42% emission at rest and are
desaturated (the emissive mask is keyed from the cyan in each paint at load time), go to 100% plus bloom on a win, and
to 0 in H1. The brightness falloff across the grid was flattened (0.86 to 1.12 instead of 0.55 to 1.15). Measured on
the master at cell = 64 px: 95th-percentile luminance of the bottom-row lows is 59-61 against 58-96 for the other rows
(round 1: cell luminance 16-21 on the bottom row), and every glyph reads in my own 64 px downscale. Mids are
desaturated 28% in the compositor so brass reads as tarnished brass.

**Item 9, frame.** Not a single painting any more. `frame.py` builds it at 2x from parts: one painted girder, one
painted pillar and one painted corner plate (each upscaled x4 with Real-ESRGAN, then cropped to a true rectangle, so
every edge is straight), a painted basalt texture behind the steel with a broken outline, and a dark gasket lip. The
opening is the 5x5 grid plus a 12 px margin, exactly (754x754 at 1x in landscape, cell 146). The nine brass bosses and
the generator squiggles are gone; the only brass on the frame is instruments. Built in as physical parts:

- depth gauge in the left pillar: painted glass tube and brass scale, stencilled marks 0 / 1K / 2K / 5K / 11K and
  three enamel zone bands (cyan, sulfur, blood);
- sonar scope on its own bracket, top right, with a brass zone plate under it ("TWILIGHT ZONE");
- ritual bar and five rune seals in the bottom lintel;
- engraved brass plates for BALANCE and BET on a left outrigger and WIN in the top lintel (the win value is lit by the
  stage, so it is the only win read-out);
- a four-switch panel (XBET, BUY, AUTO, TURBO) on a rail, and the spin control as a handwheel at the bottom right.

Because it is assembled from parts, the same code produces the portrait frame: thinner pillars, and sonar, switches,
plates and wheel on a console under the sill.

**Item 10, master.** No corner text. Left third: trench and the creature's body (the hero `lev_lunge` painting,
mirrored, rotated 62 degrees, darkened to 62%). Right third: the instruments. Behind the reels there is only the key
light and the dark edge of the head; the pale skull of round 1 is gone. Portrait version added.

**Item 11, the creature is the hero.** H1 uses `lev_eye.png` at 1.4x with the whole slit pupil (43x206 px on screen)
in the gap between reels 2 and 3 across rows 1-2, both flanked by lows; every symbol's emission is 0 and brightness
is 16%, so tiles are black shapes on the iris. H3 uses `lev_lunge.png`: its maw (a ring of fangs with the lure in the
throat) is scaled so the ring is 1.6 cells wide and centred on the strike cell, and comes through the glass; its body
stays behind the symbols. The strike is off-centre (row 2, reel 4). The rest of the grid stays visible at 62%. There
is one hot highlight upper-left of the ring and a light ramp from the upper left; the full-frame chromatic split is
gone. `lev_maw.png` was tried and not used: its ring is cropped top and bottom by its own canvas.

**Item 12, H2 is a targeting beat.** The shadow pass and the lightning-shaped stress marks are deleted. Other cells
drop to 46%, the strike cell alone stays lit, the inner iris disc of `lev_eye` is slid 34 px toward that cell, a
painted whirlpool churns on the cell, and the glass over it bows out (a real local magnification of the picture, with
a lit arc on the upper-left of the dome and three short dark stress cracks).

**Item 13, H4 and H5.** The Wild Maw sits on the same centre at the same 1.6-cell size as H3's ring, then settles to
one cell in H5. It is the only red on screen and has the highest emission of any symbol (the red-keyed throat is
boosted). The four neighbours are the chosen helmet and compass, lit by rim light only, no warm glow. No untouched mid
is diagonal to the strike cell (the grid was rewritten). The scar is four straight dark cracks with a lit lip and wet
sheen, no glow. The creature's maw recedes below and behind the reveal in H4. Captions carry the 3.1 s timings:
H1 0-900, H2 900-1500, H3 1500, H4 1580-2300, H5 2300-3100, and the sheet header states what the code does today.

**Item 14, the win is water.** One fiction in every panel: the viewer's side is dry, the sea is behind the glass.
- The seam is a 2 px dark hairline with a thin lit lip on its upper-left edge, in straight segments with small kinks,
  routed along the joints between cells (row 2/3 joint, down the reel 3/4 joint, along the row 3/4 joint) with a short
  spur into each winner. No glow, no forks, no travelling spark.
- Water is composited by a new `stage.water()`: sprite luminance becomes a dark teal body plus cool white highlights
  scaled by distance from the key light, and its height map displaces the picture behind it (refraction). Nothing in
  the water is self-luminous.
- W2: a burst toward the viewer at the root of each spur, two jets that arc and fall, the first run-off.
- W3 is split. W3a holds the four winners at full size while "4.20" lights on the WIN plate and water runs down the
  glass to the sill (the run-off sprite the reviewer accepted in H5, plus a new one). W3b crushes them reel by reel
  (28%, 40%, 56%, 80% of size, so the order is visible) and leaves the seam as a wet line with beads and drips.
- Winners are `high_angler.png` from the chosen set. No bubbles are drawn by the compositor.
- Timings follow the code where the review asked: W1 0-240 ms, W2 240-600, W3a 600-1000, W3b 1000-1250.

---

## 2. What the Help does in the engine (unchanged from round 1)

Source: `slot_engine/core/state_machine.py`, `slot_engine/core/creature.py`, `slot_engine/core/progression.py`,
`slot_engine/static/canvas/index.html` (`strikeSeq`).

It fires when a tumble stalls with no win, `pending_lifeline` is set and the depth level is above 0. The flag is armed
by a level-up, by the pearl ascension and at the start of an xBet round, and one strike consumes it. The cascade is
evaluated again afterwards; a win is likely, not guaranteed.

| Level | Footprint | Effect |
| --- | --- | --- |
| 1 Lurker | 1x1, random cell | Cell becomes `WILD_MAW`; each orthogonal neighbour that is a LOW becomes helmet or compass. |
| 2 Stalker | 2 rows x 1 column | Both cells wild; adjacent mids become highs. |
| 3 Maelstrom | 2x2 | Wild multipliers x2 / x3 / x5. |
| 4 Tentacles | 3x3 | Wilds and highs. |
| 5 Awakened | 2x2 | Sticky roaming wild block, x2. |

The storyboard shows level 1 at cell (row 1, col 3, zero-based). The board in H0 is dead (reels 1 and 2 share only the
helmet and reel 3 has none). After the strike a helmet way exists on reels 1-4.

`strikeSeq` today: 1.5-2.4 s hush, then the lunge, the chomp with hit-stop, the creature dives away (about 1.1 s), and
only then do the wild and the neighbours surface, followed by a 1.1 s hold: about 4.9 s after the hush. The storyboard
is the reviewer's full version (about 3.1 s) with the transformation on the hit-stop release and the recede underneath
it. That is an engine change (review item 13), not something the code does yet. H2 has no counterpart in code.

---

## 3. Frame by frame

**Master.** A bolted viewport sunk in a trench. The reels are behind its glass; the light comes from behind them,
upper centre-left. The creature is the dark ribbed body and plated head sliding down the left third. On the right the
sonar sweeps, the switches wait, the wheel is the largest brass object. Idle motion: snow, sonar sweep, gauge level,
the body easing past.

**H0 dead spin, 0 ms.** Same board, 20% darker, nothing lit. Stillness and the sound dropping carry it.

**H1 dread, 0-900 ms.** Being watched. Every symbol's own light goes out and the eye fills the upper-left nine cells
behind the glass, slit in the reel gap. Moves: lid opening, the iris brightening, the sonar blip jumping.

**H2 targeting, 900-1500 ms.** It has chosen. The pupil snaps right, all cells dim except one, water churns on that
cell and the glass bulges toward you over it. The player can point at the cell that is about to be hit.

**H3 impact, 1500 ms.** The ring of fangs is through the glass on that cell, lure lit in the throat, its body visible
behind the reels running back to the upper left. The cell's symbol is gone, the four neighbours are knocked 20 px
outward, water bursts in around the ring and one jet is already falling. Hit-stop frame, 9 px shake.

**H4 transformation, 1580-2300 ms.** The mouth stays: a Wild Maw the size of the ring, the hottest thing on screen.
Wild first, then the four neighbours 60 ms apart turn to brass. Wet cracks join the five cells; the creature's maw is
a dim shape sinking below.

**H5 aftermath, 2300-3100 ms.** The Wild settles to one cell. Water runs down the glass over the rows below and beads
on the sill. The body in the left third has dropped lower, leaving.

**W1, 0-240 ms.** A dark line runs along the joints and puts a spur into each of the four anglers; they brighten and
their lures light. Beads of water form on the line.

**W2, 240-600 ms.** The seam opens 3 px. Water is forced through at each spur toward the viewer and falls; what is
behind it bends.

**W3a, 600-1000 ms.** The winners hold, whole and bright. 4.20 lights on the WIN plate. Sheets of water run to the sill.

**W3b, 1000-1250 ms.** They are crushed in reel order with a few inward flecks; the cells behind go dark; the seam is
a wet, dripping line.

---

## 4. How it was made

52 Z-Image-Turbo paints in total (36 in round 1, 16 in round 2), 3 Real-ESRGAN upscales, BiRefNet only in round 1.
No studio, game or artist is named in any prompt. Prompts and seeds: section 6.

- **Frame parts** are painted on flat green (the sonar on magenta) and keyed in `frame.py` by hue: a pixel is
  background if its chroma points the same way as the border's chroma (cosine above 0.86) and is at least 30% as
  strong. Greys never match, and the cast shadow the model paints on the background does, so it is removed too.
- **Lettering** (plates, gauge marks, switch labels) is drawn by `frame.py` as engraved or stencilled text, so values
  and language can change without repainting.
- **Dynamic instrument parts** are drawn by `stage.py` from `frame_meta_*.json`: gauge level, sonar sweep and blip,
  ritual bar fill, lit seals, win value.
- **Creature**: `lev_eye.png` and `lev_lunge.png` from `slot_engine/static/canvas/assets/hero/`, read only, composited
  with their own alpha.
- **Water sprites**: `r2_fx_splash`, `r2_fx_jet_arc`, `r2_fx_churn`, `r2_fx_runoff` (round 2) and `fx_drain_a`,
  `fx_cracks_a` (round 1).
- **Stage order**: backdrop, key glow, world creature, snow, frame shadow, reel backplane, behind-reel creature
  (clipped to the opening), backplane FX, symbols, glass sheen, FX over the symbols, frame with instruments, FX in
  front, vignette, post highlights, shake, grain.

---

## 5. What these targets still do not nail

1. **W2 is now the quietest of the four win panels.** The bursts were pulled back so the winners stay readable, and
   the result reads as "wet" more than "pressurised". The sound's loudest stem needs a home; today W3a (the hold with
   run-off) is the stronger picture.
2. **The seam is a straight thin line.** It reads as a crack in glass up close, but at sheet size it can read as a UI
   rule, especially the right-angle step around the viper. It needs chipped edges and a second, fainter fracture.
3. **The splash and jet sprites are fountains seen from the side**, not cones seen head-on. "Toward the viewer" is
   carried by placement and refraction, not by the drawing. The splash sprite also contains a few small ring-shaped
   droplets that can be taken for bubbles.
4. **Refraction is strong in stills and untested in motion.** Under the run-off, glyphs smear; it may need less
   strength when animated.
5. **The pupil snap in H2 is a 34 px slide of the iris disc.** It is visible when H1 and H2 are flipped, hard to see in
   a single still. The churn sprite also hides the strike cell's own symbol.
6. **H3's creature is partly hidden by design.** Only the maw is in front of the symbols; the body is behind them at
   60%, so the mass reads less than in round 1's (wrong) painting. The neighbour cells are partly covered by spray.
7. **`lev_lunge` is used four ways** (idle body, H3 maw, H4 recede, H5 leaving). It is the right animal, but its
   cut-off tendrils and the hard right edge of its canvas show if it is moved much. The idle body is a rotated crop,
   not a pose painted for that place.
8. **The frame is assembled, and it shows in places.** The sill texture is mirror-tiled (a symmetric pattern is visible
   left and right of the seals), the corner plates are four copies of one plate, and both pillars come from one
   painting. The ritual bar is the depth-gauge painting turned sideways. The seals carry near-identical runes.
9. **Instruments are dim.** The right-hand column is deliberately the darkest part of the screen; the switch labels
   and the zone plate are hard to read at 1080p and will not read on a phone in landscape.
10. **No bet steppers.** BET is a plate with a value; plus and minus are not designed. Autoplay, turbo, xBet and bonus
    buy exist only as four identical switches with small labels.
11. **Portrait is a first pass.** The world band above the frame works, but the console repeats the landscape parts
    without a real layout pass, and the gauge is squeezed into a 96 px pillar.
12. **Tier ladder is not measured to the reviewer's targets.** Blurred peaks on the master: lows 52-103 (the top row
    sits in the key light), helmets 61-96, highs 87-113, Leviathan 107. Lows near the key are as bright as mids two
    rows down. The symbol files are graded by the symbols agent; the stage only applies a small per-tier multiplier.
13. **Backdrop is still the round-1 paint**: hard-edged and graphic next to the frame and symbols, and stretched 2.5x
    in portrait.
14. **The Wild in H4 is very saturated.** It is the brightest thing as asked, but close to neon against the rest.
15. **Only the cyan depth tier is painted.** No sulfur or blood grades of either moment.
16. **Stills only.** Timing, easing, hit-stop and the order of the five cells in H4 are in captions, not shown.

---

## 6. Prompts, seeds, sizes

Round 3 added 11 paints (`r3_*`): three corner plates, a pillar, a blank seal, and six that are not used (a girder, two cones, three crush frames). 63 paints in total.


Round-1 suffix, appended only where the table says so:

> Dark painterly digital concept art, gritty horror-industrial mood, desaturated, visible brushwork, film grain, cold cyan bioluminescent light, near-black teal shadows, premium game key art.

| Image (`generated/targets/moments/<name>.png`) | Seed | Size | Suffix | Used in round 2 |
| --- | --- | --- | --- | --- |
| `backdrop_a` | 11 | 1344x768 | yes | backdrop layer |
| `backdrop_b` | 23 | 1344x768 | yes | no |
| `frame_green_a` | 5 | 1152x896 | yes | no |
| `frame_mag_a` | 6 | 1152x896 | yes | no |
| `creature_sil_a` | 31 | 1344x768 | yes | no |
| `frame_green_b` | 41 | 1152x896 | yes | no |
| `frame_green_c` | 42 | 1152x896 | yes | no |
| `frame_green_d` | 43 | 1024x1024 | yes | no |
| `creature_sil_b` | 52 | 1344x768 | yes | no |
| `creature_sil_c` | 53 | 1344x768 | yes | no |
| `creature_eye_a` | 61 | 1344x768 | yes | no |
| `sym_lows` | 71 | 1344x768 | yes | no |
| `sym_helmet` | 72 | 768x768 | yes | no |
| `sym_compass` | 73 | 768x768 | yes | no |
| `sym_angler` | 74 | 768x768 | yes | no |
| `sym_squid` | 75 | 768x768 | yes | no |
| `sym_viper` | 76 | 768x768 | yes | no |
| `sym_leviathan` | 77 | 768x768 | yes | no |
| `sym_wild` | 78 | 768x768 | yes | no |
| `sym_scatter` | 79 | 768x768 | yes | no |
| `fx_breach_jaws_a` | 81 | 1024x1024 | yes | no |
| `fx_breach_jaws_b` | 82 | 1024x1024 | yes | no |
| `fx_burst_a` | 83 | 1024x1024 | yes | no |
| `fx_jets_a` | 84 | 1344x768 | yes | no |
| `fx_jet_single` | 85 | 768x768 | yes | no |
| `fx_drain_a` | 86 | 1024x1024 | yes | H5, W2-W3b run-off |
| `fx_cracks_a` | 87 | 1024x1024 | yes | H3 glass cracks |
| `fx_implode_a` | 88 | 768x768 | yes | no |
| `creature_sil_d` | 54 | 1344x768 | yes | no |
| `sym_low_10` | 91 | 768x768 | yes | no |
| `sym_low_j` | 92 | 768x768 | yes | no |
| `sym_low_q` | 93 | 768x768 | yes | no |
| `sym_low_k` | 94 | 768x768 | yes | no |
| `sym_low_a` | 95 | 768x768 | yes | no |
| `shadow_serpent_a` | 101 | 1344x768 | no | no |
| `shadow_serpent_b` | 102 | 1344x768 | no | no |
| `r2_girder_a` | 201 | 1344x768 | no | no |
| `r2_girder_b` | 202 | 1344x768 | no | frame lintel, sill, outriggers (x4 upscaled) |
| `r2_pillar_a` | 203 | 768x1344 | no | no |
| `r2_pillar_b` | 204 | 768x1344 | no | frame pillars, rail (x4 upscaled) |
| `r2_corner` | 205 | 768x768 | no | frame corner plates (x4 upscaled) |
| `r2_basalt` | 206 | 1344x768 | no | frame basalt backing |
| `r2_gauge` | 207 | 768x1344 | no | depth gauge, ritual bar |
| `r2_sonar` | 208 | 1024x1024 | no | sonar scope |
| `r2_valve` | 209 | 1024x1024 | no | spin wheel |
| `r2_seals` | 210 | 1344x768 | no | rune seals |
| `r2_plate` | 211 | 1344x768 | no | balance / bet / win / zone plates |
| `r2_switches` | 212 | 768x1024 | no | switch panel |
| `r2_fx_splash` | 221 | 1024x1024 | no | H3, H4, W2 bursts |
| `r2_fx_jet_arc` | 222 | 1024x1024 | no | H3, H4, W2 falling jets |
| `r2_fx_churn` | 223 | 768x768 | no | H2 churn |
| `r2_fx_runoff` | 224 | 1024x1024 | no | H5, W2-W3b run-off |

Prompts as sent (before any suffix):

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

**`r2_girder_a`** (seed 201, 1344x768)

> A single long straight horizontal heavy steel girder beam spanning the full width of the picture from the left edge to the right edge. Blackened corroded steel plate, one neat row of large dome rivets along its top edge and one along its bottom edge, a few vertical weld seams dividing it into plates, thin rust streaks bleeding down from some rivets, wet sheen. Plain clean surface: no brass, no ornaments, no symbols, no text, no debris. The beam is a thick straight band across the middle of the picture; above and below it is flat solid pure bright green. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_girder_b`** (seed 202, 1344x768)

> A single long straight horizontal heavy steel girder beam spanning the full width of the picture from the left edge to the right edge. Blackened corroded steel plate, one neat row of large dome rivets along its top edge and one along its bottom edge, a few vertical weld seams dividing it into plates, thin rust streaks bleeding down from some rivets, wet sheen. Plain clean surface: no brass, no ornaments, no symbols, no text, no debris. The beam is a thick straight band across the middle of the picture; above and below it is flat solid pure bright green. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_pillar_a`** (seed 203, 768x1344)

> A single long straight vertical heavy steel girder beam spanning the full height of the picture from the top edge to the bottom edge. Blackened corroded steel plate, one neat row of large dome rivets along its left edge and one along its right edge, a few horizontal weld seams dividing it into plates, thin rust streaks bleeding down from some rivets, wet sheen. Plain clean surface: no brass, no ornaments, no symbols, no text, no debris. The beam is a thick straight band across the middle of the picture; left and right of it is flat solid pure bright green. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_pillar_b`** (seed 204, 768x1344)

> A single long straight vertical heavy steel girder beam spanning the full height of the picture from the top edge to the bottom edge. Blackened corroded steel plate, one neat row of large dome rivets along its left edge and one along its right edge, a few horizontal weld seams dividing it into plates, thin rust streaks bleeding down from some rivets, wet sheen. Plain clean surface: no brass, no ornaments, no symbols, no text, no debris. The beam is a thick straight band across the middle of the picture; left and right of it is flat solid pure bright green. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_corner`** (seed 205, 768x768)

> A single square heavy blackened steel corner gusset plate, thick, with chamfered corners, a border row of large dome rivets all around its edge, one diagonal weld seam, rust streaks, wet sheen. Plain: no brass, no symbols, no text. Centred, filling most of the picture. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_basalt`** (seed 206, 1344x768)

> Full-frame texture of a wall of rough black basalt rock blocks with columnar joints and chipped edges, wet, very dark grey-black, subtle cold highlights from the upper left, no objects, no background, edge to edge stone. Realistic gritty oil painting, muted.

**`r2_gauge`** (seed 207, 768x1344)

> A tall narrow vertical brass depth gauge instrument: a long glass tube set in a tarnished brass housing with rounded brass end caps, and beside the tube a long flat brass scale strip with many small engraved tick marks and no numbers. Verdigris in the crevices. Centred, spanning most of the picture height. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_sonar`** (seed 208, 1024x1024)

> A round sonar scope instrument: a thick dark steel bezel ring with eight bolts and a thin tarnished brass inner ring, a domed dark glass screen showing faint cyan concentric range rings, a crosshair, a soft cyan sweep wedge and one small bright blip. It is mounted on a short heavy riveted black steel bracket arm that enters from the left side. Front-on flat orthographic view. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours. Isolated game asset on a flat solid pure magenta background.

**`r2_valve`** (seed 209, 1024x1024)

> A large industrial valve handwheel seen exactly from the front: a thick round rim with five straight spokes and a hexagonal hub nut in the centre, worn tarnished brass rim, dark steel spokes, grime and verdigris. Centred, filling most of the picture. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_seals`** (seed 210, 1344x768)

> Five separate round carved stone seals in one horizontal row, evenly spaced, same size: each is a dark basalt disc set in a thin dark iron ring, with a different simple angular rune carved deep into its centre. No glow, no colour.  Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_plate`** (seed 211, 1344x768)

> One blank rectangular tarnished brass nameplate, wide and low, with a small slotted screw in each corner, slightly dented and scratched, verdigris at the edges, completely blank: no text, no engraving, no pattern. Centred. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_switches`** (seed 212, 768x1024)

> A small tall dark steel control panel with four heavy tarnished brass toggle switches in one vertical column, each with a small blank brass label plate to its right, a bolt in each corner of the panel. No text. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r2_fx_splash`** (seed 221, 1024x1024)

> A burst of pressurised seawater spraying straight toward the camera out of a small hole, seen head-on: a dense white foamy core, a foreshortened cone of spray, elongated droplets flying outward and getting larger and blurrier toward the edges of the picture, fine mist. Water only: no bubbles, no rings, no circles. Lit from the upper left by a cold white light, the water itself is dark and translucent with white foam and highlights. Isolated on a pure flat black background, nothing else. Realistic oil painting, high contrast.

**`r2_fx_jet_arc`** (seed 222, 1024x1024)

> A thin pressurised jet of seawater shooting out toward the viewer and slightly downward, then losing force and arcing down under gravity, breaking up into droplets and a falling ragged curtain of spray at the bottom. Water only: no bubbles, no rings, no circles. Lit from the upper left by a cold white light, the water itself is dark and translucent with white foam and highlights. Isolated on a pure flat black background, nothing else. Realistic oil painting, high contrast.

**`r2_fx_churn`** (seed 223, 768x768)

> Top-down view of a small violent round whirlpool of churning seawater: spiral streaks of white foam, dark teal water, spray thrown off the edge. Water only: no bubbles, no rings, no circles. Lit from the upper left by a cold white light, the water itself is dark and translucent with white foam and highlights. Isolated on a pure flat black background, nothing else. Realistic oil painting, high contrast.

**`r2_fx_runoff`** (seed 224, 1024x1024)

> Seawater running down a vertical pane of dark glass: several thin wavering rivulets from top to bottom, clinging beads and droplets, a few drips falling off the bottom. Sparse, mostly empty. Water only: no bubbles, no rings, no circles. Lit from the upper left by a cold white light, the water itself is dark and translucent with white foam and highlights. Isolated on a pure flat black background, nothing else. Realistic oil painting, high contrast.


Round-3 prompts as sent (no suffix):

**`r3_corner_b`** (seed 301, 768x768)

> A single square heavy blackened steel corner gusset plate, thick, with chamfered corners, a border row of large dome rivets all around its edge, one diagonal weld seam, rust streaks, wet sheen. Plain: no brass, no symbols, no text. Centred, filling most of the picture. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r3_corner_c`** (seed 302, 768x768)

> A single square heavy blackened steel corner gusset plate, thick, with chamfered corners, a border row of large dome rivets all around its edge, one diagonal weld seam, rust streaks, wet sheen. Plain: no brass, no symbols, no text. Centred, filling most of the picture. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r3_corner_d`** (seed 303, 768x768)

> A single square heavy blackened steel corner gusset plate, thick, with chamfered corners, a border row of large dome rivets all around its edge, one diagonal weld seam, rust streaks, wet sheen. Plain: no brass, no symbols, no text. Centred, filling most of the picture. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r3_pillar_c`** (seed 304, 768x1344)

> A single long straight vertical heavy steel girder beam spanning the full height of the picture from the top edge to the bottom edge. Blackened corroded steel plate, one neat row of large dome rivets along its left edge and one along its right edge, a few horizontal weld seams dividing it into plates, thin rust streaks bleeding down from some rivets, wet sheen. Plain clean surface: no brass, no ornaments, no symbols, no text, no debris. The beam is a thick straight band across the middle of the picture; left and right of it is flat solid pure bright green. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r3_girder_c`** (seed 305, 1344x768)

> A single long straight horizontal heavy steel girder beam spanning the full width of the picture from the left edge to the right edge. Blackened corroded steel plate, one neat row of large dome rivets along its top edge and one along its bottom edge, a few vertical weld seams dividing it into plates, thin rust streaks bleeding down from some rivets, wet sheen. Plain clean surface: no brass, no ornaments, no symbols, no text, no debris. The beam is a thick straight band across the middle of the picture; above and below it is flat solid pure bright green. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r3_seal_blank`** (seed 306, 768x768)

> A single round dark basalt stone disc set in a thin dark iron ring, with a perfectly blank, smooth, slightly worn flat face: no carving, no symbols, no letters, no marks, no pattern. Centred, filling most of the picture. Front-on flat orthographic view, no perspective. Lit by one cold light from the upper left. Realistic gritty oil painting, muted dark colours, fine brushwork. Isolated game asset on a flat solid pure bright green background.

**`r3_fx_cone_a`** (seed 311, 1024x1024)

> Seen exactly head-on from the front: a hard narrow high-pressure jet of seawater firing straight at the camera through a tiny hole in a pane of glass. A small dense bright white core in the exact centre of the picture, sharp straight spray streaks radiating outward from it in all directions like spokes, a thin circular ring of fine spray around the core where the jet tears through the glass, and fine mist. Symmetric radial composition. No fountain, no falling water, no bubbles, no round droplets. Water only. Lit from the upper left by a cold white light. Isolated on a pure flat black background, nothing else. Realistic oil painting, high contrast.

**`r3_fx_cone_b`** (seed 312, 1024x1024)

> Seen exactly head-on from the front: a hard narrow high-pressure jet of seawater firing straight at the camera through a tiny hole in a pane of glass. A small dense bright white core in the exact centre of the picture, sharp straight spray streaks radiating outward from it in all directions like spokes, a thin circular ring of fine spray around the core where the jet tears through the glass, and fine mist. Symmetric radial composition. No fountain, no falling water, no bubbles, no round droplets. Water only. Lit from the upper left by a cold white light. Isolated on a pure flat black background, nothing else. Realistic oil painting, high contrast.

**`r3_crush_1`** (seed 321, 768x768)

> A deep-sea anglerfish with warty brown-violet skin, a wide jaw of long pale needle teeth and a thin lure stalk, being crushed by enormous water pressure, its body just beginning to buckle: squeezed narrower from both sides, deep creases forming along its flanks, jaw forced half shut. Single object centred, isolated on a pure flat black background, lit by one cold light from the upper left. Realistic gritty oil painting, muted colours, game symbol icon.

**`r3_crush_2`** (seed 322, 768x768)

> A deep-sea anglerfish with warty brown-violet skin, a wide jaw of long pale needle teeth and a thin lure stalk, being crushed by enormous water pressure, its body collapsed to half its size like a crumpled tin can: deep folds, fins bent, jaw twisted shut, lure stalk snapped. Single object centred, isolated on a pure flat black background, lit by one cold light from the upper left. Realistic gritty oil painting, muted colours, game symbol icon.

**`r3_crush_3`** (seed 323, 768x768)

> A deep-sea anglerfish with warty brown-violet skin, a wide jaw of long pale needle teeth and a thin lure stalk, being crushed by enormous water pressure, reduced to a small tight crumpled knot of folded flesh, teeth and fins, like a crushed ball, with a thin ring of dark silt around it. Single object centred, isolated on a pure flat black background, lit by one cold light from the upper left. Realistic gritty oil painting, muted colours, game symbol icon.
