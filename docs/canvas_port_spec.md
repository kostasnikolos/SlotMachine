# Canvas → Game port spec

**Target look:** the Design canvas "The Descent: Abyssal Leviathan" (https://claude.ai/artifact/Qh5cU4RMbQ4KRmAsLPGpvB), board `Main.dc.html` (1920×1080, Director bar) + `Levels.dc.html` (depth-level spec). The user chose it over the current game and over stage_v2. The real game (`slot_engine/static/index.html` + `game.js` + `js/WebGLGameEngine.js`) keeps its math, API flow, audio and the grid/feel fixes; its **look** moves to the canvas.

**Method:** every step lands behind `?look=canvas` first (default unchanged), gets captured next to the canvas, and is reviewed before it becomes the default. A local copy of the canvas source and its assets is in the scratchpad folder `artifact-files/bfdac82b-6d4c-46e3-8783-526585ee3b40/` (read-only reference).

## What the canvas is made of

| Layer | Canvas implementation | Game equivalent |
| --- | --- | --- |
| Type | Chakra Petch (HUD) + JetBrains Mono (numbers) | Cinzel / Orbitron / Rajdhani → replace |
| Accent | one `--a` rgb var (default `63,245,255` bioluminescence); orange `#ff7a1a` = wins/features; crimson `#ff2a4b` = deep levels | several hard-coded hexes → one var |
| Ground | `#000307`, panels `linear-gradient(rgba(1,4,8,.86), rgba(0,1,3,.94))` + `backdrop-filter: blur(10px) brightness(.6)`, 1px border `rgba(var(--a),.09)`, radius 14, **corner brackets** (`.c.tl/.tr/.bl/.br`, 18px, 2px, glow) | `abyssal_trench_bg.jpg` wrapper with hue-rotate per depth |
| Layout 1920×1080 | header 88px (logo left, Director centre, sound/rules/menu right) · left panel 330×796 @48,120 (depth number 52px mono + zone name + "abyss column" canvas) · frame @top 104, h 812, p 19, 5×5 grid gap 8 inside 772px, top chip (`.chip`) · right panel 330×796 (radar 160 + lifeline creature card + pressure gauge canvas + icon row: multiplier, pearls, vents) · footer 130px (wallet left · bet pill + 132px round spin + auto/turbo centre · xBet + Buy right) | header bar, two cockpit sidebars, HUD banner, control bar |
| Grid | `.cell` glass tiles (`rgba(0,4,8,.42)`, border `rgba(var(--a),.07)`, radius 8), `.cell.win` orange pulse, `.cell.dim` 0.32; symbols drawn on a WebGL canvas over the cells from **PBR atlases** (albedo/normal/emissive/aux, 4×4 of the same medallion symbols the game already has) | DOM cells + separate WebGL symbol layer (already aligned by `alignToCells()`) |
| Background | `data-lev` canvas: GLSL fog/caustics/depth; Leviathan = 3D mesh (geo JSON + PBR jpgs) drifting behind, strike animation; `data-levfx` particles | ocean_ambient.js fish/bubbles + leviathan_3d_engine.js |
| Overlays | level-up (`.lu`: 120px depth, name, rewards chips), feature (`.feat`), strike card, undertow water, big win (`.bwfront` ladder, 3D bw canvas, slam/jitter), buy modal (4 `.bcard`), scanlines, `.hud.shake` | HUD banner + CSS classes |
| Depth styling | `.hud.d3/.d4/.d5` → redder borders, chroma text, flicker; Levels board gives per-level bg gradients, shafts, vents, walls, eyes, cracks | `#game-wrapper.depth-N` hue-rotate filters |

## Steps (each behind `?look=canvas` until reviewed)

1. **Chrome:** fonts, `--a` var, ground, panels with corner brackets, header/footer/sidebars re-laid to the canvas geometry (responsive below 1600: same rules as today). Spin button 132px ring. Scanlines toggle. No change to symbols or background yet.
2. **Grid frame + cells:** `.frame` + `.cell` glass tiles, win pulse/dim states mapped to the game's existing win/cascade classes, top chip (ways / free spins).
3. **Instruments:** left abyss column (depth canvas), right radar + lifeline + pressure gauge, icon row — driven by the game's real `updateDepthProgress`, purge and multiplier events.
4. **Depth atmosphere:** per-level palette from `Levels.dc.html` replacing hue-rotate; `.d4/.d5` red regime.
5. **Overlays:** level-up, feature, big-win ladder (reuse `feel_director.js` tiers), buy modal.
6. **Background + Leviathan:** port the `data-lev` shaders and the mesh (assets: geo JSON `100d5105…`, `21dd5801…`, `b2ac6177…`; base/normal/mr/emissive jpgs listed in the canvas) into the game's background layer.

## Gate for each step
G5 cohesion and G6 parity are judged **against the canvas screenshot**, not against Nolimit references. Plus: default (`no flag`) pixel parity with `artifacts/current_game_desktop.png` (re-capture that baseline after the grid fix), feel checks still PASS, mobile 390 still usable.
