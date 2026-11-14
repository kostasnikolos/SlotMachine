# Free local asset tools — what we can legally ship

Researched 2026-11-14. Everything here runs on the RTX 5060 (8 GB) through the ComfyUI we already have, and
costs nothing. The filter is **commercial use of the model**, not just of its output: this is a revenue-generating
gambling product, so a licence that forbids commercial *use* is out even when it blesses the outputs.

None of this is legal advice, and a licence is not regulatory clearance — see the caveats at the bottom.

## Install next, in order

| # | Model | Repo | 8 GB plan | Licence |
| --- | --- | --- | --- | --- |
| 1 | **Z-Image-Turbo** (6B) | `Tongyi-MAI/Z-Image-Turbo` | FP8 or GGUF + `qwen_3_4b` text encoder; official ComfyUI template | **Apache 2.0** |
| 2 | **Wan 2.2 TI2V-5B** (image→video) | `Wan-AI/Wan2.2-TI2V-5B` | ComfyUI's own docs say it fits 8 GB with native offloading | **Apache 2.0**, commercial use stated |
| 3 | **Chroma1-HD** (8.9B) | `lodestones/Chroma1-HD`, GGUF `silveroxides/Chroma1-Base-GGUF` | GGUF Q4 + T5-XXL + FLUX VAE | **Apache 2.0** |
| 4 | **Qwen-Image-Edit-2511** (20B) | `Qwen/Qwen-Image-Edit-2511`, GGUF `QuantStack/…-GGUF` | GGUF Q4 or Nunchaku 4-bit | **Apache 2.0** |
| 5 | **FLUX.2 klein 4B** | `black-forest-labs/FLUX.2-klein-4B` | GGUF Q4 mandatory (official figure is 13 GB) | **Apache 2.0** — the 4B only |
| 6 | **BiRefNet** (cut-outs) | `ZhengPeng7/BiRefNet` | trivial | **MIT** |
| 7 | **Real-ESRGAN** (upscale) | `xinntao/Real-ESRGAN` | trivial | **BSD-3-Clause** |
| 8 | **Krita + krita-ai-diffusion** | `Acly/krita-ai-diffusion` | runs against our ComfyUI | **GPL-3.0** plugin; our art is ours |

Z-Image-Turbo is the quality-per-VRAM winner for painted creature art and renders in 8 steps, so iteration is fast.
Chroma1-HD is FLUX-grade painting on schnell's permissive licence — the dark deep-sea workhorse.
Qwen-Image-Edit-2511 is the "same creature, new pose" tool; slow here but legally clean.
Wan 2.2 is the only image-to-video model I would ship with.

Also install **ComfyUI-GGUF** (city96) for every quantised model above, and **Nunchaku** for Qwen-Image-Edit on 8 GB.

Keep what we already own: SDXL (OpenRAIL++-M) + **ControlNet Union ProMax** (`xinsir/controlnet-union-sdxl-1.0`,
Apache 2.0) stays the inpaint/outpaint/pose backbone.

## Do not install, do not ship

- **FLUX.1-dev, FLUX.1 Fill [dev], FLUX.1 Kontext [dev], FLUX.2 [dev], FLUX.2 klein 9B** — FLUX [dev]
  Non-Commercial Licence v2.0 (25 Nov 2025). §1(c) excludes "revenue-generating activity"; the outputs carve-out
  is in tension with it and is not an argument to run in front of a gambling regulator. A paid BFL licence exists.
- **Qwen-Image-2.1 / 2.0** — Qwen Research Licence, research or evaluation only. It is the one with native RGBA
  sprite output, which is exactly what a slot wants. Still no.
- **SDXL-Turbo** — `sai-nc-community`; the launch post says not intended for commercial use.
- **Stable Video Diffusion**, all variants — Stability non-commercial research licence.
- **SUPIR** — non-commercial without the author's written permission.
- **4x-UltraSharp** — CC-BY-NC-SA-4.0. Widely assumed free; it is not, and ShareAlike contaminates the pipeline.
- **RMBG-2.0** — CC BY-NC 4.0. Use BiRefNet, which it is built on.
- **CogVideoX-5B** — needs a bigmodel.cn commercial registration (2B is Apache).
- **SD 3.5** ($1M registration) and **LTX-Video** ($10M) — usable today, but a scheduled problem later.

Quantising does not launder a licence: a GGUF or Nunchaku rebuild of FLUX-dev is still FLUX-dev.

## Tools worth having beside the models

- **Krita AI Diffusion** — live inpaint/outpaint on a painting canvas against our ComfyUI. Biggest workflow win.
- **Material Maker** (MIT) — procedural metal, bone and coral surfaces for frames and medallions.
- **Blender** — 2.5D symbol renders with identical lighting across a set: consistency by construction, not by luck.
- **Inkscape** (GPLv2) — vector UI frames and HUD.
- **DragonBones** runtimes (MIT) — free Spine alternative if we ever rig a symbol.
- **SpriteKiln** (GPL-3.0) — a ComfyUI node pack of 30 game-art workflows. Its own docs want ~24 GB VRAM and it is
  untested on NVIDIA, so take its workflow design, not its pipeline.

## The third way: our own generators

`scripts/ai/assetgen/` is code that makes assets — deterministic, parameterised, ours by authorship, with no
licence question at all. It already covers the sound set (`sfx.py`) and the low-rune medallions (`symbols.py`).
Anything *systematic* — a set that must share one construction, a frame that must tile, a sound that must sit in a
budget — belongs there rather than in a model. Keep the models for the painted hero shots they are good at.

## Caveats

1. **Licence ≠ regulatory clearance.** None of these licences mention gambling, and no gambling-specific clause was
   found in OpenRAIL++-M or the Apache models — "not found", not "confirmed absent". MGA/UKGC obligations around
   game-art provenance, and disclosure of AI-generated content in some jurisdictions, are a compliance question.
2. **Keep the provenance log.** Record per asset which model, which version, which licence. If we ever have to prove
   no FLUX-dev-derived art shipped, that log is the only way to do it. `generated/*/manifest.json` already does this
   for the generators; do the same for anything a model paints.
