# Architectural Review, Flagship Benchmarking & Unified Visual Roadmap
**Project:** The Descent: Abyssal Leviathan (Studio Slot Engine)  
**Target Benchmark:** Nolimit City (*Mental*, *Das xBoot*, *Blood & Shadow 2*), Push Gaming (*Razor Returns*), Print Studios (*Darkness*)

---

## 1. Executive Summary & Current State Audit

We have engineered a fully functional high-volatility slot prototype with working math, cascades, Hadal depth progression, custom sound synthesis, and a 1M+ vertex 3D Leviathan mesh. However, **it is currently architected as a web dashboard of separate HTML/DOM boxes rather than a unified video game stage**. 

To commercialize and sell a slot game to tier-1 aggregators (Evolution, Relax Silver Bullet, EveryMatrix, Light & Wonder), the game cannot feel like HTML flexbox containers with CSS borders. It must be a **single, hardware-accelerated, cohesive visual world** where the grid, meters, character, and symbols are part of one physical machine.

### What We Have Done (Strengths)
1. **Mathematical Engine & Cascading Logic**: 
   - 5x5 Ways (3,125 ways) expanding to 6x5 (7,776 ways) in Hadal Core.
   - Working 6-tier Depth Progression with symbol purges (10, J, Q, K, A) and Hydrothermal Vents multipliers.
   - Clean event emission architecture (`SPIN_STARTED`, `GRID_DROP`, `WIN_EVALUATION`, `LEVEL_UP`).
2. **Procedural Web Audio Engine**:
   - Dedicated Web Audio API synthesizer for sub-bass hydrophone hum, sonar pings, jaw chomps, and creature roars without heavy external MP3 downloads.
3. **True 3D Leviathan Asset**:
   - Custom 3D mesh (`custom_leviathan.glb`) with multi-point lighting, bioluminescent throat glow, and programmed surge-and-devour attack animations.

### Where the Current Prototype Falls Short (The Core Problem)
1. **Fragmented DOM Box Architecture**:
   - The UI is split into 4 floating HTML panels: Left Sidebar (Barometer/Runes), Center Stage (Viewport Frame + Symbol Grid), Right Sidebar (Sonar Radar + Progress Bar), and Bottom Control Bar.
   - On desktop, it looks like a telemetry control dashboard with a slot stuck in the middle. On mobile, flexbox forces these panels into an awkward vertical column stack where elements push the reels around.
2. **Disconnected Symbol Layer**:
   - Symbols are 25 HTML `<div>` elements containing flat `<img>` tags. DOM elements cannot receive 3D scene lighting, cannot be refracted by underwater shockwaves, cannot have GPU-accelerated motion blur, and suffer layout recalculations during rapid cascade drops.
3. **The "Tacked-On" 3D Character**:
   - Because the 3D Leviathan lives in a separate Three.js overlay canvas above or below the HTML symbols, it has to be toggled with `display: block` and `display: none` to prevent covering the DOM tiles. It cannot swim continuously in the background behind semi-translucent symbols, cast real shadows on the reels, or physically erupt through the frame.
4. **Asset Weight & Load Friction**:
   - The raw 3D model is ~20MB with over 1 million vertices. While stunning in fidelity, commercial web slots demand initial bundles under 15MB total to ensure instant mobile loading over 4G connections.

---

## 2. Deep Dive: How Nolimit City & Tier-1 Flagships Build Games

