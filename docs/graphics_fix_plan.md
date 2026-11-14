# Graphics and sound fix plan

Written 2026-11-14 after the owner's verdict on the tool examples: the painted fish are good, the rune icons are
not. The order of work is the owner's: **first pictures of how we want it, then build one complete slice
(frame + action + icon + sound), reviewed at each step.**

## What is wrong today (from `artifacts/canvas/portrait_1920x1080.png`)

1. **Low runes.** Five dim procedural brass rings fill 60-70% of every grid. They are the most-seen art in the
   game and the weakest. The art bible asked for carved basalt glyphs with no frame; neither the atlas nor my
   `symbols.py` medallions delivered that.
2. **No set.** Each creature symbol sits in a different ornate ring with baked-in text and its own background.
   Nothing looks painted by one hand, and the tiers do not separate.
3. **The frame is web UI.** Thin cyan lines and flat boxes; the reels do not sit inside a physical object.
4. **Moments have no picture to aim at.** The help (Leviathan lifeline strike) and the win were built straight
   in code. We never agreed what a perfect frame of each looks like.
5. **Sound is designed per effect, not per moment.** There is no cue built to the beats of the help, and
   symbols share generic voices instead of each icon having its own.

## Step 1 — Targets ("photographs of how we want it")

Three specialists work in parallel to one shared beat sheet, all on the licence-cleared local stack
(Z-Image-Turbo for paint, BiRefNet for cut-outs, our numpy synth for sound):

| Target | Output |
| --- | --- |
| Symbol set: three directions for the lows, one chosen; mids and highs repainted to match | `artifacts/targets/symbols_target.png`, `symbols_before_after.png` |
| Master key frame of the idle screen, as painted layers | `artifacts/targets/keyframe_master.png` |
| The help, six frames H0-H5 | `artifacts/targets/storyboard_help.png` |
| The win seam, three frames W1-W3 | `artifacts/targets/storyboard_win.png` |
| Sound: help cue in stems, win seam by cascade step, a voice per symbol | `artifacts/targets/sound_*_sheet.png`, `scripts/ai/assetgen/moments.py` |

Beat sheet (shared by picture and sound):

- **Help, ~2.4 s.** H0 stillness → H1 dread, the eye opens (0-600 ms) → H2 approach, the frame strains
  (600-1100) → H3 impact, with a vacuum dip just before it (1100) → H4 transformation (1180-1700) →
  H5 aftermath (1700-2400).
- **Win seam, ~0.9 s.** W1 hairline crack (0-150) → W2 breach, water jets through (150-500) → W3 implosion
  and scar (500-900).

## Step 2 — Review the targets

A reviewer who did not make them scores the sheets against the art bible gates (readable at 64 px, tier
hierarchy under blur, one light, cohesion, reference parity). Anything under 4 goes back to its maker.

## Step 3 — One complete slice in the real game

Not everything at once. One vertical slice, end to end, so we learn the pipeline before repeating it:

1. **Icon:** the chosen low runes and repainted symbols packed into the atlas (albedo, normal, emissive, aux).
2. **Frame:** the painted reel frame from the master key frame, layered behind the grid.
3. **Action:** the help, re-timed to the storyboard beats.
4. **Sound:** the help cue and the per-symbol voices wired to the same beats.

Gates before it counts as done: the game-feel gate, the math pin (no engine change is expected), and a
reviewer comparing game captures frame by frame with the storyboard.

## Step 4 — Repeat for the rest

Win seam, level-up, big-win tiers, each as picture → review → slice. The targets stay in `artifacts/targets/`
as the standing reference.

## Rules that do not change

- Licence-cleared models only (`docs/local_asset_tools.md`); every asset logged with model and licence.
- No studio or artist names in prompts; no competitor art, ever.
- Sound cannot be judged by a model. Every cue is verified on meters and still needs the owner's ears.
