# Target review, round 1

Reviewer: independent art director, did not make any of this. Date 2026-11-14.
Reviewed against `docs/art_bible.md` (gates G1-G6) and `docs/graphics_fix_plan.md`, with the current build
(`artifacts/canvas/portrait_1920x1080.png`) as the baseline. All crops, my own 64 px downscales, 8 px blurs and
magenta/white halo sheets are in `generated/tmp/review/` (script: `generated/tmp/review/mk.py`).
Sound was reviewed as a design on paper and meters only. Nobody, including me, has heard it.

## Verdicts

| Deliverable | Verdict | One line |
| --- | --- | --- |
| Symbol set (`symbols_target.png`, 12 cut-outs) | **FAIL, close** | 8 of 12 are ship-quality targets; G2, G3 and G6 sit at 3 because the top of the ladder (mid / high / apex / wild) is flat and the Leviathan is the wrong animal. |
| Master key frame (`keyframe_master.png`) | **FAIL** | Right direction, wrong execution: it was built with a second, weaker symbol set whose lows cannot be read, the helmets are the brightest thing on screen, and the HUD is still four lines of text. |
| Help storyboard (`storyboard_help.png`) | **FAIL** | H3 and H4 land. H2 does not read, the creature is four different animals, none of them the one already in the game. |
| Win storyboard (`storyboard_win.png`) | **FAIL** | The seam is lightning in W1 and W3 and half-lightning in W2. The winners are not the angler from the symbol sheet. |
| Sound design (paper only) | **Structure sound, three risks** | The loudest moment is on the impact with a real dip before it. The apex and wild voices do not exist on a phone speaker, the win's weight sits on the weakest picture, and the transformation's mood contradicts the picture's. |

Every deliverable is a large step up from the baseline. None is yet a target I would let the engine team build to.

## The finding that cuts across everything

**There are two symbol sets and the wrong one is in every moment frame.** The symbol maker's 12 cut-outs
(`generated/targets/symbols/`) are good. The moments maker painted a separate set (`sym_*`, seeds 72-95, in
`generated/targets/moments/cut/`) and used it in the master, H0-H5 and W1-W3: unlit slabs, a different helmet with a
glowing faceplate, a pocket-compass with a ship's wheel, a red squid, a black snake, a bone-skull fish as "Leviathan",
and a piranha with no lure as "angler". So the master does not show the chosen symbols at all, and both storyboards
are scored on symbols nobody intends to ship. Rebuild all ten stage frames from the symbol-sheet cut-outs before
anything else is judged again. This is a composite job (`stage.py` reads a different folder), not a repaint.

## Score tables

PASS needs 4 or more on every applicable line.

### Symbol set

| Gate | Score | Evidence |
| --- | --- | --- |
| G1 readable at 64 px | 4 | My own row (`row64_x3.png`): all 12 identifiable. Weakest: J (thin stroke, dimmest glyph, p95 luminance 96 against 128 for the 10), squid (covers 22% of its box), compass (could be a porthole). |
| G2 tier hierarchy | 3 | Lows recede properly (blurred cell mean 25-29). Above them the ladder is flat: helmet 33, compass 37, angler 39, squid 41.5, wild 41.7, viper 42.5, leviathan 42.7. Peak after blur: squid 135, viper 108, helmet 105, leviathan 105, angler 99, **wild 94**. A mid ties the apex and the wild has the lowest peak of the top five. |
| G3 one light | 3 | Direction is consistent (upper-left half brighter than lower-right on all 12, ratio 1.10-1.79). But 7 of 12 carry their own light (five lit grooves, red-eyed leviathan, red maw), and the helmet has a warm frontal light with no cool rim, which the bible asks for on mids. |
| G4 integrated HUD | n/a | |
| G5 cohesion | 4 | One brush, one grain, no frames, no text. The squid is a natural-history plate among horror paintings; the helmet is cleaner than its neighbours. |
| G6 reference parity | 3 | Lows, viper, angler and maw would survive next to a premium dark slot. The horned red-eyed demon head and the top-down compass bowl would be picked out. |

### Master key frame

