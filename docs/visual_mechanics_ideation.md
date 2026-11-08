<!-- Ideation brief, 2026-11-08: mock each idea with its Gemini prompt before building. -->

# The Descent: Abyssal Leviathan — Visual mechanics ideation brief

Grounding: `docs/art_bible.md` (one key light upper-centre-left, palette Abyss/Trench/Biolume/Brass/Sulfur/Blood, no baked
backgrounds, gates G1–G8) and `docs/feel_design_plan.md` (ration the creature, silence before strikes, no presentation at or
below stake). The current captures tell us where the room is:

- `hero_eye.png` / `hero_lunge_bite.png`: the hero layer is the strongest thing on screen. The grid itself is still a 5x5
  of identical dark brass medallions floating in a thin teal bracket; the "viewport" is not yet a thing you could put your
  hand on. Everything below is built to make the grid and frame feel like the inside of a hull the creature is outside of.
- `crush_depth.png`: "crushed by pressure" is a dim plus a text card. It should be felt by the frame and the water, not read.
- `pressure_levelcard.png`: the rising head works; the card is text on black. The instruments around it do not know anything happened.
- `bigwin_t4_leviathan.png`: crack overlay + REC HUD is the right language; cracks should exist in the base game too, as a
  slow-growing record of pressure, so T4 is the payoff of something the player has watched grow.

All timings assume the UK profile (cascade step 450 highlight / 250 remove / 300 drop / 120 pause; cycle ≥ 2.6 s; nothing
celebratory at ≤ stake). Every idea has an "at ≤ stake" clause so G8 stays PASS.

**Prompt conventions for Gemini / SDXL** (paste first, then the per-idea prompt):

