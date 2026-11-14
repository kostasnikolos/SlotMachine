# Slice review, round 3 (the real game)

Reviewer: the same independent art director as rounds 1 and 2. Date 2026-11-14.
Method as before: 100% crops, my own 64 px downscales and 8 px blurs, cell-by-cell luminance on the fixed board.
Working files: `generated/tmp/review/r3_*` (script `generated/tmp/review/r3.py`).

Not checked: the random idle captures (`slice_idle_1920.png`, `slice_idle_390.png`) were not opened this round; the
idle scores come from the fixed-board captures, which are the same screen with a known board. The short help film
strip was not opened; the short version is judged from its six-beat strip and `slice_report.json`. Sound was not
reviewed this round. Line numbers below are from `slot_engine/static/canvas/index.html` as it stands today.

## Verdicts

| Deliverable | Round 2 | Round 3 | One line |
| --- | --- | --- | --- |
| Game: idle, landscape | FAIL | **FAIL, close on symbols** | The symbol ladder now works and the set looks premium. What fails is everything around it: a painted steel frame between two cyan-line web panels and round web buttons. |
| Game: idle, 390 px | FAIL | **FAIL** | Symbols are the best they have been. There is no painted frame at all in portrait, so it is the old web layout with new icons. |
| Game: help sequence | FAIL | **FAIL, close** | The impact is now the brightest frame by a factor of two and the result is readable. The eye is too faint, the mouth is still one cell off, and the reward appears under the creature's body. |
| Master key frame, landscape | FAIL, close | **PASS** | Readable values, bet steppers, lit spin hub, priced xBet and bonus buy, five distinct runes, no gibberish. |
| Master key frame, portrait | FAIL, close | **PASS, with one note** | Same. The backdrop is still the stretched round-1 paint. |
| Win storyboard | FAIL, close | **FAIL, close** | The seam is right now and the crush is a crush. The W2 bursts have gone white and star-shaped: they read as glass shattering or a flash, not water. |

## Score table

PASS needs 4 or more on every applicable line.

| Gate | Game idle, landscape | Game idle, 390 px | Game help |
| --- | --- | --- | --- |
| G1 readable at 64 px | 4 | 4 | 4 |
| G2 tier hierarchy | 4 | 4 | 3 |
| G3 one light | 3 | 3 | 3 |
| G4 integrated HUD | 2 | 1 | 2 |
| G5 cohesion | 2 | 2 | 3 |
| G6 reference parity | 2 | 2 | 3 |

Evidence:

- **G1 (idle):** all twelve identify in my 64 px downscale of both captures (`r3_set1920_64_blur.png`). Chipped
  tablets now have five different silhouettes.
- **G2 (idle):** blurred peaks on the fixed board, landscape: lows mostly 45-72, compass 76-96, helmet 106-118,
  angler 140, viper 149, squid 158, Leviathan 181, Wild 210. Cell means: lows 15-30, mids 23-35, highs 45-55,
  Leviathan 73, Wild 86. The 390 px capture gives the same order (53-72 / 72-112 / 133-152 / 178 / 198).
  The order is right at every step. Two blemishes: three lows read 94-136 (see G3), and the Wild out-shines the
  Leviathan by more than the target asked (target 150 against 130).
- **G3 (idle):** the three hot lows are the Q above the viper (136), the 10 under the angler (117) and the A beside
  the helmet (104). I cannot tell from a still whether that is overscan from the neighbouring creature inside my
  measurement window or a real local light; either way a low beside a creature reads brighter than a low alone. The
  tablets on the right-hand column also carry a warm rim that the target does not have.
- **G4 (idle):** the reel frame is physical; the gauge fills. Everything else is the old UI: the "3,125 WAYS" pill
  floats on the lintel, the depth and sonar panels are cyan-line boxes, controls are round web buttons.
- **G5/G6 (idle):** the frame's mean luminance is 29 against 9 for the left panel and 4 for the right panel. Three
  materials on one screen: oil-painted steel, flat near-black glass with 1 px cyan borders, and neon rings. The sill
  is cut off by the control bar and the spin ring overlaps it.
- **G1/G2 (help):** the Wild and the four brass neighbours are clearly brighter than the rest in H5. In H4 they are
  not: they appear while the board is still dimmed and the creature is on top of them.
- **G4 (help):** the name card is off the reels but is still a neon-orange box sitting on the painted lintel, next to
  the "WAYS" pill.

## Status of the round-two fixes