| Gate | Score | Evidence |
| --- | --- | --- |
| G1 readable at 64 px | 2 | At cell = 64 px (`master_cell64_x2.png`) the glyphs in rows 3-5 are dark-on-dark: bottom-row cell luminance 16-21, barely above the backplane. The red squid and the piranha disappear into the water. |
| G2 tier hierarchy | 2 | Under an 8 px blur (`master_blur8.png`) what survives is two helmets, the compass and the creature's glow. Every high recedes. The order is inverted. |
| G3 one light | 3 | Key at upper centre-left with falloff is there and works on the frame. Helmet faceplates and the bone fish's eye are their own cyan lamps; the pale creature smear behind rows 1-2 lowers tile contrast exactly where the light should help. |
| G4 integrated HUD | 2 | The depth gauge in the left pillar is the one integrated element. Title, zone, balance and bet are plain text in the four corners. No sonar, ritual bar, seals, spin, bet controls, win meter. |
| G5 cohesion | 3 | Frame reads as a 3D render with generator debris, backdrop is hard-edged and graphic, symbols are soft paint. Grain and vignette hide it at a glance only. |
| G6 reference parity | 2 | A stranger picks ours on two counts: you cannot read what is on the reels, and two thirds of the screen has nothing to do. |

### Help storyboard

| Gate | Score | Evidence |
| --- | --- | --- |
| G1 readable at 64 px | 2 | Inherits the unreadable lows. The five upgraded cells in H4 do read at phone size; the eye in H1 becomes a cyan cloud; H2's shadow becomes a smudge. |
| G2 tier hierarchy | 3 | H4 separates the five struck cells from the twenty dimmed ones very well. Inside the five, the Wild Maw is the darkest and the gold helmets the brightest: the reward's centre is its weakest element. |
| G3 one light | 3 | H1 is the best lighting in the whole pack (tiles as black shapes on the iris). H3 is lit evenly from the front; H4's halos are ambient glow with no direction. |
| G4 integrated HUD | 2 | Same corner text in all six. |
| G5 cohesion | 2 | Four creature paintings that disagree with each other and with `lev_eye` / `lev_rise` / `lev_maw` / `lev_lunge` (see `creature_compare.png`). |
| G6 reference parity | 3 | H3 and H4 have premium weight. H2 is a placeholder. |

### Win storyboard

| Gate | Score | Evidence |
| --- | --- | --- |
| G1 readable at 64 px | 2 | Winners are the lure-less piranha, not the angler. In W3 they are crushed to a third of a cell exactly when "+4.20" appears, so the player cannot see what paid. |
| G2 tier hierarchy | 3 | Winners pop and the rest dim in W1 and W2. In W3 the scar is brighter than everything, symbols included. |
| G3 one light | 3 | The seam is uniformly self-luminous cyan; nothing on it is lit from the key. |
| G4 integrated HUD | 2 | Win amount is floating Bahnschrift text. |
| G5 cohesion | 3 | A 2 px procedural polyline with glow on top of oil paint. The painted jet sprites are the only part that belongs. |
| G6 reference parity | 2 | Glowing zigzag with forks is the stock "electric win line". It is the cheap tell this game is trying to lose. |

## What I checked on the makers' claims

- **"Cut-outs are clean" (symbols): true.** On magenta and white at 100% (`edges_magenta_100.png`, `halo_white.png`)
  there is no grey rim and no fringe; semi-transparent pixels are 2-7% of each matte (squid 13%, all on thin arms).
- **"All five letterforms correct": true.** 10, J, Q, K, A are all proper glyphs. The 1 of the 10 has a slightly
  deformed top flag; acceptable.
- **Symbol G2 self-score of 4: too generous.** The measured ladder above the lows is flat. I score 3.
- **Symbol G3 self-score of 3: agreed**, for a different reason. Direction is fine; the count of self-lit symbols is the issue.
- **"Frame opening fully transparent, keyed clean" (moments): true.** Zero green-spill pixels on the metal, exactly two
  transparent regions (outside and opening), 2.6% semi-transparent edge.
- **"Phone readability was not tested" (moments): tested here, it fails.**
- **"About 2.4 s" on the help sheet header** contradicts the code (4.9 s after a 1.5-2.4 s hush). The sheet should say so.

## Is `frame_cut.png` a usable, game-ready frame?

No. It is a clean matte of a painting that is not production art.

- 1024 px source scaled 1.14x to fill 1080p. It is already soft; it cannot serve a retina phone or a 1440p desktop.
- Generator debris is baked into the steel: black-and-white squiggles on the right pillar and both top lintel
  sections that read as stray glyphs or eyeballs (`frame_zoom.png`), and white specks. These will be noticed on a
  static element the player stares at for an hour.
