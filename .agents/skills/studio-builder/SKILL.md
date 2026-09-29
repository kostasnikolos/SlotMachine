---
name: studio-builder
description: Defines the workflow for the Studio Builder, focusing on WebGL implementation, Three.js pipelines, and headless Playwright snapshot capture.
---

# Studio Builder Guidelines

The Studio Builder implements the technical architecture defined by the Planner. You write the WebGL/Three.js code and generate verification snapshots for the Reviewer.

## Headless Rendering Pitfalls (CRITICAL)

When capturing Three.js canvases using Playwright (`headless: true`), you must avoid the following common failure modes:

1. **Browser Caching (The "Identical Snapshot" Loop)**:
   - Playwright heavily caches `.js` and texture files across runs if the URL remains the same.
   - **Fix**: ALWAYS append a dynamic timestamp to your HTML file injections. Never hardcode `?v=999`. 
   - Example Python fix: `html = re.sub(r'\?v=\d+', f'?v={int(time.time())}', html)` before running the capture script.

2. **Pitch Black / Grey Renders**:
   - Happens when materials fail to compile (e.g., missing shaders, texture load failure) or lights are not configured.
   - **Fix**: Use a `THREE.LoadingManager` and wait for `manager.onLoad` before firing `window.__RENDER_READY = true`. Ensure dynamic lights (Key/Rim) have sufficient intensity.

3. **Blown-out / White Shaders**:
   - Happens when PointLight intensity is set astronomically high (e.g., 50,000) while `THREE.ACESFilmicToneMapping` is enabled, causing Math NaN crashes in the GPU.
   - **Fix**: Keep light intensities reasonable (e.g., 1.0 to 10.0) when Tone Mapping is active.

4. **The "Bubble Wrap" Texture Bug**:
   - When mapping textures onto large procedural geometries like `THREE.ExtrudeGeometry`, default UV mapping stretches 1 unit of texture to 1 unit of world space. If your frame is 30 units wide, repeating the texture `(1, 1)` will stamp it 30 times, making rocks look like tiny bubble-wrap.
   - **Fix**: Scale down texture repeats significantly for large objects: `texture.repeat.set(0.05, 0.05)`.

5. **Invisible GPU Deformations**:
   - If injecting custom vertex shaders via `onBeforeCompile`, remember that Three.js caches materials. Dynamic uniforms might not update unless you force material updates or pass uniforms via attributes.
   - **Fix**: For static headless snapshots demonstrating physics, you can fallback to `mesh.scale.set()` to visibly prove squash-and-stretch to the Reviewer.
