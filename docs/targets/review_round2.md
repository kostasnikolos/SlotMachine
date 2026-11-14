# Target and slice review, round 2

Reviewer: the same independent art director as round 1. Date 2026-11-14.
Method as before: 100% crops, my own 64 px downscales and 8 px blurs, alpha and halo checks, claims checked against
pixels. Working files are in `generated/tmp/review/` with the prefix `r2_` (script `generated/tmp/review/r2.py`).
Sound is judged on the makers' tables only; I did not re-measure the audio and nobody has heard it.
Not inspected at 100%: `slice_help_short_film.png` (I used the short strip and `slice_report.json`).

## Verdicts

| Deliverable | Round 1 | Round 2 | One line |
| --- | --- | --- | --- |
| Symbol set (target) | FAIL, close | **PASS** | The ladder is now real and measured, the Leviathan is the hero's animal, the lows have a rest and a win state. Minor work listed. |
| Master key frame, landscape | FAIL | **FAIL, close** | A frame you could ship a game in. The tier ladder does not survive the key-light falloff, and the frame carries gibberish engraving, five identical seals and a HUD you cannot read. |
| Master key frame, portrait | none | **FAIL, close** | Same strengths, same faults, plus a stretched backdrop. |
| Help storyboard | FAIL | **PASS** | Every beat reads and it is one creature. H2 is the weakest panel. |
| Win storyboard | FAIL | **FAIL, close** | It is water now. The seam itself reads as a UI selection rule, and the crush is still a scale-down. |
| Game: idle screen | n/a | **FAIL** | The new symbols are in, and the game's lighting inverts them: the lows are the brightest things on the board and the creatures are nearly black. |
| Game: help sequence | n/a | **FAIL** | Timing and order are right. The impact is the darkest frame of the sequence, the reward cannot be seen, and there is no eye. |

The targets have largely arrived. The work has moved to the game.

## Score tables

PASS needs 4 or more on every applicable line.

### Symbol set (target)

| Gate | Score | Evidence |
| --- | --- | --- |
| G1 64 px | 4 | All 12 identifiable in my own row (`r2_row64_x3.png`). Rest-state lows still read; A is weakest (peak 60). Helmet is a dark shape but unmistakable. |
| G2 hierarchy | 4 | I reproduced the makers' blurred peaks exactly: lows 60-70, mids 85, highs 110, Leviathan 130, Wild 150. Caveat: the helmet's cell mean (27.8) equals a low's. |
| G3 one light | 4 | Upper-left brighter than lower-right on 11 of 12 (ratio 1.16-1.88); the Wild is radial by design. Grooves are quiet at rest. The rim is a matte-edge overlay, not relighting; the engine has to do the rest. |
| G4 | n/a | |
| G5 cohesion | 4 | One hand. The Wild's added glow is pink and airbrushed against the paint; the helmet is muddy after a 27% cut. |
| G6 parity | 4 | Nothing on the sheet would be picked out as the cheap one. The squid is the dullest high. |

### Master key frame

| Gate | Landscape | Portrait | Evidence |
| --- | --- | --- | --- |
| G1 64 px | 4 | 4 | Every glyph reads in every row at cell = 64 px (`r2_master_cell64_x2.png`). |
| G2 hierarchy | 3 | 3 | Blurred peaks on the master: top-row lows 87-105, helmets 68-98, squid 87, angler 101, Leviathan 105, viper 113. The key falloff outweighs the tier grade: a low near the light beats a helmet and ties the apex in the far corner. |
| G3 one light | 4 | 4 | One key, upper centre-left, on symbols and frame. |
| G4 integrated HUD | 4 | 4 | Nothing floats; every meter is a physical part. Usability is a separate matter, see question 4. |
| G5 cohesion | 3 | 3 | Round-1 backdrop is still hard-edged and graphic (stretched 2.5x in portrait). Four identical corner plates, both pillars from one painting, ruler engraving that is generator gibberish. |
| G6 parity | 3 | 3 | The tells: nonsense characters on the brass scales, five seals with the same rune, HUD text too dim to read. |

### Help storyboard

| Gate | Score | Evidence |
| --- | --- | --- |
| G1 | 4 | Eye, maw and the five changed cells all read at sheet size. |
| G2 | 4 | In H4 and H5 the Wild is clearly the loudest thing; the brass neighbours are second; the rest are dimmed. |
| G3 | 4 | H1 backlit from the iris, H3 one hot highlight at the upper-left of the ring. |
| G4 | 4 | Frame instruments only. |
| G5 | 4 | `lev_eye` and `lev_lunge` throughout. The H2 churn is a glassy swirl that reads as an orb, in a slightly different hand. |
| G6 | 4 | H1, H3 and H4 have the weight. H2 carries less. |

