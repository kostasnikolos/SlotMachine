# Discovery brief — how the Leviathan should appear

Status: complete through phase 5. Owner: Kostas. Written 2026-11-04 after the five-round reviewer loop on the 2.5D hero
shots (commits d0a4134 → 2839482).

## 0. Problem statement

The Leviathan is the game's signature, but today the player only ever sees pieces of it: an eye, open jaws, a rising head,
a frontal maw, each a painted close-up with shader life. The owner's verdict after playing: "the idea is good, but just the
teeth biting the symbols isn't nice". The creature has no body on screen, so the bite reads as a mouth pasted over the grid
rather than an animal lunging out of the dark. "Solved" = a strike where the player sees the Leviathan as a creature
(a figure with presence in the scene) that moves to the cell and bites, at the quality of Nolimit City's painted characters,
on a free/cheap toolchain, at 60 fps on a phone.

Constraints: free route only (Gemini app for images, local ComfyUI, no API billing); canvas front end (Three.js + 2D canvas,
own WebGL hero layer); single cyan key light and desaturated palette (art bible); the feel gates (hit-stop, cycle times,
no celebration at or below stake) must keep passing; the engine's strike event (footprint, transmuted symbols, timing) is fixed.

Open questions: is the engine's 1×1 to 3×3 footprint bite the right beat for a whole-figure reveal, or should the body
be a background presence and the bite stay a close-up? How much texture memory can the phone build spend on frames?

## 1. Needs (from the owner's own words in this session, in order)

| # | Stated request | Underlying need | Priority |
| --- | --- | --- | --- |
| N1 | "we need to make it realistic, if there is a way, or omit him, like Nolimit does on Beheaded" | A creature that reads as alive and part of the scene, or nothing. No tube, no cut-out. | must |
| N2 | "just the teeth isn't very nice, showing only its teeth biting" | The bite must show the animal, not only the mouth: body or figure context during the strike. | must |
| N3 | "maybe the leviathan on the background and the teeth showing up with a whole figure not just the mouth" | A persistent background presence plus a whole-figure lunge; the close-up as the climax, not the whole shot. | should |
| N4 | "render many images showing in very short time like a video? as we tried with open and closed mouth?" | Real motion between poses (open to closed jaws, approach to strike), not a static painting with warps. | must |
| N5 | "how is the wild which comes in the screen in Beheaded?" | Match the way Nolimit stages a feature symbol's arrival: character acts, symbol lands, timing tight. | should |
| N6 | earlier: "the hitting is too fast", "slow down" | Readable pacing; the creature moment must not rush the cascade beat. | must (gate) |
| N7 | earlier: "stay on free tools" | No paid animation suites or API billing unless a free tier covers it. | must |

Current process on a strike: hush 1.5–2.4 s, 3D silhouette hidden, painted jaws slide to the cell (0.9 s), jaw-mask slam on
the chomp held 257 ms, painting drops out (450 ms), wilds surface. Where it fails N2/N3: between the silhouette vanishing
and the jaws appearing there is no body; the jaws arrive as a picture, not as the head of the animal that was just lurking.

## 2. What exists (research 2026-11-04; sources named; "not found" = no public source)

**How Nolimit City does it.** Animator job ads ask for "AE, PS, Spine, AI" (vakanser.se/jobb/animator+75/); front-end ads ask
for "HTML5, Typescript, Pixi, GSAP" (vakanser.se/jobb/frontend+game+developer+3/); a 2024 candidate report names "Sprite,
Spine, and Pixi.js" as the animation toolset (naukri.com code360 interview experiences). So their characters are, most
plausibly, Spine skeletal rigs with mesh deformation on a PixiJS WebGL stage, with After Effects for VFX and set pieces.
No source shows Live2D, Rive, DragonBones or video layers. Spine has an official PixiJS runtime (esotericsoftware.com/spine-pixi).

**Beheaded (18 June 2024, nolimitcity.com/games/beheaded).** Shipwreck survivor hunted by a "Tzantza collector"; three Soul
Wilds (Happy, Sad, Angry) with Wild Zone sizes 1×1 / 2×2 / 3×3 at 4 / 10 / 18 souls (olbg.com/slots/games/beheaded). The
only sourced character moment: "a grotesque video is added to the gameplay, and it's played once you hit a payout of 25x
the bet or more" and "the Tzantza collector appears before the beginning of a bonus round" (slotcatalog.com/en/slots/beheaded,
search snippet). How the wild enters the screen: not found in any text source. The executioner belongs to Dead Men Walking
(Sept 2025): "animations bring the hooded executioner himself to life" (news.worldcasinodirectory.com, article 119773).

**Industry norm.** Push Gaming, Hacksaw and Playtech all hire Spine animators; Hacksaw asks animators to "create reference
material that front-end developers can use as a goal" (zerply.com, Hacksaw 2D Animator). Frame sequences survive for
"lightweight reels" and short bursts (keyframe.it.com/slot-symbol-animation). Vendor figure: one second of 30 fps flipbook
is about 3.39 MB versus 0.18 MB for the equivalent rig (esotericsoftware.com/spine-demos). Practitioners cap atlases at
2048–4096 px and halve frame rates (html5gamedevs.com topics 40335, 14319). WebM alpha video works only in VP8/VP9, iOS 15+.

**Tools for a single painting to animation.**

