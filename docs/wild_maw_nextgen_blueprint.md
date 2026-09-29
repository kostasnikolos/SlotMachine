# Wild Maw Next-Gen WebGL Blueprint

## Overview
Technical blueprint for upgrading the `sym_wild_maw` into a Next-Gen WebGL asset capable of breaking the frame, aligning with the `studio-planner` guidelines.

## Technical Requirements
- **Materials:** Multi-layer PBR materials for separate mesh planes (Background, Midground, Foreground).
- **Shaders:** Custom GLSL shaders for vertex displacement (Vertex Breathing).

## Advanced Techniques
1. **Multi-Layer Parallax:**
   - **Background (Void):** Distant void environment.
   - **Midground (Teeth/Maw):** Main anatomical structure.
   - **Foreground (Saliva/Bubbles):** Transparent overlays reacting to movement.
2. **Vertex Breathing:**
   - Custom GLSL shader applied to the Midground.
   - Slow sinusoidal displacement on the vertices to simulate a pulsing, breathing jaw in the Idle state.
3. **Breaking the Frame:**
   - Win state animation.
   - Z-index manipulation to bring the symbol forward.
   - Mesh scales up 1.5x.
   - Jaws physically break the grid bounding box, overlapping adjacent columns.

## Milestones & Acceptance Gates

### Milestone 1: Multi-Layer Parallax Setup
- **Action:** Split `sym_wild_maw` into Background, Midground, and Foreground planes with assigned PBR textures.
- **Acceptance Gate:** Snapshot showing depth separation between the three layers from a slightly offset camera angle. The Foreground saliva must correctly render transparency over the Midground.

### Milestone 2: Vertex Breathing Shader Implementation
- **Action:** Implement custom GLSL shader for vertex manipulation on the Midground mesh.
- **Acceptance Gate:** Sequential snapshots showing the min and max states of the vertex expansion (pulsing jaw) without texture tearing.

### Milestone 3: Break the Frame Animation
- **Action:** Implement the Win state logic (scale up 1.5x, Z-index boost).
- **Acceptance Gate:** Snapshot of the grid during a Win state where the `sym_wild_maw` clearly overlaps adjacent symbol boundaries and sits visually closer to the camera.
