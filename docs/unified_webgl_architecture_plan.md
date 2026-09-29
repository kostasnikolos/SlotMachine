# The Descent: Abyssal Leviathan - Pure Canvas Engine Architecture Plan

## 1. Single Canvas Architecture & Unified WebGL Stage
The core mandate is a total elimination of HTML/DOM elements for gameplay and UI. The engine will utilize a **Monolithic WebGL Stage** with a single `<canvas>` element filling the viewport.
- **Scene Graph:** A single Three.js scene containing all game elements (reels, symbols, backgrounds, UI overlays).
- **Camera System:** A locked studio camera that handles both 16:9 desktop (auto-fit) and 9:16 mobile (crop/scale) seamlessly without DOM media queries.
- **Lighting & Depth:** 5 dynamic light sources illuminating a continuous Z-depth stage. The 3D Leviathan sits in the deep background, reels in the mid-ground, and UI in the foreground.

## 2. PBR Texture Pipeline
To avoid a flat "cardboard cutout" look, all 2D symbol assets must be converted to a full PBR (Physically Based Rendering) suite:
- **Base Color:** The core symbol graphic.
- **Sobel Normal Map:** For surface bump and light interaction.
- **Roughness / Metalness:** To differentiate materials (e.g., metallic diving bells vs. organic tentacles).
- **Emissive Glow:** For active win lines and scatter/bonus triggers.

## 3. Monolithic Frame Integration & In-Canvas UI System
All HTML sidebars and buttons are replaced by 3D integrated elements within the scene:
- **Depth Barometer:** Sculpted into the left structural pillar of the frame.
- **Sonar Sweep:** Integrated into the top-right console.
- **Ritual Progress Bar & Runic Seals:** Built directly into the bottom lintel.
- **Controls & HUD:**
  - Spin button: A circular 3D disc or textured plane in the bottom-right.
  - Bet controls & Balance: Integrated into the bottom panel.
  - Bonus Buy Modal & Big Win Splash: Rendered as dynamic 3D overlay planes that fade into the foreground.

## 4. In-Canvas Input Handling (Raycasting)
User interactions will be purely handled through the canvas:
- `canvas.addEventListener('pointerdown')` (and `pointerup`/`pointermove`) to capture raw screen coordinates.
- **Raycasting:** Use `THREE.Raycaster` to project clicks into the 3D scene and intersect with UI bounding boxes/planes.
- Custom event dispatcher to route interactions to the Spin, Bet, and UI logic controllers.

## 5. Text Rendering (Dynamic CanvasTextures)
Text (balance, bet amount, win amounts) cannot rely on HTML fonts.
- Use an off-screen HTML5 2D canvas to draw text.
- Pass this 2D canvas into `THREE.CanvasTexture`.
- Apply the texture to 3D planes for dynamic, crisp text that correctly interacts with scene lighting and z-indexing.

## 6. Reel Kinematics & Shaders
- **Squash-and-Stretch:** Vertex shaders applied to symbol meshes during reel spin for motion blur and velocity physics.
- **Landing Harmonics:** Spring-based procedural animation when reels lock into place.
- **Fluid Refraction Shockwaves:** Screen-space post-processing shaders that trigger on Leviathan strikes or major scatter landings, rippling across the entire canvas.

## 7. Migration Strategy & Snapshot Review Gates (Multi-Phase Execution)
Inspired by Nolimit City and Push Gaming architectures, migration will occur in strict phases:

### Milestone 1: UI Sprite System & Raycaster Foundations
- Implement the unified WebGL scene and 2D canvas text rendering.
- Recreate Spin, Bet, Balance, and Win displays as in-scene sprites/planes.
- Implement raycaster-based pointer event handling.
- **Gate:** Visual snapshot verification of interactive UI elements inside the canvas before proceeding.

### Milestone 2: Monolithic Frame & PBR Pipeline Integration
- Integrate the Depth Barometer, Sonar Sweep, and Runic Seals into the 3D frame.
- Upgrade the 25 symbol quads to use the full PBR Texture Pipeline.
- Wire game logic to the new in-canvas controls.
- **Gate:** Snapshot review of lighting, PBR materials, and layout integration across both aspect ratios (16:9 and 9:16).

### Milestone 3: Kinematics, Shaders & DOM Purge
- Implement squash-and-stretch vertex shaders and landing harmonics.
- Add screen-space shockwave post-processing.
- Strip all HTML DOM gameplay elements from `index.html`. Only `<html><body><canvas id="game"></canvas><script src="..."></script></body></html>` remains.
- **Gate:** Final full-gameplay snapshot review verifying engine stability and zero DOM interference.