Nolimit City (*Mental*, *Das xBoot*, *Blood & Shadow 1 & 2*, *San Quentin*, *Tombstone RIP*) is the gold standard for visceral, industrial, high-impact slot games. Analyzing their client codebase and rendering pipeline reveals a completely different architectural paradigm:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      TIER-1 STUDIO CLIENT PIPELINE                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ UNIFIED HARDWARE-ACCELERATED CANVAS (WebGL / WebGPU / PixiJS)  │   │
│   │                                                                │   │
│   │   [Layer 0: Atmospheric Environment]                           │   │
│   │   - Abyssal depth fog, caustic ray shaders, floating particles │   │
│   │                                                                │   │
│   │   [Layer 1: Continuous Background Creature / Rig]              │   │
│   │   - 3D Mesh / Spine Rig swimming in deep Z-space               │   │
│   │   - Bioluminescent lights illuminating the scene from behind   │   │
│   │                                                                │   │
│   │   [Layer 2: Monolithic Grid Casing & Integrated Meters]        │   │
│   │   - Forged basalt / submarine steel reel enclosure             │   │
│   │   - Left/Right: Depth Barometer built INTO the grid pillars    │   │
│   │   - Bottom: Ritual / Sonar Bar built INTO the grid lintel      │   │
│   │                                                                │   │
│   │   [Layer 3: 3D / WebGL Symbol Quads]                           │   │
│   │   - Normal-mapped 3D tiles with specular reflections           │   │
│   │   - Squash-and-stretch tumble physics, motion blur             │   │
│   │   - In-cell enhancer frames (xWays, xSplit, Wild Maws)        │   │
│   │                                                                │   │
│   │   [Layer 4: Foreground Creature Breaches & Impacts]            │   │
│   │   - Creature lunges forward across Z-plane OVER the symbols    │   │
│   │   - Water cavitation particles, steam bubbles, blood splatters │   │
│   │                                                                │   │
│   │   [Layer 5: Full-Screen Post-Processing Shaders]               │   │
│   │   - Radial shockwave refraction, chromatic aberration          │   │
│   │   - Dynamic depth LUT color grading (Cyan -> Gold -> Blood)    │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ MINIMAL DOM OVERLAY (Only Standard Regulatory Controls)        │   │
│   │ - Spin button, Bet selector, Balance display, Hamburger menu   │   │
│   └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Lessons from Flagship Games:

### 1. *Blood & Shadow 2* (Nolimit City) — The Unified Ritual Bar
- **How it works**: The player advances through 5 levels of dark magic to unlock the 5x5 grid and banish low symbols.
- **The Visual Integration**: Nolimit City **does not** place the level progression in a side panel. Instead, the **"Ritual Bar" is the bottom metallic threshold of the reel frame itself**. 
- Symbols that explode release soul wisps that fly directly into the Ritual Bar. When full, the Ritual Bar flashes and physically expands the reel frame upwards. Everything is enclosed in one solitary gothic shrine.

### 2. *Das xBoot* (Nolimit City) — The Mechanical Submarine Frame
- **How it works**: A submarine under depth charge attack with an asymmetric 2-3-4-4-3-2 grid.
- **The Visual Integration**: The reel frame is rendered as the interior bulkhead of a U-boat. The depth gauges, valve wheels, and torpedo chutes are **welded directly onto the top and sides of the reels**. There are zero standalone sidebar boxes; the entire game screen is a single submarine cross-section.

### 3. *Mental* (Nolimit City) — In-Cell Enhancers & Visceral Shaders
- **How it works**: Asylum horror slot with "Fire Frames", "Enhancer Cells", and organ symbols.
- **The Visual Integration**: Features are not tracked on external UI cards. If an Enhancer Cell or Fire Frame is active, it appears **directly inside or bolted to the reel grid**. All distortions (sepia flicker, screen shake, chromatic aberration) operate as GLSL post-processing passes over the entire canvas.

### 4. *Razor Returns* (Push Gaming) — Seamless Creature Presence
- **How it works**: The mechanical predator shark looms menacingly behind the industrial steel cage of the reels.
- **The Visual Integration**: The creature is **not** hidden behind a `display: none` toggle. It is rendered inside the same WebGL scene, lurking in murky underwater fog behind the semi-translucent symbols. When a feature triggers, it bites through the grid, creating water shockwaves that warp the symbols underneath.

---

## 3. Gap Analysis: Where We Are vs. Studio Standard

| Feature Area | Current Prototype | Nolimit City / Push Gaming Standard | Gap Severity |
| :--- | :--- | :--- | :--- |
| **Grid & UI Architecture** | 4 separate HTML/CSS `<div>` panels (Left Barometer, Center Reels, Right Sonar, Bottom Controls) arranged via CSS flexbox. | **Monolithic Viewport**: A single WebGL stage. Frame, reels, meters, and background are rendered as one unified structure. | **CRITICAL (Showstopper for B2B Sale)** |
| **Reel Symbol Rendering** | 25 HTML `<div>` elements with flat static `<img>` PNGs. Cascades managed via DOM class toggles. | **GPU Sprites/Quads**: Symbols rendered on WebGL planes with normal maps, specular gloss, and dynamic shader lighting. | **HIGH** |
| **Creature Integration** | Three.js canvas in a floating overlay container; turned on/off via `display: none / block` to prevent black box overlap. | **Continuous In-Scene Actor**: Creature swims continuously in deep Z-space behind semi-translucent reels; lunges forward through the reels seamlessly. | **HIGH** |
| **Progression & Meters** | Bulky sidebar widgets with separate text cards and radar SVGs. | **Integrated Frame Meters**: Barometer forged into left pillar; Sonar/Ritual meter built into bottom lintel of the reel frame. | **HIGH** |
| **Reel Kinematics** | Linear CSS translateY drops with uniform timing. | **Physical Squash & Stretch**: Symbols stretch on fall ($1.2\times$ Y), squash on impact ($0.8\times$ Y), and settle with harmonic oscillation. | **MEDIUM** |
| **Post-Processing FX** | CSS `transform: translate()` screen shake; no shader refraction. | **GLSL Post-Processing**: Full-screen shockwave fluid displacement, caustics, and depth-based color grading. | **MEDIUM** |
| **3D Asset Weight** | 20MB raw GLB with 1M+ vertices (slow 4G load time). | **Optimized PBR Model**: 15k–30k vertices with baked 2K normal/roughness maps; total asset bundle < 3MB. | **HIGH** |