> Style: dark painterly deep-sea horror-industrial, desaturated teal and black, heavy film grain, Nolimit City grit, no
> cartoon, no neon rainbow. Single cold cyan bioluminescent key light (#3FE0D0) from upper-centre-left, cold low teal
> ambient, no white top light. Palette only: #02060A abyss black, #0B1418 trench, #1E2C31 silt, #B8874A and #D9B77E brass,
> #3FE0D0 biolume, #E8B04A sulfur, #E0314B blood, #F2E6CF bone. No text, no logo, no watermark, no UI.

For cut-out assets add:

> Isolated element on a pure solid black background #000000, no gradient, no vignette, no floor, no fog outside the
> element, hard edges where the element ends.

---

## (a) Win highlight and cascade

### 1. Seam Breach (the owner's seed, built out)

**What the player sees.** A win is not a glow, it is the sea getting in. On win detect: 0–40 ms the first symbol of the way
lights from behind (rim only, from the key light direction). 40–240 ms a hairline crack races across the glass along the
winning way, column to column at 40 ms/column, jagged, with a thin cyan refraction halo (the crack is in the glass in front
of the symbols, so it crosses the gaps between cells). 240–330 ms at each symbol on the way a needle-jet of water fires
inward from the crack, perpendicular to the path, 1–2 cells long, atomising into fine spray that drifts down; the medallion
behind it brightens as the jet hits it. 330–450 ms the seam widens into a slow flowing current that carries silt along the
way toward the last symbol, the water line slightly refracting the symbols beneath. Multiple ways through the same symbols
share one seam that thickens; a 5-of-a-kind seam is the width of a finger. At 450 ms the seam holds and the destruction step
(idea 3) takes over. Cascade step 2+: the old seams do not vanish, they dim to a wet scar for the rest of the spin. Depth
grade applies: 0–2,000 m the water is biolume cyan, 2,000–5,000 m sulfur-tinged, 5,000 m+ the water is dark and the halo is blood.

**At ≤ stake:** crack only, no jets, no current, no sound beyond the neutral tick; the crack fades in 300 ms.

**Why it fits.** The viewport is the only thing between the player and 800 atm. A win is the hull admitting the sea along
exactly the line the player is paid on. It reads as a way (a path), not a cell glow.

**AI mock brief (16:9).** Close-up of a thick riveted submarine viewport glass seen from inside, behind it a dark 5x5 grid
of tarnished brass medallions with carved runes, barely lit. A single jagged hairline crack runs horizontally across the
glass left to right through five medallions, glowing faint cyan at its edges with refraction, and from the crack thin
high-pressure needle jets of seawater spray inward toward the viewer at each medallion, atomising into fine mist, droplets
catching the cyan light. The medallions touched by the jets are brighter, the rest stay dark. Wet black steel frame with
rivets around the glass. Painterly, grainy, horror-industrial, dark.
Cut-out: One horizontal jagged glass crack with cyan refraction halo and three needle water jets spraying downward from it,
isolated on pure black #000000, no glass, no frame, for use as an overlay sprite.

**Rebuild.** Three.js foreground FX layer: the way is a polyline; a screen-space quad with an SDF crack shader
(noise-displaced segment distance, animated `progress`) draws crack and halo; jets are 2D canvas sprite strips spawned per
node, oriented perpendicular; the current is the same SDF with scrolling silt noise. Scars are the SDF frozen at low alpha.
**Cost:** M. **Risk:** low on cycle; medium on readability if the halo is too bright over lows: keep it under 30% luminance.

### 2. Lure Relay (high-tier variant of the way highlight)

**What the player sees.** When the winning way is made of creature medallions, the seam does not form first. The creatures'
own light relays down the way: 0–60 ms the first medallion's lure/eye opens, 60 ms later the next (max 240 ms for five).
Each ignition pushes a soft refraction ring 1 cell wide. On the last medallion igniting, the Seam Breach fires along the
whole way at once in 120 ms, like the glass could not hold against the combined light. The lures stay lit through
destruction and go out one by one as the symbols implode.

**At ≤ stake:** relay only, no seam.

**Why it fits.** Highs are the creatures; their win should be the creatures waking. Keeps the one-light rule.

**AI mock brief (16:9).** Row of four painted creature medallions (anglerfish, squid, viperfish, leviathan head) in dark
tarnished brass, each with a single bioluminescent cyan point lit inside the creature's eye or lure, the light increasing
in intensity from left to right, the last one blazing and casting cyan rim light on the ones beside it, thin concentric
refraction rings in the water around each lit point. Dark teal black background, grainy, painterly.

**Rebuild.** Per high symbol a 1-channel lure mask (64x64) sampled in the symbol shader with an `ignite` uniform; the ring
is a UV-displacement ripple in the symbol layer shader. **Cost:** S. **Risk:** none.

## (b) Symbol destruction and refill

### 3. Hull Implosion (replaces "explode")

**What the player sees.** Winning medallions do not burst outward, they are crushed. 0–33 ms the medallion squashes 8% on
the axis toward the seam. 33–50 ms hit-stop on the whole board (first implosion of a step only, and only if the step pays >
stake). 50–200 ms the medallion collapses to its centre like a can at depth: edges fold in with a brass tear, the rune face
buckles, scale 1.0 → 0.08 ease-in-quart, a short ring of dark brass dust and three or four bright flecks snap outward then
are pulled back by suction (velocity reversed at 120 ms). 200–250 ms a single bubble of trapped air escapes upward and the
slot is empty black. Symbols implode in way order, 25 ms apart (simultaneous after 10, so the step never exceeds 250 ms).
The existing dissolve sound's sine drop lands on the collapse frame.

**At ≤ stake:** implode without hit-stop or dust ring, at 70% scale, neutral.

**Why it fits.** Everything at depth dies by pressure, not by fire. Suction also motivates the refill physically.

**AI mock brief (16:9, a 6-frame strip).** Six-frame animation strip left to right of a tarnished brass medallion with a
carved rune being crushed by water pressure: frame 1 intact, frame 2 slightly squashed, frame 3 edges folding inward with
a torn brass rim, frame 4 collapsed to a crumpled brass knot with a ring of dark brass dust and a few bright cyan-lit
flecks, frame 5 tiny crushed slug with a single air bubble rising, frame 6 empty. Each frame the same size, isolated on
pure black #000000, cold cyan key light from upper left, painterly, grainy.

**Rebuild.** Symbol quad shader with a radial pinch (UV toward centre with a noise crease) driven by `collapse` 0→1; the
dust ring is 12 canvas particles with a velocity flip; the last 2 strip frames as a sprite for slug and bubble.
**Cost:** S/M. **Risk:** low; keep ≤ 250 ms.

### 4. Marine Snow Refill (replaces "drop", changes with depth)

**What the player sees.** Nothing falls from a shelf. In Sunlight and Twilight replacements sink into view from the murk
above as dark silhouettes, 300 ms, ease-in, with a thin trail of marine snow (pale specks drifting up past them), resolving
into a lit medallion only in the last 80 ms when they enter the key light; land with a 1-frame squash and a puff of silt
that drifts up. Columns stagger 40 ms. In Midnight and below the direction inverts: the vacuum pulls symbols up from below,
trailing bubbles, and the upper symbols slide down to meet them; at Hadal the incoming symbols rise lit blood-red from
beneath. The Core: refill comes from both edges toward the empty cells.

**At ≤ stake:** identical, without the silt puff.

**Why it fits.** Direction of refill is a free storytelling channel; "things come up from below" is the shift from
exploration to being hunted. Marine snow is the one thing every deep-sea documentary shows and no slot does.

**AI mock brief (9:16).** Vertical column of five dark tarnished brass medallions sinking downward through black water seen
through a porthole, the top ones barely silhouetted in murk, the bottom one entering a cyan key light and resolving into a
lit carved rune medallion, pale specks of marine snow drifting upward past them, faint silt cloud at the base. Teal black,
painterly, grainy, horror-industrial. Variant: medallions rising upward from a blood-red glow below, trailing small bubbles.

**Rebuild.** 2D canvas symbol layer: per-cell y tween with a luminance ramp tied to y; marine snow is a cheap particle
field with per-level direction; the inversion is the same tween with the source edge flipped. **Cost:** S. **Risk:** low;
resolve the medallion by 220 ms.

## (c) The frame reacting to depth and pressure

### 5. Hull Integrity (the viewport keeps the score)

**What the player sees.** A real riveted steel frame with a thick glass pane and a bottom sill that degrades with pressure
points and never heals within a level:
- L0: clean glass, a faint breath of condensation at the lower corners on an 8 s cycle.
- L1: condensation beads form at the top edge and run down one at a time (every 6–10 s, 1.2 s run, refracting the symbols).
- L2: a hairline crack starts at the upper-left rivet. Every pressure point extends it one segment (20–60 px, 120 ms, a
  1-frame tick flash and a glass "tink"); seeded per session so it is the same crack all level long.
- L3: rivets at the crack's end weep rust; the crack forks; vents are visible as brass pipes on the sill venting silt.
- L4: water pools on the inside sill with a refracting waterline across the bottom row; the pane bows (0.5–1% barrel
  distortion breathing with the pressure chip pulse).
- The Core: the crack reaches the opposite rivet; the T4 big-win crack overlay is the continuation of this one.

"Crushed by pressure" replaces its text card with: the frame shudders 2 px, one crack segment grows, a bead drops, the
symbols dim, 400 ms total; the text becomes a small stamped label on the sill.

**At ≤ stake:** crack growth is allowed (a loss signal) with no flash and no sound beyond the tink.

**Why it fits.** The thesis is "pressure accumulates". A gauge says it; the frame proves it. The frame is the HUD.

**AI mock brief (16:9).** Interior view of a heavy riveted black-steel submarine viewport frame around a square pane of
thick glass; behind the glass a dark 5x5 grid of tarnished brass rune medallions. The pane shows a long forked hairline
crack from the upper-left rivet across a third of the glass with faint cyan refraction, condensation beads running down
the top edge, rust streaks weeping from two rivets, a shallow pool of water on the inside sill at the bottom refracting the
lowest medallions. Cyan key light upper left, sulfur-tinted water, wet metal, painterly, grainy, horror-industrial.
Cut-outs: Riveted black steel viewport frame, square, empty centre, isolated on pure black #000000. Single forked glass
crack segment with faint cyan refraction, isolated on pure black #000000.

**Rebuild.** Frame as a painted 9-slice; crack as a seeded L-system polyline through the idea-1 SDF shader; beads are
canvas sprites with a refraction offset in the symbol layer; pooled water is a horizontal band shader; bowing is a post
barrel uniform. **Cost:** L (five pieces that ship independently). **Risk:** medium on readability: crack under 2 px,
never across a glyph at full opacity, luminance capped at 40% over cells.

### 6. The Sill (pressure meter as pooling water)

**What the player sees.** The bottom lintel is a trough. Progress toward the next zone is the water level in the trough:
every pressure point adds a measured pour from a brass vent at the left end (300 ms, a ripple travelling the width), the
water line creeps up the rune seals embossed on the sill. Cascade landings make it slosh (1-cell wave, 400 ms). One point
short (idea 8) the meniscus bulges over the lip and trembles. Level-up: the trough overflows down the frame's outer face in
a sheet, 800 ms, then resets empty and the hero head rises behind the level card. The multiplier chip sits half-submerged at
the right end and its pulse makes rings.

**At ≤ stake:** the pour happens (progression) with no ripple highlight.

**AI mock brief (16:9, letterbox crop of the bottom of the frame).** Close-up of the bottom sill of a riveted black-steel
submarine viewport seen from inside: a shallow brass-lined trough half full of dark teal water, five carved rune seals
embossed on the back wall of the trough partially submerged, water pouring in from a small brass vent pipe at the left end,
a ripple travelling right, the meniscus catching a cyan rim light from upper left, wet metal, rust, grain. Dark, painterly.

**Rebuild.** 2D canvas: a 1D heightfield water surface (spring sim, 64 samples) as a filled path with a 2 px specular
line, clipped to the trough sprite; seals under a waterline mask; overflow as a sheet strip. **Cost:** S/M. **Risk:** low.

## (d) Anticipation and near-miss

### 7. Dead Reel (one column short)

**What the player sees.** Only when the outcome is genuinely decided by the last column (either direction, so it stays
honest): as column 4 lands, the key light flickers and the lamp over column 5 fails (80 ms flicker, 2 frames off); column 5
does not refill. For 600 ms the column is black water with marine snow; the ambience drops out; the hero eye slides in
behind column 5 only, cropped by the pane, pupil contracting on the empty cells. At 700 ms the column's symbols sink into
view at 60% speed, resolving bottom to top, 150 ms apart, and the lamp relights on the last one. Hit: Seam Breach jets fire
from the eye's side. Miss: the eye blinks once and recedes in 400 ms, no shake, neutral. Total +900 ms.

**At ≤ stake / miss:** strictly neutral recede.

**AI mock brief (16:9).** Interior of a riveted submarine viewport, a 5x5 grid of dark brass rune medallions behind glass,
the rightmost column is empty black water with pale marine snow drifting; pressed against the glass behind only that
column, cropped by the frame, is a huge pale sea-creature eye with a vertical slit pupil, glowing cyan-white, veined, its
iris light catching the rivets and the edge of the neighbouring medallions. Rest of the scene dim, the lamp over the empty
column is dark. Painterly, grainy, horror, desaturated teal.

**Rebuild.** Hero flipbook eye with a per-column crop mask and a look-at offset; column 5 refill is idea 4 at 0.6 speed;
lamp flicker is a key-light keyframe. **Cost:** M. **Risk:** medium: the honesty gate; fire on true decisive columns
only and log every trigger with the outcome.

### 8. Meniscus (gauge one point short)

**What the player sees.** When pressure points land exactly one short of the zone line at spin end: in the gauge the
submersible's lamp beam touches the zone line and the water above it bulges 3–4 px, trembling at 8 Hz for 500 ms; the zone
label ghosts to the next zone's name at 20% alpha for two frames; in the trough the meniscus climbs over the lip and holds;
one crack segment twitches without growing. Everything settles in 300 ms; only a low creak of metal. Next spin, the first
point gained plays the level-up with the overflow.

**At ≤ stake:** a progression tease, capped at 800 ms so it does not pad losing spins.

**AI mock brief (9:16 crop of the gauge pillar).** Tall narrow brass-and-steel depth gauge set into a black stone pillar: a
vertical shaft of dark water with a tiny submersible whose single lamp beam points down to a horizontal etched zone line
reading as a bulkhead ring; the water at the line bulges upward as a trembling meniscus, barely held, faint cyan light
under it; above, a mechanical odometer depth readout. Rust, condensation, grain, cyan key light upper left, painterly.

**Rebuild.** 2D canvas gauge: a sine-driven bulge on the water-column path, a label crossfade, idea 6's heightfield.
**Cost:** S. **Risk:** low.

## (e) Depth gauge and HUD as living instruments

### 9. Bathysphere Instruments (gauge, sonar, chip)

**What the player sees.** The left pillar becomes a brass bezel with a glass face, a mechanical odometer depth readout whose
digits roll (120 ms per digit, with a clack), a shaft of water with the descending submersible whose lamp is the only light
in the pillar, and bulkhead rings at each zone line the sub passes through (400 ms pass, the ring's shadow sweeping the
sub). A pressure needle under the odometer jitters with amplitude growing per level (±1° at L0, ±6° at L4) and pins into
the red at the Core. Marine snow drifts up the shaft, faster when the sub sinks. Top-right sonar: NO CONTACT most of the
time; the Leviathan appears as a blip 1.5–3 s before any hero strike, closing on each sweep (the honest telegraph and the
audio drop-out window); after the strike the blip sits at the centre and fades. The multiplier chip becomes a brass pressure
valve whose pulse is a needle kick; at ×3 and above it vents a small jet of silt on each pulse. Big wins: the sonar ring
flashes per tier, the odometer rolls down live with the count.

**At ≤ stake:** passive life only; no sonar event, no vent.

**AI mock brief (9:16 pillar; 1:1 sonar).** Vertical brass bathysphere instrument set into a black riveted steel pillar: at
the top a mechanical odometer depth counter with bone-white digits in brass drums, below it a small round pressure dial with
a trembling needle near a red zone, below that a tall glass-fronted water shaft with a tiny submersible and its lone
downward lamp beam, horizontal etched bulkhead rings at intervals, pale marine snow drifting up. Condensation on the glass,
rust, cyan key light upper left, desaturated teal black, painterly, grainy.
Sonar: Round brass-rimmed sonar scope with a dark green-teal glass face, a sweeping phosphor line, concentric rings, a
single faint contact blip near the outer ring, grain and scratches on the glass, cyan-teal only, isolated on pure black #000000.

**Rebuild.** 2D canvas for all instruments (odometer = digit strips with a y tween; needle = rotation with noise jitter;
shaft = idea 4's snow field); the sonar blip is driven by the strike scheduler. Pillar and bezel are painted 9-slices.
**Cost:** M. **Risk:** low.

## (f) Idle and attract life

### 10. Something Passes

**What the player sees.** 10 s of no input: the ambient dims 10% over 2 s and the chip pulse slows to a resting heartbeat.
At 12 s a vast shadow slides across the backdrop behind the grid from right to left over 4–5 s, never resolved, visible
only because the key light is occluded: the rim light on the medallions dims and shifts as it passes, and the marine snow
in the gauge swirls in its wake. At 25 s a single condensation bead runs down the glass. At 40 s the hero eye opens at the
pane edge for 1.2 s, looks at the spin button, and recedes. At 60 s the pane fogs from the corners and the sonar shows a
faint contact that never closes. Any input snaps everything back in 200 ms. No symbol ever lights, no sound rises.

**AI mock brief (16:9).** Interior of a riveted submarine viewport, a dim 5x5 grid of dark brass rune medallions behind
glass, cyan key light from upper left partially blocked by an enormous indistinct shadow passing behind the glass from
right to left, so the right half of the medallions have lost their rim light and the left half still catch it; a single
drop of condensation running down the glass; marine snow swirling. Nothing of the creature is identifiable, only its
absence of light. Desaturated teal black, grainy, painterly, lonely.

**Rebuild.** An occluder sprite multiplied into the key-light term the symbol shader already uses, translated over 4.5 s;
everything else reuses existing pieces. **Cost:** S. **Risk:** none; never during a cycle or count-up.

## (g) Symbol upgrades and transmutation

### 11. Crush and Recast (rune purge at level-up)

**What the player sees.** When the gauge purges a low rune, before the level card: every instance of that rune on the board
is crushed in reading order, 60 ms apart (idea 3's implosion without the dust, ending on a small barnacled brass slug,
220 ms each). The slugs are dragged by the current to the sill and drop into the trough with a plink. The rune's seal on
the sill fills with blood red from the bottom, 600 ms, and a crack runs through it. Only then the trough overflows and the
head rises. Where that rune would have landed, the refill brings the next rune up instead; the first upgraded symbol in a
purged slot arrives wet, with a drip for 1 s. Maw-bite transmutation uses the same family: the symbols the Maw leaves behind
carry a bite crescent missing from the rim and a bead of dark water running out of it for the rest of that cascade.

**AI mock brief (16:9, two assets).** Three dark brass rune medallions with the letter K being crushed in sequence by
pressure, left intact, middle folding inward, right fully collapsed into a small barnacled brass slug sinking toward a
brass trough of dark water below; a rune seal embossed on the trough's back wall filling with blood red from the bottom
and cracked; cyan key light upper left, desaturated teal black, painterly, grainy, horror-industrial.
Cut-out: A dark brass creature medallion (anglerfish) with a crescent bite missing from its rim, torn metal at the bite
edge, a single bead of dark water running down from the bite, isolated on pure black #000000.

**Rebuild.** Idea 3's collapse shader with an alternate end sprite; slug travel is a canvas tween; seal fill is a waterline
mask in blood; the bite crescent is a per-symbol alpha mask on the shared rim plus a 1 s drip sprite. **Cost:** M.
**Risk:** low; cap the purge at 1.2 s by going parallel after five.

## (h) Portrait-specific

### 12. Flooding From Below (1080x1920)

**What the player sees.** In portrait the lower third is the hull floor. Pressure is shown as the compartment flooding: a
waterline sits across the lower stage, below the grid at L0, climbing per level until at Hadal it covers the bottom row of
the HUD (controls read through water with refraction and a film of silt; the DOM controls stay crisp above a glass plate).
Seam Breach jets fire down toward the waterline and ripple it. Cascade landings slosh it. The depth gauge moves to a brass
strip down the right edge of the grid with the odometer at its top; the sonar becomes a small disk in the top corner. The
hero eye presses up from below the waterline, half-submerged. Level-up: the waterline jumps one band with a surge up the
side walls, 600 ms, and the head rises through the water under the card.

**AI mock brief (9:16).** Vertical view inside a riveted submarine compartment: a square viewport in the upper-middle with
a dim 5x5 grid of dark brass rune medallions, a brass instrument strip down its right edge with an odometer depth counter;
below the viewport the compartment floor is flooded, a dark teal waterline crossing the lower third with refraction and a
film of silt, wet steel walls with rust streaks, a huge pale creature eye half-submerged below the waterline looking upward,
cyan key light from upper left, condensation, grain, painterly, horror-industrial, desaturated teal black.

**Rebuild.** A full-width band shader (UV displacement below the line, specular line, silt film) with a `level` uniform;
the portrait HUD panel is a layout swap; the eye is a flipbook crop plus the band shader on top. **Cost:** M. **Risk:**
medium only for the HUD under water: refraction under 3 px around the regulatory controls.

---

## Ranking by impact per effort

| Rank | Idea | Moment | Cost | Impact | Why here |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 Seam Breach | win way | M | very high | The owner's seed; changes every winning spin; one shader plus sprite jets. |
| 2 | 3 Hull Implosion | destruction | S/M | high | Every cascade step, cheap, matches the audio recipe. |
| 3 | 4 Marine Snow Refill | refill | S | high | Every step; depth-inverting direction is a free narrative beat. |
| 4 | 10 Something Passes | idle | S | high | Cheapest "the creature is alive" signal; reuses everything. |
| 5 | 9 Bathysphere Instruments | HUD | M | high | Fixes the HUD permanently and telegraphs the strike honestly. |
| 6 | 6 The Sill | HUD / level-up | S/M | medium-high | Turns pressure points into water; pairs with 8 and 11. |
| 7 | 2 Lure Relay | win way (highs) | S | medium | Makes highs feel like creatures. |
| 8 | 8 Meniscus | near-miss | S | medium | Quiet, cheap, best with 6 and 9. |
| 9 | 11 Crush and Recast | purge / transmute | M | medium-high | Strong, but only at level-ups and bites. |
| 10 | 5 Hull Integrity | frame | L | very high | Highest ceiling; five pieces; ship crack + beads first. |
| 11 | 7 Dead Reel | anticipation | M | high | Great moment, highest gate risk; needs engine-side trigger logging. |
| 12 | 12 Flooding From Below | portrait | M | medium | After the landscape set is locked. |

## Mock these three first

1. **Seam Breach (idea 1)**: validates the owner's seed and the whole "sea gets in" language; if crack-plus-jets reads at
   64 px cells, the rest of the family (5, 6, 12) is safe.
2. **Hull Integrity (idea 5)**: mock the full L3 frame state as one 16:9 image; the cheapest way to decide whether the
   frame should carry the score before anyone builds a crack system.
3. **Bathysphere Instruments (idea 9)**: the pillar in 9:16 and the sonar as a cut-out; judge at once whether painted
   instruments beat the current web pills.

Fourth, if there is budget for one more image: Hull Implosion (idea 3) as the 6-frame strip, the image that most changes
how every cascade feels, and directly usable as a sprite reference.