- Nine identical brass bosses are the brightest things on the frame and do nothing. They pull the eye off the reels.
- The inner edge of the opening wobbles and the opening is 611 x 642, not matched to a 5x5 cell grid.
- One piece. Portrait needs the pillars and lintels to re-flow, so it must be corners + pillars + lintels (or 9-slice).
- The gauge is the right idea and should be kept: brass tube in the left pillar. It needs numerals and zone marks.

Keep the design language (bolted black steel, rust bleeds at joints, brass instruments let into it). Repaint it.

## Answers to the six questions

### 1. Low runes: lit groove or unlit slab?

Neither as shown. **Use the direction-A tablets from the symbol sheet, with the groove dimmed at rest and lit on win.**

- The master's unlit slabs are disqualified by measurement: they cannot be read at phone size below the top two rows.
- The sheet's fully lit grooves read perfectly, but seventeen cyan letters at full strength is a second light source
  spread over the whole grid. It fights the single key light, flattens the win state (nothing left to turn on), and
  breaks the bible's "glow only on win".
- Target: at rest the groove floor sits at roughly 35-40% of its painted emission and is desaturated toward Mist, and
  the **pale worn rim of the cut** (already in the paint) carries the letter by catching the key light. On a win the
  groove goes to 100% plus bloom. Cells nearer the key can sit a little higher than cells in the bottom corners.
- This needs one emissive mask per glyph. It can be pulled from the existing paints by keying the cyan (hue and
  saturation threshold, small blur). No repaint.
- The slab itself is correct and should stay, despite the bible saying "transparent ground": a bare carved glyph has
  nothing to be carved into. Update the bible line rather than the art.

**Are five identical outlines a problem?** Yes. Fourteen to seventeen of the same chamfered octagon reads as a stamped
tile, which is the "framed token" look the bible set out to kill; it also throws away silhouette as a second way to
tell the letters apart. **Cheapest fix: break the matte, not the paint.** In `finalize.py`, give each of the five
glyphs its own deterministic chipped alpha (bite one or two different corners off, notch one edge, using a seeded
noise mask per glyph) so each letter owns a silhouette. Minutes of numpy, no model call. If that is not enough, the
next cheapest is one extra slab seed per glyph (five paint calls).

### 2. Symbol by symbol