Frame luminance still has the right shape: 21.7, 14.6, 16.0, **23.4**, 18.0, 21.9.

### Win storyboard

| Gate | Score | Evidence |
| --- | --- | --- |
| G1 | 3 | W3b crushes the winners to specks; glyphs under the run-off smear. W3a (hold with 4.20 on the plate) fixes the round-1 complaint. |
| G2 | 4 | Winners are the real angler and stay the brightest things until the crush. |
| G3 | 4 | Water is lit, not luminous. One lens-flare star in W2 is out of character. |
| G4 | 4 | Win value on the WIN plate. |
| G5 | 3 | The seam is a 2 px ruled line with right angles on top of oil paint. |
| G6 | 3 | See question 5. |

### Game captures

| Gate | Idle (1920 and 390) | Help sequence | Evidence |
| --- | --- | --- | --- |
| G1 | 2 | 2 | Lows read very well on the phone capture. Angler and squid are near-black shapes on a near-black board (`r2_game_64_blur.png`). In the help, the transmuted helmets are black. |
| G2 | 1 | 2 | Inverted. Blurred peaks in the game: lows 32-82, angler 36, squid 33. Under blur only the lows and one lit compass exist. In the help the Wild does pop. |
| G3 | 2 | 2 | A warm local light at the lower right triples whatever is under it (same compass: 32 dim, 85 lit). It is not the upper-left key. |
| G4 | 1 | 1 | Old thin-line frame and web controls (expected, not in yet). The help adds two more floating boxes: an orange target rectangle and a name card. |
| G5 | 2 | 2 | Painted symbols inside neon-outlined cell boxes; dot-particle bubbles. |
| G6 | 2 | 2 | |

## Status of the 15 round-one items

| # | Item | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Stage uses the chosen symbols | **Done** | `stage.py` reads `generated/targets/symbols/`; master and all panels show the sheet's set. |
| 2 | Leviathan repaint | **Done** | Teal scaled head, cyan slit eye, pale fangs, lit throat, no horns or red, neck fades out. Matches the hero in kind. |
| 3 | Emissive mask, rest and win states | **Done in targets, partly in game** | `_emissive`, `_win`, `_full` exist and the sheet shows both states. `docs/art_bible.md` line 46 still says "transparent ground". In the game the rest groove renders brighter and more saturated than the target rest state. |
| 4 | Own outline per tablet | **Partly** | Different corners are bitten, but at grid size the five still read as one chamfered slab (`r2_low_alpha.png`), and the J is on a visibly different, narrower slab. |
| 5 | Grade to tier peaks | **Done on the sheet, not downstream** | Sheet peaks are exact. They do not hold on the master (falloff) or in the game (inverted). Helmet was cut 27%, too much. |
| 6 | Squid repaint | **Done** | Frontal fan, dark wine flesh, no iridescence. Dullest of the highs, acceptable. |
| 7 | Compass repaint | **Done** | Gimbal rings and needle give a clear silhouette. |
| 8 | J repaint | **Done** | Bold stem and hook, rest peak 68. |
| 9 | Frame repaint in parts with HUD | **Partly** | 3840 x 2160, assembled from parts, clean matte (35 stray green pixels, no magenta), gauge numerals, sonar, ritual bar, seals, plates, switches, wheel. Faults in question 4. |
| 10 | Master with HUD and side thirds, portrait | **Done** | Left: trench and the hero's body. Right: instruments. No corner text. Portrait exists. |
| 11 | H1 and H3 from the hero paintings | **Done** | `lev_eye` with the slit in a reel gap, symbol emission off; `lev_lunge` ring on an off-centre strike cell with the grid still visible. |
| 12 | H2 as a targeting beat | **Done** | Pupil shift, one cell kept lit, churn. The churn hides the cell's own symbol and reads as an orb. |
| 13 | H4, H5 and `strikeSeq` timing | **Targets done, engine partly** | Game: full 2.57 s, short 1.45 s, bite 612 / 354 ms after the lunge starts, transformation about 200 ms after the bite with the creature leaving underneath. The pictures are far from the storyboard (below). |
| 14 | Water seam | **Partly** | One fiction, dark seam, lit water, run-off, W3a hold, real angler. Seam reads as a UI rule; jets rise like fountains; refraction untested in motion; crush is a scale-down. |
| 15 | Sound | **Done on paper, one gap** | Jet is the loudest win stem at every step (-3.1 against -8.4 dBFS at step 1); cells rise and the last has weight; dread has a 294 Hz-1.2 kHz layer; three land variants each. Gap the maker states: in the 200 Hz-4 kHz band the squid and angler stingers (-17.9, -18.3) are louder than the apex stinger (-19.5). Still unheard. |

