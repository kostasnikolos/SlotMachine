---
name: slot-3d-visual-engine
description: >-
  Comprehensive engineering framework and toolkit for building studio-grade 3D WebGL
  visual engines for online slot games (inspired by Nolimit City, Print Studios, and Push Gaming).
  Use whenever designing, scaffolding, or implementing 3D rigged character/monster animations,
  unhinging creature jaws, squash-and-stretch reel physics, GLSL screen-space fluid refraction shaders,
  normal-mapped symbol lighting, and audio-reactive screen impacts.
---

# Studio-Grade 3D Slot Visual Engine (Nolimit City Architecture)

This skill provides the complete architecture, procedures, and templates for engineering high-volatility, commercial-grade 3D visual engines for online slots. It bridges the gap between flat HTML/DOM prototypes and the visceral, hardware-accelerated aesthetic pioneered by **Nolimit City** (*Beheaded*, *Blood & Shadow 2*, *San Quentin*, *Das xBoot*) and **Push Gaming** (*Razor Shark*).

---

## 1. Core Architecture

A commercial studio slot engine decouples the system into three coordinated layers:

```
┌────────────────────────────────────────────────────────┐
│ 1. HTML/CSS Cockpit HUD (Porthole, Radar, Bet Controls) │
└──────────────────────────┬─────────────────────────────┘
                           │ Dispatches timeline events
┌──────────────────────────▼─────────────────────────────┐
│ 2. Unified WebGL 3D Viewport (Three.js GPU Engine)     │
│    ├── Perspective Camera (FOV 45-50°, 3D tilt)        │
│    ├── Articulated 3D Monster Rig (Bones, Jaws, Lure)  │
│    ├── 3D Symbol Reels (Squash & stretch physics)      │
│    ├── Dynamic Lighting & Level Fog Color Grading      │
│    └── GLSL Fluid Refraction & Chromatic Aberration    │
└──────────────────────────┬─────────────────────────────┘
                           │ Audio-visual synchronization
┌──────────────────────────▼─────────────────────────────┐
│ 3. Procedural Web Audio Engine (Sub-bass, hydrophones) │
└────────────────────────────────────────────────────────┘
```

---

## 2. Key Visual Pillars & Runbook

### Pillar 1: Unified WebGL Scene (Zero DOM Tiles)
Never render slot symbols as HTML `<div>` or `<img>` elements when studio fidelity is required. DOM elements cannot share lighting, normal maps, or perspective depth with 3D characters.
- Render all symbols on **3D Box / Plane Meshes** inside a Three.js scene.
- Position the camera at $(0, 0, 480)$ with $FOV \approx 48^\circ$, focused on $(0, 0, 0)$.

### Pillar 2: The Articulated 3D Creature Rig
A mascot, demon, or deep-sea monster must feel alive throughout idle, anticipation, and attack states:
1. **Bone Kinematics**:
   - Spine chain: 12–16 trailing vertebrae moving on a sine-wave damping curve.
   - Cranium & Jaw: Upper skull fixed; lower jaw bone pivots down $0^\circ \to 75^\circ$ forward on an unhinge axis.
   - Fangs: Double rows of conical teeth with high specular gloss (`roughness: 0.1, metalness: 0.4`).
   - Lure / Eye: Emissive glow meshes paired with dynamic Three.js `PointLight` that illuminates the reels.
2. **Animation State Machine**:
   - `IDLE`: Swims/drifts in deep Z-space ($Z \approx -220$), undulating smoothly, breathing, with lure swaying.
   - `ANTICIPATION`: When cascades chain or bonus spins trigger, coils back into shadows, spines flare.
   - `STRIKE(coords)`: Surges forward through the water to $Z = +30$ directly over target cells, jaw unhinges wide, clamps down with crunch bite, emits water cavitation particles, transmuting symbols before receding.
   - `ROAR`: Heads-up toward camera porthole, jaws snap wide, camera shakes with sub-bass audio sync.

### Pillar 3: Squash-and-Stretch Reel Kinematics
Studio slots never drop symbols with rigid linear motion:
- **Falling**: Velocity stretch along Y-axis (`scale.y = 1.18, scale.x = 0.90`).
- **Landing**: Heavy impact squash (`scale.y = 0.82, scale.x = 1.12`).
- **Recovery**: Damped spring harmonic oscillation to rest (`scale = 1.0`).

### Pillar 4: Screen-Space GLSL Refraction & Shockwaves
Normal-map fluid displacement shaders make impacts visceral:
- Explosions and jaw chomps emit a radial shockwave uniform that physically warps the pixels of the underlying reels through pressurized viewport glass.
- Chromatic aberration splits RGB channels on heavy hits.

---

## 3. Step-by-Step Implementation Guide

When creating or upgrading a slot with this engine:

1. **Include Three.js in `index.html`**:
   ```html
   <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
   ```

2. **Scaffold the 3D Viewport**:
   - Copy or adapt the modular template: [webgl_viewport.template.js](./templates/webgl_viewport.template.js)
   - Add the canvas to the viewport container:
     ```html
     <div id="viewport-frame">
       <canvas id="webgl-slot-canvas"></canvas>
     </div>
     ```

3. **Instantiate the Rigged Creature**:
   - Use [creature_rig_3d.template.js](./templates/creature_rig_3d.template.js) to configure cranium, jaw, fangs, and spinal trailing segments.

4. **Connect Event Timeline in Client Controller**:
   Hook math state machine events to 3D calls:
   ```javascript
   case 'GRID_DROP':
     await viewport3D.dropReels(ev.data);
     break;
   case 'CREATURE_LIFELINE_STRIKE':
     await viewport3D.creature.strikeAt(ev.data.transmuted);
     break;
   case 'LEVEL_UP':
     viewport3D.setAtmosphere(ev.data.new_level);
     break;
   ```

5. **Apply Mobile Responsive Sizing**:
   Ensure `PerspectiveCamera.aspect` and `renderer.setSize` resize smoothly on window/orientation change.

---

## 4. Reusable Templates & Reference Files

- [Nolimit City Visual Architecture Study](./references/nolimit_visual_architecture.md): Full breakdown of *Beheaded*, *Blood & Shadow 2*, and *Das xBoot*.
- [WebGL Viewport Template](./templates/webgl_viewport.template.js): Complete Three.js scene controller with lighting, camera, and reel matrix.
- [3D Creature Rig Template](./templates/creature_rig_3d.template.js): Articulated creature model with jaw hinge and spine kinematics.
- [Fluid Refraction Shader](./templates/fluid_refraction.frag.glsl): GLSL screen-space displacement shader.