| # | Fix | Status | Evidence |
| --- | --- | --- | --- |
| G1 | Ladder under game lighting | **Done** | Order holds cell by cell at both sizes (numbers above). Creatures are 2-3 times the lows in cell mean. |
| G2 | On-screen size per tier | **Done** | By eye on the fixed board: tablets about 0.70 of a cell, mids about 0.90, highs fill and touch the cell edge, Leviathan and viper overlap neighbours. My automatic bounding-box measure saturated on this capture, so there is no number. |
| G3 | Impact is the brightest frame, mouth on the cell | **Partly** | Brightness: done. Frame mean 15.2, 14.2, 10.0, **32.2**, 14.7, 16.2 (full) and 14.5, 14.7, 13.9, **30.6**, 16.6, 17.0 (short). Mouth: in H2 and in the film at +392 to +692 ms the jaws sit about one cell above and left of the struck cell. The flash also shows concentric line rings, a sonar-ping graphic, not water. |
| G4 | Card off the grid, lift, earlier undim | **Partly** | Card is on the top edge. Board is back by about +790 ms after the bite (was 1300). The changed cells get no lift at the moment they change, and the card is still an orange web box. |
| G5 | Eye during the dread | **Partly** | It is there and the tablets do go dark against it. It is too faint: grid luminance 5th-95th percentile is 5-42 in the game against 0-104 in the storyboard, and the pupil is hidden behind a tablet instead of sitting in a reel gap. |
| G6 | No orange box, no dot bubbles | **Partly** | No orange box under the painting. A cyan rectangle outlines the struck cell from H4 on, and dot particles still ring the changed cells in H5. |
| G7 | Fixed-board captures | **Done** | `slice_set_1920.png`, `slice_set_390.png`; help starts from a board of lows so all four neighbours turn. |
| T1 | Frame scales, seals, blank plates, parts | **Done** | Five distinct runes, real numerals, no gibberish; the pack in `generated/targets/moments/game_frame/` has blank plates, lit and unlit seals, hub states, and totals 0.51 MB. Duplicate corner plates remain. |
| T2 | Usable HUD | **Done** | Bone values on dark insets, steppers, lit hub, priced xBet and bonus buy, auto and turbo as separate switches. Readable in my 2x view of `keyframe_master_390.png`. No reserved corner for menu and sound is drawn. |
| T3 | Ladder survives the falloff | **Partly** | Master blurred peaks: lows 43-80, helmets 89-96, compass 94, viper 101, squid 102, angler 119, Leviathan 139. Order holds; mids and two highs are within 10 points of each other. Good enough to pass. |
| T4 | Symbol grade fixes | **Done** | Helmet reads as brass again (peak 106-118 in game), Wild is red not pink, chips differ per tablet. |
| T5 | Seam and jets | **Partly** | Seam wanders and no longer boxes a non-winner; W3b is a real fold. W2 bursts are white starbursts with radial needles (`r3_W2_100.png`), and they cover the winners. |

## The help: game against storyboard, in the order a player would notice

1. **The reward appears underneath the creature (H4).** At +392 to +692 ms the neighbours are turning while the
   head and body still cover the upper right of the grid and the board is still dimmed. The storyboard's H4 is the
   clearest frame of the sequence; the game's is the most cluttered. The player only sees what they got at about
   +790 ms. Fade the creature faster and light the changed cells the instant they change.
2. **The mouth is not on the cell.** The storyboard's best idea is that the bite leaves its mouth behind as the Wild,
   same place, same size. In the game the jaws sit a cell away from the highlighted cell, so the Wild appears beside
   the mouth rather than out of it.
3. **The dread is barely visible.** A dim teal shape with no readable pupil. In the storyboard this is the frame
   people would remember. It needs about twice the brightness and the slit in a reel gap.
4. **The impact reads as a sonar ping.** Bright, correctly timed, but drawn as line ellipses and a cloud of white
   dots. The storyboard has spray and a falling jet.
5. **No targeting beat.** The game goes from eye to lunge. The lunge itself tells the player which cell, so this
   matters least; the storyboard's pupil snap can be dropped from the target rather than built.
6. **UI leftovers:** cyan rectangle on the struck cell, orange name card, dot particles in the aftermath.
7. **Aftermath has no water.** The storyboard's run-off down the glass is absent; the board simply returns.

What matches the storyboard: both lengths (2.69 s and 1.39 s measured), the order, one hero creature, the luminance
curve (dip, spike, settle), and a result the player can read at the end.

## The mixed frame: how bad, and what order to finish it

**It is the main thing holding the idle screen back, and it is worse than either style alone.** With only the web UI
the screen was consistent and cheap. With the painted frame in the middle it now shows a stranger, in one glance,
that two different games were glued together: the steel is three to seven times brighter than the panels beside it,
the panels still draw their own 1 px cyan borders, the spin ring overlaps the sill, and a rounded pill sits on a
riveted lintel. In portrait there is no painted frame at all.

Order, using what the pack already contains:

1. **Remove what floats on the painted frame.** The "WAYS" pill and the neon name card. Costs nothing, and it is the
   most visible clash because it sits on the steel itself.