## Question 3: symbols, on the sheet and in the game

**On the target sheet** (all minor, none blocks the pass):

- **Helmet:** over-corrected. Gain 0.734 makes it muddy, and on the master its blurred peak (68-98) sits below the
  lows beside it. Bring the gain back to about 0.90-0.95 and hold it under the highs with saturation instead.
- **Wild Maw:** the added glow is pink. Pull the accent to Blood `#E0314B` and confine it to the throat and inner
  teeth so it is light from inside, not a halo.
- **Lows:** outlines still too alike; the J's slab is narrower than the other four; win peaks are uneven (133 for the
  10, 176 for the K). Level the win peaks to about 150 and give the J the same slab.
- **Squid:** dullest high (cell mean 37.5). Lift the pale planes on the upper left about 10%.
- **Angler:** stalk is still about 2 px at 64 px; the lure glow belongs to the engine.

**In the game** this is where the set breaks, and it is the engine's lighting, not the paintings:

| Measure | Target sheet | Game today (`slice_idle_1920.png`) | Change |
| --- | --- | --- | --- |
| Low tablet, share of cell | 70% | 65% tall, 52-58% wide | fine; keep |
| Creature, share of cell | 112% (Leviathan 120%) | angler 75%, squid 81% | The atlas fills highs to 98% of a tile and the game draws a tile at about 0.83 of the cell. Draw per tier on screen: low 0.70, mid 0.90, wild 1.00, high 1.12, Leviathan 1.20. |
| Creature brightness | atlas albedo mean 68-83 | 27-33 on screen (about x0.40) | Raise the lit result for mids, highs and specials by about x2.0-2.2 (a higher ambient floor is the simplest lever). |
| Low brightness | atlas albedo mean 50-56 | 30-45 on screen (x0.6-0.8), glyph near win-state cyan | Halve the rest emissive; lows should sit at or under 30. |
| Local warm light | none | one compass 32, the same compass under it 85 | Remove at idle, or cap its contribution at +15%. |
| Resulting ladder (blurred peak) | 60-70 / 85 / 110 / 130 / 150 | lows 32-82, compass 32-85, angler 36, squid 33 | Target on screen: creatures at least 1.5x the lows at rest. |

So: the low tablets are not too large, they are too bright relative to creatures that are too small and far too dark.
The helmet (visible in the help strip) is nearly black in the game for the same reason, on top of its over-cut grade.
The tier ladder does not survive the game's lighting at all. The idle capture also happens to show no helmet,
Leviathan, Wild or viper; the next capture should use a fixed board with all 12.

## Question 4: the new frame

**Is `frame_cut.png` ready to go in as the reel frame?** The reel frame itself, nearly. The HUD on it, no.

What is right: built from parts so it re-flows to portrait, opening matched to a 146 px cell grid, no debris blobs,
no functionless bosses, brass means instrument, and the sonar is the best single piece of art in the project.

What must change first:

1. **Gibberish engraving.** The ruler on the ritual bar and the gauge scale carry generator characters
   (`r2_frame_100_seals.png`). Repaint the scales blank and let `frame.py` draw real ticks and numerals.
2. **Five identical seals.** All five show the same hourglass rune. Five distinct runes, and a lit state that is
   more than the one glowing disc.
3. **Text and values are baked into the layer.** "BALANCE 1,000.00", "BET 1.00", "WIN", "TWILIGHT ZONE" and the
   switch labels are in `frame_cut.png`. The game layer must ship blank plates; text is drawn live.
4. **Ship parts, not the sheet.** 3840 x 2160 RGBA is about 33 MB on the GPU against a 15 MB total budget (G7).
   Pack the parts (girder, pillar, corner, gauge, sonar, plates) and assemble in the engine.
5. **Duplication.** Four copies of one corner plate and two of one pillar. Mirror and re-grade at minimum; a second
   corner paint is better.