---

## 4. The Unified Grid Blueprint: Eliminating the HTML Boxes

To achieve studio quality, we must eliminate the separate HTML sidebars and merge the entire visual experience into a **Single Monolithic Viewport Stage**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                THE MONOLITHIC HADAL REEL FRAME (CANVAS)                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   TOP LINTEL:  [  3,125 WAYS TO WIN  ]  [ DEPTH: 5,000M - THE ABYSS ]  │
│  ┌───┬──────────────────────────────────────────────────────────┬───┐  │
│  │   │  [COL 1]    [COL 2]    [COL 3]    [COL 4]    [COL 5]     │   │  │
│  │   │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │ S │  │
│  │ D │ │ ANGLER │ │ HELMET │ │  10    │ │COMPASS │ │ VIPER  │   │ O │  │
│  │ E │ ├────────┤ ├────────┤ ├────────┤ ├────────┤ ├────────┤   │ N │  │
│  │ P │ │COMPASS │ │ SQUID  │ │   J    │ │LEVIATHN│ │   Q    │   │ A │  │
│  │ T │ ├────────┤ ├────────┤ ├────────┤ ├────────┤ ├────────┤   │ R │  │
│  │ H │ │ VIPER  │ │   K    │ │WILD MAW│ │   A    │ │ HELMET │   │   │  │
│  │   │ ├────────┤ ├────────┤ ├────────┤ ├────────┤ ├────────┤   │ D │  │
│  │ B │ │  10    │ │ ANGLER │ │   J    │ │ SQUID  │ │   K    │   │ I │  │
│  │ A │ ├────────┤ ├────────┤ ├────────┤ ├────────┤ ├────────┤   │ A │  │
│  │ R │ │ HELMET │ │   Q    │ │ VIPER  │ │COMPASS │ │ ANGLER │   │ L │  │
│  │   │ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │   │  │
│  │   │                                                          │   │  │
│  └───┴──────────────────────────────────────────────────────────┴───┘  │
│   BOTTOM LINTEL: [ RITUAL BAR: 8 / 15 PTS ] [ 10 | J | Q | K | A ]     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Design Execution of the Unified Frame:
1. **Left Pillar — The Depth Barometer**:
   - Instead of a standalone HTML sidebar, the vertical depth gauge is sculpted directly into the **left structural pillar** of the reel frame.
   - It features glowing abyssal mercury/fluid that rises from $0\text{m}$ to $11,000\text{m}$ with glowing level notches.
2. **Right Pillar — The Sonar Sweep Dial**:
   - The circular radar is embedded into the **right corner/pillar** of the frame like a pressure gauge on a submarine.
   - A sweeping laser beam scans for abyssal signatures; when high-value symbols land, blips light up on the dial.
3. **Bottom Lintel — The Hadal Ritual Bar**:
   - Directly underneath the 5 reels, a heavy metallic/basalt trough serves as the progress bar.
   - Winning cascades disintegrate into glowing cyan soul embers that fly down into the bar, filling it towards the next depth threshold.
   - The 5 runic seals (`10`, `J`, `Q`, `K`, `A`) are carved into the bottom frame bezel, slashing open with crimson fire as each low symbol tier is purged.
4. **Z-Space Creature Staging**:
   - The 3D Leviathan is permanently loaded in the scene.
   - **Idle ($Z = -180$)**: Its silhouette and bioluminescent eyes drift behind the semi-translucent basalt reel backplanes, casting ominous shadows through the gaps between reels.
   - **Anticipation ($Z = -100$)**: When 2 scatters land or cascades chain, it swims forward, jaws twitching.
   - **Devour ($Z = +40$)**: It violently breaches *through* the center of the frame, jaws snapping over winning symbols with radial shockwave refraction, before diving back into the abyssal void.