| Symbol | Status | What to change |
| --- | --- | --- |
| low_10 | Ship as target | Emissive mask; own chipped outline. |
| low_j | **Repaint (or re-pick)** | Thinnest and dimmest glyph, occupies the least of its slab. Stroke width must match the K; hook wider and heavier; same groove brightness as the 10. |
| low_q | Ship | Emissive mask; outline. |
| low_k | Ship | It is from an earlier prompt pass and its groove is flatter and greyer than the others. Level it in the grade, not by repainting. |
| low_a | Ship | Emissive mask; outline. |
| mid_helmet | Ship after a composite fix | Best object painting in the set, and that is the problem. Take it down a further 15% in value, pull the warm yellow highlights toward tarnish, add a thin cool cyan rim on the upper-left dome. Remove the pale triangular flecks on the lower-right collar: at 64 px they read as a white chip. Keep the faceplate black; do not use the glowing faceplate of the moments version. |
| mid_compass | **Repaint** | A bowl seen from above with a star: at 64 px it is a porthole or a coin. Subject: a gimballed ship's compass at three-quarter view so the gimbal ring and bowl give an unmistakable silhouette, one strong steel needle crossing the face, glass with a single cool highlight upper-left. Brass at the same tarnished value as the corrected helmet. Fill 90% of the cell. |
| high_viper | Ship | Tighten the coil so the tail stays inside 112% and does not enter the cell below. Nothing else. |
| high_angler | Ship | Thicken the lure stalk to survive 64 px (about 3 px there) and put the lure's glow back as an additive sprite in the engine. Best creature in the set. |
| high_squid | **Repaint** | Wrong pose, wrong mood, wrong value: a thin diagonal, pretty iridescent pink, and the brightest symbol on the board (mean luminance 107 against the Leviathan's 68). New pose: seen from slightly below with the arms spread toward the viewer in a radial fan and the mantle foreshortened behind, so it fills the cell and breaks its edge. Bone-white only on the upper-left planes, the rest falling to bruised dark red; one large amber eye as the focal point. No rainbow sheen. It must sit below the Leviathan in peak value. |
| high_leviathan | **Repaint, priority one** | It is a horned demon with red eyes. The creature already in the game (`lev_eye.png`, `lev_lunge.png`) is a dark teal scaled serpent-fish with a cyan slit eye, pale curved fangs, dorsal spines and a lure lit in its throat. Paint that head: three-quarter view, jaws part open, cyan slit eye as the brightest point, pale fangs, a cyan glow deep in the throat, no horns, no red, no orange. Scale 120%, largest silhouette of the set. No neck stump: let the neck run off the cell edge and fade its alpha into the dark. Highest local contrast in the set. |
| wild_maw | Ship after a composite fix | Right design, and it rhymes with `lev_maw.png` (the ring of fangs), which is exactly what a wild called "Maw" should do. It is under-lit: lowest blurred peak of the top five. Raise the throat glow and the inner tooth highlights until it is the loudest thing in the grid; keep the iron ring dark. WILD lettering can wait for the engine. |

Ship as targets: 10, Q, K, A, helmet, viper, angler, maw (8, four of them after grade/matte fixes). Repaint: J, compass, squid, Leviathan (4).

### 3. Does the tier hierarchy hold?

Lows below everything else: yes, clearly. Above that: no. Mid, high, apex and wild are one tier under blur, and the
makers are right on both of their admissions. Three levers, in this order:

1. **Value, by tier, measured.** Set target blurred peaks and grade to them: lows about 70, mids about 85, highs about
   110, Leviathan about 130, Wild about 150. Today it is 56-92 / 78-105 / 99-135 / 105 / 94.
2. **Chroma as the last step of the ladder.** The bible already reserves Blood for the Wild. Nothing else on the grid
   may be red, which is another reason the Leviathan's red eyes and orange throat must go and the squid's red must drop.
   Brass is the mids' colour, so the helmet must not be brighter than a creature.
3. **Size and edge-breaking.** Leviathan at 120% and the only symbol that visibly overlaps its neighbours; highs at
   112%; mids must stay inside the cell (compass currently fills more of its box than the helmet and reads larger than
   the squid).

### 4. Master key frame

**The direction is right.** A bolted viewport sunk in a trench, reels behind its glass, the creature as the light
behind them, the gauge let into the pillar: this is the correct answer to "web UI in a void", and the side thirds are
correctly dark (mean luminance 14 against 29 for the centre). Keep all of that.

**Missing against the art bible:**

- Sonar in the top-right. Absent.
- Ritual bar and five rune seals in the bottom lintel. Absent; the sill has three small unreadable discs.
- Any integrated HUD. Balance, bet, zone and title are corner text. Spin, bet steppers, win meter, autoplay, turbo,
  xBet and bonus buy are not designed at all, and they are a third of the baseline screen. A key frame that leaves
  them out cannot be scored for G4 honestly; it will fail the moment they are added as DOM pills.
- Gauge numerals and zone bands.
- The chosen symbol set (see the cross-cutting finding).
- The creature. The pale bone skull behind rows 1-2 is not the hero Leviathan, is hidden by tiles, and washes out the
  top row. Behind the reels there should be light and a hint of scale and eye; the body belongs where it can be seen.

**What the side thirds should carry.** They must stay the darkest part of the screen and never compete with the reels,
but they need a job:

- **Left third:** the world. Trench wall in parallax and the Leviathan's body. This is where the idle creature reads:
  a coil sliding past, far larger than the frame. Low on this side, bolted to the frame's sill as an outrigger plate:
  balance and bet.
- **Right third:** the instruments. The sonar scope on a bracket arm off the top-right corner of the frame, with the
  depth zone name on its bezel (replacing the corner text). Below it, hull-mounted switches for xBet, bonus buy,
  autoplay and turbo. The spin control as a pressure wheel or valve at the bottom-right of the sill, the largest
  brass object on screen.
- **Bottom lintel, centre:** ritual bar and the five rune seals, replacing the anonymous discs. Win meter engraved in
  the sill above them.
- The nine brass bosses go, or become these things. Brass on the frame should mean "this is an instrument".
- Portrait: the same pieces re-flow (sonar and switches under the sill, world above), which is why the frame must be
  built in parts.

### 5. Help storyboard

| Frame | Reads? | Notes |
| --- | --- | --- |
| H0 dead spin | Yes, by absence | Only 17% darker than idle. Fine as a stillness beat; let motion (snow slowing) and sound carry it. |
| H1 dread | At full size, yes. Small, no | Iris and slit in the reel gap, tiles black against it: the best idea in the sequence. Faults: the eye is off-model (a bulbous fish with tubes; `lev_eye.png` is a scaled reptilian lid), the helmet faceplates keep glowing and spoil the silhouettes, and most of the pupil is behind tiles. Use `lev_eye`, put the whole slit in a reel gap, kill every symbol's own emission for this beat. |
| H2 approach | **No** | A black blob shaped like an animal's head, no rim light, no clear target, and "the frame strains" is three small lightning marks. It also has no counterpart in the code. Replace the beat, do not polish it. Its job is honest anticipation: tell the player which cell. Other cells dim, the pupil snaps to the strike cell, water churns on that one cell, the glass over it bows toward the viewer. |
| H3 impact | Yes | Real weight. Faults: the board is completely gone (no grid, frame and gauge buried in spray), the maw is a fifth creature, it is centred because the strike cell was conveniently the centre, and the chromatic split is doing the work a single hot highlight should. Use the `lev_maw` ring of fangs, sized so its ring lands on the strike cell at about 1.6 cells, and storyboard an off-centre strike to prove the composition. |
| H4 transformation | Yes, best frame | Five cells lit, twenty dimmed, spray still in the air. Faults: the Wild is the dimmest of the five; the helmets have gone coin-gold; an untouched compass sits diagonally adjacent and makes the cross look like six; all five are lit at once although the wild should lead. |
| H5 aftermath | Mostly | The water sheets running down the lower rows are the most convincing water in either storyboard. The cross-shaped scar is lightning again. |

**Escalation:** yes in light (frame mean luminance 18.5, 15.1, 15.5, **28.5**, 18.8, 18.0: a dip, a spike, a settle),
no in information. H2 is a hole between the two strongest ideas.

**The link nobody drew:** the hero maw is a ring of fangs and the Wild Maw symbol is a ring of fangs in an iron collar.
The bite should leave its mouth behind. If H3's ring and H4's wild are the same size in the same place, the
transformation needs no explanation.

**Order: transformation straight after the impact, then the recede.** The storyboard order is better for the player.
Cause and effect stay in one glance: it bit this cell, this cell is now a wild. The code's order (creature leaves,
1.1 s of nothing, then symbols surface "alone") makes the reward look like a separate event and spends the longest
part of the sequence on an empty board. Let the creature's withdrawal play underneath the reveal instead of before it.