2. **Sill and spin.** `sill.webp`, `spin_wheel.webp`, `spin_hub_idle / ready / spinning.webp`. The spin control is
   what the player looks at most and it currently hides the sill. Keep it a real `<button>` with the wheel and hub
   as its skin; keep the busy and stop states.
3. **Balance, bet, win.** `outrigger_l.webp`, `plate_blank.webp`, `stepper_minus.webp`, `stepper_plus.webp`, and the
   WIN plate on the lintel. Values stay live DOM text in Bone on the dark inset. Steppers stay real buttons.
4. **Right side.** `outrigger_r.webp`, `sonar_housing.webp` (the existing sonar canvas drawn inside the housing),
   then xBet and bonus buy on `button_blank.webp` / `button_blank_on.webp` with their prices, then auto and turbo
   on `switch_knob.webp` / `switch_knob_on.webp`, each removable by configuration.
5. **Bottom lintel.** Ritual bar and `seal_1..5_off / lit.webp`, replacing the multiplier ring and dot row in the
   right panel.
6. **Delete the left panel.** The pillar gauge already shows depth; move the depth number and zone name to the zone
   plate. The freed left third goes to the trench and the creature's body, as in the master.
7. **Portrait.** `lintel_portrait`, `pillar_l/r_portrait`, `sill_portrait`, `console_portrait`. Phones are where most
   play happens, so this should not wait long; it is last only because it reuses every decision above.

Menu, info, sound and the regulatory line stay conventional DOM controls, restyled dark and small.

Until step 4 lands, an interim measure removes most of the clash: take the cyan borders and corner brackets off the
two side panels and let them sit as dark recessed areas.

## Fix list, game only, in priority order

| # | Where in `index.html` | Exact change |
| --- | --- | --- |
| 1 | `topChip` (template line 310, value line 6624); `.strikecard`, `.strikecard.off` (lines 81, 87) | Hide the WAYS pill while the painted frame is on (`rf.on`); show ways and zone on the zone plate later. Restyle the strike card as a brass plate: no orange border or glow, dark inset, Bone text; show it only on the first strike of a session per level. |
| 2 | `levStrike` (5340) and `levBite` (2479) | Offset the hero painting so the centre of its fang ring lands on the centre of the strike footprint (today it is about one cell up and left); scale so the ring is about 1.6 cells wide. Verify on an edge cell and a centre cell. |
| 3 | `strikeSeq` (2178-2320), the `levOp` / `levOpT` changes at 2242 and 2272 | Start the creature's fade at the hit-stop release and finish it within 250 ms, so it is gone before the first neighbour turns. Call `engDim(others, false)` for the footprint and each transmuted cell at the moment it changes, with a 300 ms brightness lift of about +40%. |
| 4 | `levPreStrike` (2385-2400) | Eye: raise its opacity or gain to about double (target grid 95th-percentile luminance near 100, today 42); set `darkT` lower so tablets are true silhouettes; place the pivot so the slit pupil falls in the gap between reels 2 and 3, rows 1-2. Short version: keep at least 250 ms of it. |
| 5 | `biteFlash` (2326) and `spawnWater('geyser', ...)` (2503, 2525) | Remove the concentric line rings and the white-dot cloud. Keep the radial flash; add painted spray that bursts outward and falls, and run-off down the glass below the cell for about 800 ms. |
| 6 | `.strike.after` (line 85) and the surfacing particles (near 4772) | Remove the cyan rectangle on the struck cell after the bite; replace the dot ring around changed cells with a single soft Biolume bloom per cell. |
| 7 | Template around line 285-372 (`.panel.pl`, `.panel.pr`), `.spinbtn` (107-113), the `rf` block (6561-6568) | Start the HUD move in the order above: full sill visible with the spin wheel and hub as the skin of the spin button; then outriggers with plates and steppers; then sonar housing and priced buttons; then seals. Interim: remove the border and corner brackets from `.panel.pl` and `.panel.pr`. |
| 8 | `.rframe img` (line 72) and the `rf.on` condition (6564) | The frame is drawn at `brightness(.56)`. Either bring the surrounding UI up to it or take the frame to about .45 until the panels are replaced, so the steel is not the brightest surface on screen. Enable the portrait pieces when `G.por` is true. |
| 9 | `tier` table (line 585) | Wild gain 2.5 to about 2.1 and Leviathan 2.9 to about 3.1, so the apex sits closer to the Wild (today 181 against 210). Then check why lows beside a creature read 94-136 while lows alone read 45-72; if it is a local light, cap it. |
| 10 | Tablet rim in the symbol shader | Remove the warm rim on right-column tablets; the only rim should be the cool one facing the upper-left key. |

Targets, briefly, since they were not the focus: the masters pass. For the win storyboard, repaint the W2 burst as
grey-green lit water in a hard cone with a spray ring, no white star and no radial needles, and keep the winners
visible through it.
