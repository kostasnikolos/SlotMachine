# The Descent: Abyssal Leviathan - Unified WebGL Architecture & Engine Merge Plan

## 1. PBR Texture Pipeline
- **Objective:** Transform flat 2D symbol JPGs into full PBR texture suites to give symbols true 3D surface depth under dynamic lighting, completely avoiding flat "cardboard cutout" visuals.
- **Pipeline:** Base Color -> Sobel Normal Map -> Roughness/Metalness -> Emissive Glow.

## 2. Unified WebGL Stage Architecture (`WebGLGameEngine.js`)
- **Core Module:** Create `WebGLGameEngine.js` to encapsulate the Three.js scene.
- **Stage Properties:**
  - Single Three.js scene with a locked studio camera.
  - Responsive layouts: 16:9 desktop (auto-fit) and 9:16 mobile crop.
  - 25 GPU symbol quads mapped to a 5x5 plane grid.
  - 5 dynamic light sources to interact with PBR textures.
  - Continuous Z-depth staging for the 3D Leviathan creature rig.
- **Audio Integration:** Imports `AudioController.js` to synchronously trigger audio cues based on WebGL state transitions.

## 3. Monolithic Frame Integration
- **Goal:** Eliminate disconnected HTML sidebars and unify the UI into the 3D environment.
- **Sculpted UI Layout:**
  - **Depth Barometer:** Sculpted seamlessly into the left pillar.
  - **Sonar Sweep:** Integrated into the top-right console.
  - **Ritual Progress Bar & 5 Runic Purge Seals:** Baked directly into the bottom lintel of the stage.

## 4. SlotGame Data Flow Integration (`game.js`)
- **Refactoring `SlotGame`:** Remove all legacy HTML `div` creation, tracking, and CSS manipulation from the slot grid.
- **Data Transmission:** `SlotGame` will pass raw 2D array grid data, cascade updates, and win line configurations directly to `WebGLGameEngine`.
- **Decoupling:** The WebGL engine acts as a pure rendering view layer that reacts to the mathematical model emitted by `SlotGame`.

## 5. Reel Kinematics & Shaders
- **Physics:** Implement squash-and-stretch vertex physics for spin start/stop momentum.
- **Animation:** Landing harmonic bounce for heavy symbols.
- **Visual Effects:** Screen-space fluid refraction shockwaves upon creature strikes and cascade hits.

## 6. Event Mapping to WebGL States
The slot engine events from `game.js` map directly to our cinematic WebGL states:
- **Spin Start (`this.spin()`):** Triggers **State 2 (Spin/Descend)**.
- **Cascade Data Received:** Triggers **State 3 (Hit/Squash)** with fluid refraction shockwaves.
- **Level Up (Depth Increase):** Triggers **State 8 (Purge)** leading directly into **State 6 (Sink/Transition)**.
- **Idle / Awaiting Input:** **State 1 (Ambient Abyss)**.
- **Big Win / Feature Trigger:** Triggers **State 5 (Leviathan Strike)**.

## 7. Multi-Phase Execution & Snapshot Review Gates
This 3-Milestone plan ensures safe refactoring and prevents regressions, with mandatory visual snapshot verification at each gate.

### Milestone 1: Scene Initialization & PBR Setup
- **Tasks:**
  - Create `WebGLGameEngine.js`, initializing Three.js camera, dynamic lights, and renderer.
  - Build the PBR Texture Pipeline and render the 25 symbol quads.
  - Integrate the Monolithic Frame elements (Barometer, Sonar, Ritual Seals).
- **Review Gate 1:** Snapshot verification of the static 5x5 grid with PBR symbols and monolithic frame UI in both 16:9 and 9:16 aspect ratios.

### Milestone 2: Data Flow & Reel Kinematics
- **Tasks:**
  - Refactor `game.js` to strip HTML DOM updates and pass data arrays directly to `WebGLGameEngine`.
  - Implement squash-and-stretch vertex shaders and landing harmonic bounce.
- **Review Gate 2:** Snapshot/Video verification of a single spin cycle demonstrating successful data ingestion, reel kinematics, and symbol landing physics.

### Milestone 3: State Mapping, Creature Rig & Audio Integration
- **Tasks:**
  - Import and hook up `AudioController.js`.
  - Map all slot events to the corresponding WebGL states (States 1-8).
  - Implement the 3D Leviathan Z-depth staging and screen-space fluid refraction shockwaves for cascading hits.
- **Review Gate 3:** Snapshot/Video verification of a full cascade sequence with a Leviathan strike, triggering a Level Up (Purge/Sink states), fully synchronized with audio.