6. **Outer edge.** The ragged basalt silhouette has a hard dark fringe behind the left pillar that reads as a cut-out
   shadow. Soften it into the backdrop.

**Is the built-in HUD the right design to build for real?** As a look, yes. As the actual controls, only in part.
Split it by what the thing is for:

| Element | Verdict | Why |
| --- | --- | --- |
| Depth gauge, sonar, ritual bar, seals, zone plate | **Build as painted** | Read-only instruments. This is the game's identity. |
| Balance, bet, win | **Keep the plates, change the text** | Money values must be the most legible text on screen. Dark engraving on tarnished brass is about the least. Draw live values in Bone on a dark inset inside the plate, at least 14 px tall on a 390 px wide phone. Today's plates would be about 8 px there. |
| Bet up / down | **Missing; add as conventional buttons** | There is no way to change the bet in the design. Two plain stepper buttons beside the BET plate, at least 44 px touch targets. |
| Spin | **Keep the wheel as art, add a clear control state** | A dim handwheel with a tiny "SPIN" stencil has no affordance. Give it a lit hub with a spin glyph, pressed, disabled and stop states, and make it the brightest brass on screen. |
| xBet, bonus buy | **Conventional labelled buttons** | These change what a spin costs. A toggle switch with a 3 px label hides both state and price. They need the price on the face and a confirm step. They can be styled as hull plates. |
| Autoplay, turbo | **Not painted into the frame** | Some jurisdictions prohibit them, so they must be removable by configuration. Separate sprites the engine can omit; never part of a baked panel of four. |
| Menu, paytable, sound, session clock and similar | **Stay in the DOM** | The art bible already says so (stage layer 6). The target has no place for them; reserve the top-right corner. |

## Question 5: does the win seam read as water?

**The water reads as water. The seam does not read as a seam.**

- W2 and W3a: grey-white, lit from the upper left, no glow, run-off sheeting down the glass to the sill. Nobody will
  call this electricity. Round 1's main complaint is answered.
- It reads as wet, not as pressure. The splashes at the spurs rise in soft crowns like small fountains. Pressure is
  a hard narrow cone toward the viewer, a ring of spray where it hits the glass plane, and mist. The sound now puts
  its weight on W2; the picture does not yet deserve it.
- The seam is a 2 px ruled line with right-angle corners along the cell joints. At sheet size it is a selection
  rectangle, and its detour around the viper (`r2_W1_100.png`) boxes a symbol that did not win. Following the joints
  was my suggestion; taken literally it produces a UI rule. Keep the routing idea but break the line: chipped,
  slightly wandering, one or two faint secondary fractures, never a closed corner around a non-winner.
- W3b is still a scale-down with dash marks around each speck; the dashes are the last spark-like element.

## Game against the storyboard, beat by beat

Measured frame luminance: storyboard 21.7, 14.6, 16.0, **23.4**, 18.0, 21.9; game (full) 12.7, 11.9, 9.6, **9.9**,
13.6, 12.8; game (short) 12.8, 12.5, 12.6, **9.5**, 13.8, 13.8.

| Beat | Storyboard | Game | Gap |
| --- | --- | --- | --- |
| H0 | Board 20% down | Board as idle | None that matters. |
| H1 dread | An eye opens behind the glass, tiles go black against it | The board dims slightly; a dark shape sits off to the right | **No eye.** In the full version roughly 900 ms pass with nothing to look at. |
| H2 targeting | Pupil snaps, one cell stays lit, churn | Hero creature swims in from the upper right; an orange rectangle marks the cell | It reads, as a UI box. The creature itself is good and on-model. |
| H3 impact | Ring of fangs through the glass on the cell, hot highlight, spray | The cell fills with white dots. The creature's mouth is a full cell below the struck cell. No flash, no spray, no shake visible | **The impact is the darkest frame of the sequence** in both versions. The loudest sound in the game lands on nothing. |
| H4 transformation | Wild at the bite, brass neighbours lit, others dimmed | Wild appears in an orange box; a "THE LURKER" name card covers the two cells to its left for about a second; neighbours change under dot particles | The Wild reads. **The neighbours do not**: the new helmet is nearly black, and the card sits on cells that can be part of the result. |
| H5 aftermath | Run-off to the sill, board back up | Board stays dimmed until about 1.3 s after the bite, then returns | Slow to show the player what they got. Bubbles, which the storyboard's fiction rules out. |

What matters most to a player, in order:

1. **The hit has no hit.** Put the mouth on the cell and make H3 the brightest frame.
2. **You cannot see what you were given.** Transmuted cells must be the brightest things on the board the moment they
   change, and nothing may cover them.
3. **Nothing happens during the dread.** The eye is the cheapest missing piece: the painting exists.
4. Orange UI boxes and dot bubbles.

What the game already gets right: both lengths, the order (reward straight after the bite with the creature leaving
underneath), one consistent hero creature, and a Wild that is the Leviathan's mouth.

## Fix list, in priority order

### Game (do these first)

| # | File | Exact change |
| --- | --- | --- |
| G1 | `slot_engine/static/canvas/index.html` (symbol shader) | Restore the ladder under game lighting: raise the lit result of mids, highs and specials by about x2.0-2.2 (ambient floor), halve the lows' rest emissive, and remove the warm local light at idle or cap it at +15%. Accept when blurred peaks on a capture are ordered low < mid < high < Leviathan < Wild with creatures at least 1.5x the lows. |
| G2 | `index.html` (symbol quad) and `scripts/ai/assetgen/atlas_pack.py` (`FILL`) | Draw per tier on screen: low 0.70, mid 0.90, wild 1.00, high 1.12, Leviathan 1.20 of the cell. Today highs land at 0.75-0.81. Highs need to overscan the cell, so the scale belongs on the quad, not only in the atlas tile. |
| G3 | `index.html` `strikeSeq` / `levStrike` | Impact: align the creature's mouth with the strike cell (it is one cell low), and add a one-frame flash plus a spray burst on the cell at the hit-stop so H3 is the brightest frame. Replace the white-dot fill. |
| G4 | `index.html` `strikeSeq` (name card, undim) | Move the name card off the grid (top lintel area) or drop it after the first strike of a session; undim the struck and transmuted cells at the moment they change and give them a 300 ms lift; undim the rest by about 600 ms after the bite, not 1300. |
| G5 | `index.html` `levPreStrike` | Dread: show `assets/hero/lev_eye.png` behind the reels with the symbols' emission off, lid opening over the hush; in the short version a 300 ms flash of it. |
| G6 | `index.html` (target marker, particles) | Replace the orange rectangle with a churn on the cell and a dim of the other 24; replace dot bubbles with the run-off sprite. No bubbles anywhere. |
| G7 | `scripts/canvas/slice_capture.py` | Capture idle on a fixed board that contains all 12 symbols, and a strike on a cell with four low neighbours, so the next review can judge every symbol and the full cross. |

### Targets

| # | File | Exact change |
| --- | --- | --- |
| T1 | `generated/targets/_scripts/frame.py`, `layers/parts/gauge.png`, `seal_1..5.png` | Blank the gibberish scales and draw real ticks and numerals in code; five distinct runes; export a game set with blank plates and no labels; mirror or repaint the duplicate corners and pillar; soften the outer fringe. |
| T2 | `generated/targets/_scripts/frame.py`, `stage.py`, `keyframe_master.png`, `keyframe_master_portrait.png` | HUD as the table in question 4: live Bone values on dark insets, bet steppers, lit spin hub with states, xBet and bonus buy as labelled price buttons, autoplay and turbo as separable sprites, a reserved DOM corner. Prove legibility on a 390 px wide render. |
| T3 | `generated/targets/_scripts/stage.py` | Make the ladder survive the key falloff: limit the falloff multiplier on symbols to about 0.85-1.15 so a top-row low cannot exceed a mid, and the Leviathan reads about 130 wherever it lands. |
| T4 | `generated/targets/_scripts/finalize.py` | Helmet gain back to 0.90-0.95 with saturation doing the holding; Wild accent to Blood and confined to the throat; win peaks of the lows levelled to about 150; J onto the common slab; stronger, different chips per tablet. |
| T5 | `generated/targets/_scripts/build_win.py`, `stage.seam`, frames `W1`-`W3b` | Break the seam line (chipped, wandering, secondary fractures, no closed corner around a non-winner); jets as hard cones toward the viewer with a spray ring; drop the lens-flare star and the dash marks; W3b as a real crush (painted strip), not a scale-down. |

Also outstanding, outside the 12: update `docs/art_bible.md` section 4 to "carved basalt tablet, groove dim at rest,
lit on win"; give the apex and wild stingers more level than the high stingers in the 200 Hz-4 kHz band
(`scripts/ai/assetgen/moments.py`); replace the round-1 backdrop; and a human listen.