**Length: neither.** 2.4 s is right for the action; 4.9 s plus a 1.5-2.4 s hush (up to 7.3 s before the board can be
evaluated) is too long for something armed at every level-up, at pearl ascension and at the start of every xBet round.
But a 600 ms dread is too short to feel the first time. Two versions:

- **Full, about 3.0-3.2 s**, first strike of a session and each first strike at a new depth: hush 500-600 ms, dread
  700, targeting 400, vacuum 80, impact and hit-stop, wild surfaces at about +120 ms, neighbours at +60 ms each,
  drain and recede together 900.
- **Short, about 1.6-1.8 s**, every repeat, xBet rounds and turbo: no hush, 300 ms eye and target, impact,
  transformation, 500 ms settle.

Sound already supports this: the stems are separate and the storyboard-timed render exists. Note the cost the sound
maker measured: with transformation on the impact's tail it has 5.6 dB of clearance above 1.5 kHz instead of 9.3.

### 6. Win seam: water or electricity?

**Electricity.** W1 is a thin, bright, cyan-white jagged line with tapering forks and a glowing travelling tip. That is
the exact drawing convention for lightning. W3's scar is the same line dimmer, with radiating dashes that read as
sparks. W2 is half rescued by the painted jets, but they glow as brightly as the line and hang as vertical streaks.

What makes it unmistakably water:

1. **Decide the fiction and hold it.** Bubbles appear in H3 and W3; jets and sheets of water appear in W2 and H5. Both
   cannot be true. The seam only makes sense if the viewer's side is dry and the sea is behind the glass. Then: no
   bubbles anywhere, water comes toward the camera and falls.
