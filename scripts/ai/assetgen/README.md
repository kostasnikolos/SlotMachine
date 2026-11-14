# The asset kit — generators, not downloads

Everything here is **code that makes assets**, written for this game and re-runnable. It exists because the two ways we
had of getting art and sound both have a hole in them:

- **AI generation** (Gemini, local SDXL) is good at one painted hero image and bad at a *set*: five runes that must share
  one construction, a frame that must tile, a sound that must sit in a budget. It also can't be re-run with one value
  changed, and its output has weak copyright (`docs/audio_sourcing_brief.md`).
- **Libraries** (Sonniss, Freesound CC0) give real recordings but nothing specific to this game.

A generator is the third way: deterministic, free, parameterised, ours by authorship, and it regenerates the whole set
when a decision changes. Use it for anything systematic; keep AI generation for the hero paintings it is good at.

## What is here

| File | Makes | Command |
| --- | --- | --- |
| `sfx.py` | The sound set (dissolve, land, crush, impact, riser, roar, seam jet, hull creak, tick, shimmer) as 48 kHz WAVs | `python scripts/ai/assetgen/sfx.py --sheet` |
| `symbols.py` | The five low-rune medallions: cast brass, corroded, the rune carved in, one cyan rim light | `python scripts/ai/assetgen/symbols.py --sheet` |
| `synth.py` | The offline synthesiser behind `sfx.py` (oscillators, noise, biquads with sweeping cutoff, FM, convolution reverb) | library |

Output goes to `generated/` (git-ignored) with a `manifest.json` next to it recording source and licence for every
file, which is the provenance log the audio brief asks for. Contact sheets go to `artifacts/canvas/` for review:
`sfx_sheet.png` (waveforms) and `symbols_sheet.png`.

## Rules the generators follow

- **Deterministic.** Each asset seeds from its own name with SHA-256, so a re-run byte-matches and a diff means a
  parameter actually changed. Never `random.seed()` from the clock or Python's salted `hash()`.
- **One key light.** Every image shades from upper-centre-left in bioluminescent cyan, per `docs/art_bible.md`.
- **No bubbles as hits.** Sounds are pressure, metal and water mass, per `docs/feel_design_plan.md` section B.
- **Parameterised, not hand-tuned twice.** A depth level, a size, a cascade step are arguments, not copies.

## Adding a generator

Add a module here, give it a `--sheet` flag and a `manifest.json` entry per asset, seed it by name, and list it in the
table above. Keep it dependency-free beyond numpy and Pillow, which the repo already has.

## What this does not replace

The painted creature hero shots (`scripts/ai/comfy_hero.py`, the Gemini prompt packs) stay as they are: a leviathan's
eye is not a thing to write in numpy. The kit covers the systematic half.
