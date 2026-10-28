# Architecture

## Overview

```
browser (descent/index.html + app.js)
   │  POST /api/slot/spin {bet, feature_buy}         or
   │  POST /api/slot/buy-bonus {bet, feature_type}
   ▼
FastAPI (slot_engine/api/app.py)
   ▼
SlotStateMachine.execute_spin()  ──►  outcome: total_payout, win_x_base_bet, final level, events[]
```

The engine decides everything. The frontend only plays back the `events` list in order. It never changes a result.

## Engine (`slot_engine/core`)

| Module | Role |
|---|---|
| `state_machine.py` | Runs one round: the base spin, cascades, level-ups, free spins, features and the max-win cap. Emits the event timeline. |
| `grid.py`, `ways_evaluator.py` | Grid fill from the reel weights, and left-to-right ways evaluation. |
| `progression.py` | Pressure points, depth level thresholds, symbol purging and spins awarded per level. |
| `creature.py` | The Leviathan lifeline strike on dead spins (wild footprints get larger with depth). |
| `vents.py` | Hydrothermal vent column multipliers (Abyss and deeper, on winning steps only). |
| `undertow.py` | The Undertow help: a 1×2, 2×1 or 2×2 block sinks and is refilled, then the tumble is re-evaluated. It always runs after the lifeline. |
| `rng.py` | The single RNG (`SlotRNG`), including `weighted_choice`. |

**Event types:**
- `SPIN_STARTED`, `GRID_DROP`, `WIN_EVALUATION`, `CASCADE_DROP`
- `LEVEL_UP`, `CREATURE_LIFELINE_STRIKE`, `UNDERTOW`, `VENTS_ERUPTED`, `PEARLS_COLLECTED`
- `ULTRA_ASCENSION_ACHIEVED`, `FEATURE_ACTIVATED`, `GRID_EXPANSION_6X5`, `MAX_WIN_CAP_TRIGGERED`, `SPIN_COMPLETE`

**Configuration** (`slot_engine/config`):
- `symbols.py`: paytable (scaled ×0.96 in the 96% rebalance), pressure points, `DEPTH_LEVEL_THRESHOLDS`, `DEPTH_METADATA` and `GAME_RULES`.
- `weights.py`: reel and refill weights, including `UNDERTOW_SYMBOL_WEIGHTS`.
- `rtp_profiles.py`: RTP targets and budgets.

**Testing.** Change the maths only together with a simulation run, and keep `tests/` green.

## Frontend

The **source of truth** is `slot_engine/static/descent/design/Main.dc.html`, a Claude Design canvas artboard. It has three parts:
- a template with `{{holes}}`, `<sc-for>` and `<sc-if>`;
- a `<helmet>` with the CSS;
- a `class Component extends DCLogic` whose `renderVals()` feeds the template.

`scripts/descent/dc_to_web.py` turns that file into `slot_engine/static/descent/index.html` and `app.js` (htm/Preact). The build:
- swaps `/_blob/<id>` canvas assets for files in `static/assets/descent/` (the `ASSETS` map);
- replaces the local engine call with `fetchRound()` to the API. The built-in JS engine copy (`engRound`) stays as an offline fallback;
- hides the Director QA bar unless the URL has `?director=1`;
- appends a `?v=<sha>` cache-buster to `app.js`.

It can also build a work copy: `--src <file> --out <folder under slot_engine/static>`.

### Layers

The page is stacked canvases plus DOM, from back to front:

| Canvas | Contents |
|---|---|
| `data-lev` | Background |
| `data-lev3d` | The Three.js Leviathan |
| `data-levfx` | Leviathan effects |
| `data-wbg` | Reel water (work copy only, see below) |
| `data-sym` | The WebGL symbol renderer |
| `data-fx` | Particles |
| `data-bw3d` / `data-bwfx` | The big-win 3D fall and its effects |
| `data-abyss`, `data-gauge`, `data-creature`, `data-hudfx` | HUD |

How each part is rendered:
- **Symbols.** Four atlases: albedo, normal, emissive and aux (`build_symbol_atlas.py`). Lantern lighting, breathing, dissolve and ripple uniforms.
- **Leviathan.** A Tripo mesh (`build_leviathan.py`) bent along a swim spine in the vertex shader, with a rigid head and a jaw hinge for the bite strike. Per-level palettes come from `defs().vis`.
- **Audio.** Fully procedural Web Audio in `makeAudio()`. It starts on the first tap.
- **Big wins.** `celebrate()` and `bwFrame()`. See [big_win_and_sound_design.md](big_win_and_sound_design.md).

### Choreography

`spin()` fetches a round, then walks its events:
- drops and cascades;
- `strikeSeq` for the lifeline;
- `undertowSeq`;
- level-up overlay, vents and pearls;
- finally the big-win tier if the win is above the stake.

Waits use `nextFrame()` / `waitK()`, so hidden tabs and slow frames don't desync audio from animation.

## Work in progress (`slot_engine/static/work/`)

Larger changes are built by parallel builder agents, each on its own copy of `Main.dc.html`. Copies are then three-way merged into the design with `git merge-file` against the snapshot they started from, reviewed, and rebuilt.

| Copy | Status |
|---|---|
| `water/` | **Done, not merged.** One continuous water shader (`wbgShaders` / `wbgSetup` / `wbgFrame`) behind the reels, in place of boxed glass cells. Caustics, sockets with contact shadows, and win light that pools between adjacent winners. |
| `telegraph/` | **Unfinished.** Undertow and Leviathan help telegraphs without boxes: an organic whirlpool and foam in place of the orange strike box. |
| `creature/` | **Unfinished.** Leviathan realism: detail texture, wet specular, shadows and AO, face fixes, slower swimming. |
| `audio/`, `bigwin/`, `bigwin3d/`, `hud/`, `jaw/`, `undertow/` | Earlier rounds, already merged. Kept for reference. |

## Roadmap

1. Finish and merge `telegraph` and `creature`, merge `water`, review, rebuild.
2. **Near-miss anticipation.** The pressure meter shudders when the player is close to the next level.
3. **Bioluminescent bloom.** Random multiplier spores on symbols.
4. **Redo the left depth column** (the "Sunlight Zone" shaft), which currently looks flat.

Open minor items:
- The L5 gauge stays full.
- The radar calls `setState` too often.