2. **A crack is dark.** Draw the hairline as a dark line with a thin lit lip on its upper-left edge, in straight
   segments with angular kinks. No glow, no tapering forks. It becomes bright only where water beads on it.
3. **It is a seam, so run it on seams.** Route it along the joints between cells with a short spur into each winning
   cell, instead of a zigzag through symbol centres. That also separates it from every other slot's win line.
4. **Water is lit, not luminous.** Dark translucent teal body, white foam and specular only on the side facing the
   key. Take the uniform cyan glow off entirely.
5. **Pressure and gravity.** Jets leave perpendicular to the glass, so toward the viewer: foreshortened cones and
   discs of spray, then arcs that fall. Mist hangs. Lightning does none of this.
6. **Refraction.** Symbols behind the film of water distort. The single most water-specific cue, and the engine
   already has a shockwave refraction pass.
7. **It lasts.** Lightning is over in a frame. Water runs down the glass, beads on the tiles below and pools on the
   sill for a second or two. H5's drain sheets already prove the sprite reads as water; use them in W3.
8. **The scar is a wet weld line that drips**, dim, not a glowing zigzag.

Separately, W3 shows the amount at the moment the winners are crushed to nothing. Hold the winners at full size for
the amount, then crush. And keep the code's 240 ms crack and 750 ms highlight; the sheet's 150 ms W1 is too short to
register which symbols won.

## Sound (design review only)

What serves the picture:

- **Help: the loudest moment is on the impact, with real contrast before it.** Sub peak in the impact window, 16 dB or
  more over anything before the dip, an 80 ms hole, every pre-impact stem gated shut. This is the correct shape and it
  matches the picture's luminance curve.
- **Tiers have distinct voices by material** (stone, brass, living, throat) and get lower, heavier and louder with
  value. The Wild as "the help cue in miniature" is the same rhyme the picture should make.
- Separate triggers for lead, impact, recede and per-cell turn: right, because the bite is clock-gated.

Risks, in order:

1. **Apex and Wild have no voice on a phone.** Their lands and stingers are 91-95% energy at 30-80 Hz. On the device
   most players use, the two most valuable symbols are the two quietest. They need body at 150-400 Hz and a transient.
   The help impact has the same exposure (89% sub) but at least has a click, a punch and a water layer.
2. **The win's weight is on the wrong picture.** The implosion is the loudest stem (-5.2 against the jet's -7.3 dBFS
   at step 1, -1.9 against -5.0 at step 5) and W3 is the weakest frame, a scale-down. Either the picture gets a real
   crush at W3 or the breach gets the weight.
3. **Mood mismatch at H4.** The picture's stated feeling is "relief turning into greed". The sound is deliberately
   cold, glassy and falling by semitones per cell. One of them is wrong. A falling ladder also reverses the genre's
   rising one, at the win seam too (every cascade step lower); players may hear their wins getting worse. Keep it
   cold if that is the game, but let the last cell (the Wild) land with weight so the beat resolves.
4. **Seconds of near-silence on mobile.** Hush (1.5-2.4 s, bed at -12 dB) then a dread built on 36 Hz and 147 Hz.
   Another argument for the shorter sequence, and for a dread layer above 300 Hz.
5. **The 80 ms dip is shorter than Bluetooth latency** and will be filled by the ambience bed unless the bed is
   ducked. Runtime work, already noted by the maker.
6. **Five stones at five pitches a tone apart** will not be told apart in a refill. Acceptable for filler. The real
   repetition risk is one take per land, fifteen lands per refill: variants are not built.
7. If the transformation moves onto the impact's tail (recommended), its clearance drops to 5.6 dB. It may need the
   impact's water layer ducked under it for 400 ms.

## Fix list, in priority order

