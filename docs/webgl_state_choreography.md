# WebGL State Choreography Blueprint
## The Descent: Abyssal Leviathan

This document serves as the definitive master blueprint for the Builder to implement the unified Monolithic WebGL Stage choreography, outlining the 8 distinct WebGL states.

### State 1: The Abyssal Idle
- **Condition**: Base state, waiting for player input.
- **Effects**: Volumetric fog rolling across the Z-depth. Breathing shaders on high-tier symbols.
- **Lighting**: Ambient abyssal glow.

### State 2: Spin Initiation
- **Condition**: Player initiates spin.
- **Effects**: Motion blur applied to reels. Z-axis camera pullback for anticipation.
- **Kinematics**: Rapid vertical acceleration.

### State 3: Base Hit
- **Condition**: Winning combination lands.
- **Effects**: Squash/stretch physics on landing, harmonic bounce.
- **Lighting**: Localized point lights ignite behind winning symbols.

### State 4: Near Miss / Tension
- **Condition**: Waiting for crucial scatter/bonus symbol on final reels.
- **Effects**: Pitch black stage, glowing 5th reel. Camera zoom on the tension reel.

### State 5: Big Win / Frame Breaker
- **Condition**: High multiplier win.
- **Effects**: Z-axis eruption—symbols scale by 1.5x, overlapping the monolithic frame.

### State 6: Sinking Progression
- **Condition**: Collection events or progressive meter filling.
- **Effects**: Fluid dissolve shaders for collection, particles flowing into the sculpted UI seals.

### State 7: Singularity Breach
- **Condition**: Bonus entry transition.
- **Effects**: Black hole distortion shader sucking the grid and frame into a singularity point.

### State 8: The Abyssal Descent / Level-Up Purge
- **Condition**: Advancing to deeper levels.
- **Effects**: Pressure crush implosion on low-pay symbols. Leviathan sweep across the background. Wilds are anchored violently to the grid.