| Tool | Cost | Fit for us |
| --- | --- | --- |
| Spine Professional (meshes) | $379–449 one-off; Enterprise required above $500k revenue (business decision) | Industry standard; runtimes for Pixi and Three; needs a layered painting (parts), not our flat cut-outs |
| Live2D Cubism FREE | free under 10M JPY annual sales; 1 texture up to 2048 px, 100 meshes, 30 parameters | Built for "one painting breathes, blinks, turns"; the commercial condition is a legal check |
| Rive free | free, splash screen on export; own MIT web runtime | Fine for UI, awkward for a painted creature |
| DragonBones | free, MIT, community-maintained Pixi v8 port | Maintenance risk |
| AI image-to-video (Kling, Runway, Pika free tiers) | watermarked, non-commercial, opaque clips | Unusable for the product on free tiers |
| Local video models in ComfyUI (Wan 2.1 1.3B, AnimateDiff) | free, local on the RTX GPU, Apache/MIT licences | Opaque clips need chroma keying; moderate quality at 480p; untested here |
| Local frame interpolation (RIFE, FILM) between painted keyframes | free, local | Turns 3–5 Gemini keyframes into 24–48 frames; untested on our paintings |
| Depth-based 2.5D (today) | free | Life without a rig; cannot change pose |

A reacting whole-figure background creature is not documented as a standard pattern in any reviewed Nolimit, Hacksaw,
Push or Print Studios title; Nolimit's figure moments are framed set pieces (video or long sequence) at thresholds.

## 3. Options

| Option | What it solves | Leaves open | Effort | Cost | Risk |
| --- | --- | --- | --- | --- | --- |
| A. Whole-figure lunge painting as a third beat (far silhouette, whole creature rushing the glass, jaws), 2.5D as today | N2, N3 (the body connects to the mouth), keeps the passed gates | N4 only partly (warps, not poses) | S | 0 (one Gemini painting) | Gemini may not hold the creature's look at a new angle |
| B. Flipbook bursts from painted keyframes plus local frame interpolation, packed at 4096 px or less, 15–24 fps, 1–2 s, played by the hero layer | N4 (real open-to-closed, approach-to-strike motion), N2 with A's painting as a keyframe | Long idles (memory); every new pose needs a keyframe | M | 0 | Interpolation between paintings can morph instead of move |
| C. Skeletal mesh rig of a layered painting (Live2D FREE or Spine Pro), own Three.js player or Pixi runtime | N1–N5 the way Nolimit does it; idle loops are cheap | Needs the painting delivered in parts (head, jaw, body, fins, tendrils); licence check or $449 | L | 0 or $449 | Pipeline and runtime build; part-consistent art from Gemini is the hard bit |
| D. Local video model (Wan 2.1) chroma-keyed clip for set pieces (bonus intro, 25× and up), like Beheaded's video | The one documented Nolimit pattern; whole figure | Not the per-strike bite | M | 0 | 480p quality; keying halos; 8 GB VRAM |
| E. Real 3D rigged creature | Everything | Rejected earlier: 68 MB unrigged GLB, blobby AI meshes | L | 0 | As before |

Weights (owner's priorities first): "the animal, really moving" (N2, N4) 40%; free toolchain 25%; 60 fps on phone 15%;
effort to a visible result 10%; matches Nolimit's actual method 10%.

**Recommendation: A now, B as the experiment, C as the destination if B morphs.**
A fixes the exact complaint (a mouth with no body) in a day with one painting and keeps every gate. B is the "many
images like video" idea done the only free, licence-clean way (our own keyframes, interpolated locally), and it is what
the industry still uses for short bursts. C is what Nolimit actually does, but it needs parts art and a rig runtime; start
it only if B's frames morph. D is a later set-piece layer, not the bite. What would change this: a Spine Pro licence
approved (then C first), or Gemini failing to keep the creature consistent across angles (then C, with parts painted by hand).

Process today versus improved (strike): today = paint, cut out, shader warps, jaws slide, mask slam. Improved = paint
3 keyframes of the same creature (far, lunge, jaws closed), cut out, interpolate locally, pack a sheet, the hero layer
plays the burst (far, lunge, chomp) with the rig life on the final frame. Steps removed: the mask slam and its seam flash.

## 4. Riskiest assumption

"Gemini can produce pose-consistent keyframes of the same creature, and local interpolation between two of them reads as
motion, not a morph." If wrong, B collapses and C (a rig with parts) is the only route to N4.

Test (about 2 hours): take the existing open-jaws painting, ask Gemini for the same image with the jaws closed (image
edit, same angle, same light); cut out both; interpolate 12 frames with RIFE or FILM on the local GPU; pack a sheet; play
it in the hero layer at the chomp instead of the mask slam; capture a 60 ms sheet. Pass = the teeth travel and the lips
meet without smearing. Fail = smear or ghosting: stop B, brief the layered painting for C.

### 4a. Test status (2026-11-05)
- Toolchain proven: RIFE 4.9 (the ComfyUI-Frame-Interpolation node's implementation, MIT, cloned by the owner) runs on
  the RTX 5060 via `scripts/ai/interp_frames.py`; the hero layer plays a WebP frame sheet at the chomp (`flipbook_pack.py`).
- Half of the assumption holds: interpolating the open jaws to a synthetically closed copy (lower jaw slid up 16% of the
  height) gives 12 frames where the teeth travel and the throat closes coherently, no smear (artifacts/canvas/interp_dry_sheet.png).
- Still open: whether Gemini can deliver a closed-jaws painting that stays aligned with the open one (same angle, scale,
  position). If it drifts, the alignment, not the interpolator, is the risk; a remedy is to align B to A by the brow plates
  before interpolating (translate/scale fit on the matte) and to accept small drift as motion.

## 5. Open questions and risks

- Business/legal: Spine Pro purchase ($449) or Live2D FREE eligibility (annual sales under 10M JPY): owner's call.
- Memory budget on phone for bursts (target two 2048-pixel atlases or fewer, under 3 MB per moment).
- Whether the engine's 1×1 strike footprint is a big enough beat for a whole-figure lunge; the 2×2 and 3×3 strikes at
  depth are the natural home for the full sequence.