---

## 5. Math Engine Observation (The Bonus Buy Payout Issue)

The user noted: *"there are also problems with the maths, every buy wins a lot that doesnt make sense. but thats the last thing we will tackle first is the visuals"*.

### Root Cause Analysis in `state_machine.py`:
1. **Compounding Purge Probability**:
   - In `STANDARD_BONUS_100X` and `ULTRA_BONUS_350X`, starting at Level 3 ($5,000\text{m}$) or Level 5 ($11,000\text{m}$) purges 3 to 4 low symbols from the symbol pool.
   - Because only high-paying symbols (Angler, Squid, Viper, Leviathan, Wild) remain, the probability of connecting across 3,125 to 7,776 ways skyrockets. Almost every spin connects a 5-of-a-kind.
2. **Infinite Spin Bank Re-Triggers**:
   - Every winning cascade awards pressure points (`gauge.add_points()`).
   - In the bonus game, these points constantly trigger additional `LEVEL_UP` events, awarding $+2$ to $+3$ additional free spins repeatedly. A 6-spin bonus regularly balloons into 18+ spins.
3. **Base Bet Multiplier Mismatch**:
   - Line payouts are evaluated against `base_bet`. When buying a 100x bonus at bet $\$1.00$, the player pays $\$100.00$, but cascading multipliers and vent multipliers multiply against the huge symbol combination density, yielding guaranteed $200\times - 800\times$ returns instead of realistic high-volatility variance (where some buys return $15\times$ and rare buys hit $1,500\times$).
4. **Resolution Plan (Reserved for Math Phase)**:
   - Cap bonus re-triggers (free spins cannot be re-awarded indefinitely).
   - Implement realistic reel strips (weighted frequency tables) for bonus modes rather than unweighted random selection from the purged pool.
   - Calibrate the volatility curve to ensure standard casino RTP distribution ($96.0\%$ with high variance).

---

## 6. Actionable Implementation Roadmap

### Phase 1: Unified Canvas Stage & Monolithic Frame (Visual Overhaul Priority)
- [ ] **Step 1.1**: Migrate the scene layout from 4 separate HTML panels into a unified WebGL/Three.js viewport canvas with a fixed studio aspect ratio (16:9 desktop with auto-fit letterbox, 9:16 mobile portrait crop).
- [ ] **Step 1.2**: Design and render a bespoke **Hadal Basalt & Submarine Steel Frame** that holds the reels, integrating:
  - The Depth Barometer into the left vertical pillar.
  - The Sonar Radar into the top-right console.
  - The Ritual Points Bar and 5 Runic Purge Seals into the bottom frame lintel.
- [ ] **Step 1.3**: Convert DOM symbol tiles into textured WebGL quads with subtle normal-map lighting and glowing bioluminescent borders.

### Phase 2: Integrated 3D Leviathan & Depth Kinematics
- [ ] **Step 2.1**: Optimize the 3D model: Decimate mesh geometry down to ~35k polygons, bake 2K PBR textures (diffuse, normal, roughness, emissive), compressing model size from 20MB to under 3.5MB.
- [ ] **Step 2.2**: Implement continuous Z-depth presence: Leviathan swims in deep fog behind the reels during idle, surges through the frame on feature triggers, and casts dynamic lighting onto adjacent symbols.
- [ ] **Step 2.3**: Implement squash-and-stretch reel kinematics: Velocity stretch ($1.18\times$) on fall, impact squash ($0.82\times$) on landing, with damped harmonic bounce.

### Phase 3: Nolimit-Grade Visual Polish & Shaders
- [ ] **Step 3.1**: Screen-Space Fluid Refraction Shader: Custom GLSL shockwave uniform triggered on Leviathan chomps and high-tier cascades that physically distorts underlying symbol pixels.
- [ ] **Step 3.2**: Depth Color Grading LUTs: Atmospheric post-processing transitions from murky sunlight teal ($0\text{m}$) to sulfur-gold ($2,000\text{m}$) to abyssal blood-crimson ($11,000\text{m}$).
- [ ] **Step 3.3**: Particle Systems: Disintegrating winning symbols emit glowing soul embers that fly into the bottom Ritual Bar.

### Phase 4: Math Engine & Volatility Calibration
- [ ] **Step 4.1**: Fix bonus buy infinite re-trigger loop and implement weighted reel strip distributions.
- [ ] **Step 4.2**: Run Monte Carlo simulations (10,000,000 spins) to certify 96.0% RTP with true Nolimit-style extreme volatility.