| # | File | Change | Type |
| --- | --- | --- | --- |
| 1 | `generated/targets/_scripts/stage.py` (then `build_master.py`, `build_help.py`, `build_win.py`) | Load symbols from `generated/targets/symbols/` instead of `generated/targets/moments/cut/`. Rebuild master, H0-H5, W1-W3. Every frame below is re-scored only after this. | Composite |
| 2 | `generated/targets/symbols/high_leviathan.png` | Repaint as the hero creature's head: dark teal scales, cyan slit eye, pale fangs, cyan-lit throat, no horns, no red, no neck stump, 120%. Match `slot_engine/static/canvas/assets/hero/lev_eye.png` and `lev_lunge.png`. | Repaint |
| 3 | `generated/targets/symbols/low_*.png` via `generated/targets/_scripts/finalize.py` | Export an emissive mask per glyph (key the cyan). Show the lows at 35-40% groove emission at rest and 100% on win, and add both states to `symbols_target.png`. Update art bible section 4 to "carved basalt tablet". | Composite, then engine |
| 4 | `finalize.py` | Give each of the five tablets its own chipped alpha outline (seeded, deterministic). | Composite |
| 5 | `finalize.py` grade block | Grade to measured blurred peaks: lows ~70, mids ~85, highs ~110, Leviathan ~130, Wild ~150. Helmet down 15% and de-yellowed with a cool upper-left rim and the pale flecks removed; Wild throat and teeth up; level K's groove to the others. | Composite |
| 6 | `generated/targets/symbols/high_squid.png` | Repaint: arms fanned toward the viewer, fills and breaks the cell, bone-white only on upper-left planes, dark red elsewhere, amber eye, no iridescence, below the Leviathan in value. | Repaint |
| 7 | `generated/targets/symbols/mid_compass.png` | Repaint: gimballed ship's compass in three-quarter view, strong needle, tarnished brass at helmet value, 90% of the cell. | Repaint |
| 8 | `generated/targets/symbols/low_j.png` | Repaint or re-pick: stroke weight and groove brightness equal to the K and 10, wider hook. | Repaint |
| 9 | `generated/targets/moments/layers/frame_cut.png` | Repaint at 2048 px or larger, in parts (four corners, two pillars, two lintels), opening matched to the 5x5 grid, no generator debris, bosses removed. Built in: gauge with numerals and zone bands (left pillar), sonar on a bracket (top-right), ritual bar and five rune seals (bottom lintel), engraved balance / bet / win plates and a spin valve on the sill. | Repaint |
| 10 | `artifacts/targets/keyframe_master.png` (`stage.py`) | Lay out the full HUD as physical parts and give the side thirds their jobs: creature body and trench left, instruments and switches right. Remove the pale skull from behind rows 1-2; keep only light and an eye there. No corner text. Add a portrait version. | Composite, after 9 |
| 11 | `generated/targets/moments/frames/H1.png`, `H3.png` (`build_help.py`) | Use the existing hero paintings: `lev_eye.png` for H1 with the full slit in a reel gap and all symbol emission off; `lev_maw.png` for H3 with its ring sized and placed on the strike cell, struck off-centre, grid still visible at the edges, one hot highlight instead of a full-frame chromatic split. | Composite |
| 12 | `generated/targets/moments/frames/H2.png` | Replace the shadow pass with a targeting beat: other cells dim, pupil snaps to the strike cell, churn on that cell, glass bows outward. Drop the lightning-shaped stress cracks. | Composite (new FX paint for the bowed glass) |
| 13 | `generated/targets/moments/frames/H4.png`, `H5.png`; `slot_engine/static/canvas/index.html` `strikeSeq` | H4: Wild is the brightest of the five and sits exactly where H3's ring was; brass neighbours at graded value, not gold; move the stray compass off the diagonal; scar redrawn as a wet crack. Engine: transformation at the hit-stop release with the recede underneath, full version about 3.1 s and a 1.6-1.8 s short version for repeats and xBet. | Composite, then engine |
| 14 | `generated/targets/moments/frames/W1.png`-`W3.png` (`stage.seam`, `build_win.py`) | Seam as a dark hairline with a lit lip, routed on cell joints with spurs into winners; water lit by the key and not luminous; jets toward the viewer then falling; refraction over the symbols behind; no bubbles; W3 holds winners at full size for the amount, then crushes, with drain sheets and a dripping weld scar. Winners are the real angler. | Composite plus two FX repaints (cone jet, crush strip), refraction engine-side |
| 15 | `scripts/ai/assetgen/moments.py` | Give APEX and WILD lands and stingers body at 150-400 Hz and a transient so they exist on phone speakers; add a dread layer above 300 Hz; let the last transformed cell land with weight; align the win's loudest stem with whichever of W2 or W3 the picture makes strongest. Then a human listen. | Engine-side (sound) |

Items 1, 3, 4 and 5 need no model calls and should be done first; they will change the scores of the master and both
storyboards on their own. Items 2 and 9 are the two repaints that everything else depends on.
