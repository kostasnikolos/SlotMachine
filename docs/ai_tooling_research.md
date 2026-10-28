# AI Tooling Research (2026-10-28)

Findings that shape the pipeline. Model ids change every few months — re-check with `python scripts/ai/gemini_generate.py --list-models`.

## Google tools
- **AI Studio / Build mode** writes web apps (could prototype Three.js scenes). It does **not** produce 3D meshes or game assets.
- **Genie 3 / Project Genie**: explorable worlds, US-only, AI Ultra, no API, no export. Reference only.
- **Flow** (absorbed Whisk/ImageFX): image + video studio. **Stitch**: UI design.
- **No Google text/image-to-3D** exists.
- **Imagen 4 was shut down 2026-08-17.** Veo 3.1 preview ids were shut down 2026-10-22; video is now `gemini-omni-1.1-flash`.

## Image models available to our key
`gemini-nano-banana-2.1` (default, cheapest good), `gemini-3.1-flash-image`, `gemini-3-pro-image` (hero pieces), `gemini-omni-1.1-flash` (video).
- Up to 10–14 reference images per call (6 on Pro) — the main style-consistency lever.
- No alpha output: generate on flat black, matte afterwards. SynthID watermark on all output.
- **API free tier: image models unavailable (quota 0). Billing required.**
- Paid, 2K image: Nano Banana 2.1 ≈ $0.05 ($0.025 Batch); 3 Pro ≈ $0.134. ~150 keepers ≈ $12–25 on Nano Banana with Batch.
- Google AI Pro includes Developer Program premium with ~$10/month Cloud credit usable on the API (must be activated).

## 3D
Meshy 6, Tripo v3.1, Rodin Gen-2.5 (~$0.18–0.25/call, GLB/FBX PBR); TRELLIS 2 (MIT, self-host). Meshes lose the painterly look → at most one hero mesh baked to 2D. Not core.

## Techniques adopted (impact ÷ effort)
1. Style-referenced Nano Banana 2.1 batches → automatic matting → palette grade.
2. Offline depth maps (Depth Anything V2; mind the CC-BY-NC Base checkpoint) → parallax shader on backdrop and Leviathan.
3. AI normal maps (Marigold Normals, Apache-2.0) → relight painted symbols with the moving bioluminescent key light.
4. AI-written GLSL atmosphere: caustics, marine snow, fog, god rays.
5. Omni first/last-frame clips → sprite sheets, only for Leviathan reveal and big win.

Rejected: Gaussian splats (size, look), real-time 3D as core art.

## Claude skills
- obra/superpowers: process only, nothing visual — skip for art.
- anthropics/skills `frontend-design`: borrow for HUD chrome.
- cloudai-x/threejs-skills (MIT): shaders, post-processing, lighting — candidate for the Builder.

## How studios work
Public signal: 2D painted art + Spine animators + JSON exports. AI used for concept/exploration ("AI explores, artists own the result"). No public evidence of generative AI at Nolimit, Pragmatic, Push or Hacksaw.
