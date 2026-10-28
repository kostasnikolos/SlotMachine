# The Descent: Abyssal Leviathan

A high-volatility deep-sea horror slot. It has two parts:

- **Python engine (FastAPI).** Owns all maths and randomness. It returns each round as a timeline of events.
- **WebGL / Three.js frontend.** Plays those events back: lit 3D symbols, a Leviathan creature, big-win screens and procedural sound.

The target RTP is about 96% (`default` profile) and the maximum win is 15,000× the bet.

## Quickstart

```bash
pip install -r requirements.txt
```

```bash
python3 -m uvicorn slot_engine.api.app:app --host 127.0.0.1 --port 8090 --reload
```

Then open:

| URL | What it is |
|---|---|
| http://127.0.0.1:8090/ | The game |
| http://127.0.0.1:8090/?director=1 | The game plus the Director bar, a QA tool that forces levels, strikes, Undertow and big wins |
| http://127.0.0.1:8090/docs | The API's Swagger docs |
| http://127.0.0.1:8090/legacy | The old frontend |

Run the tests with:

```bash
python3 -m pytest tests/ -v
```

## The game

- **Grid.** 5×5 ways (3,125). It expands to 6×5 (15,625 ways) at the Core.
- **Cascades.** Winning symbols dissolve, and new ones drop in.
- **Pressure.** Every win adds pressure points.
- **Depth levels.** Pressure drives the player down six levels:

  | Level | Depth | Points needed |
  |---|---|---|
  | Sunlight | 0 m | 0 |
  | Twilight | 500 m | 15 |
  | Midnight | 2,000 m | 80 |
  | Abyss | 5,000 m | 225 |
  | Hadal | 8,000 m | 585 |
  | Core | 11,000 m | 1,130 |

  Each new level removes a low symbol and awards spins.
- **Leviathan lifeline.** On a dead spin, the creature strikes the grid and leaves wilds behind.
- **Undertow.** A block of 2 or 4 symbols sinks under foam, and new symbols surface in its place. See [docs/undertow_feature.md](docs/undertow_feature.md).
- **Hydrothermal vents.** These add column multipliers.
- **Pearls.** Collecting enough pearls in a round ascends straight to the Core.
- **Bets and buys:**

  | Option | Cost | What it does |
  |---|---|---|
  | xBet | 2× | Starts at Twilight with 55 points |
  | Standard bonus | 100× | Abyss, 6 spins |
  | Mystery | 200× | Standard or Ultra; Ultra 40% of the time |
  | Ultra bonus | 350× | Core, 6×5 grid, 8 spins, 2× global multiplier |
- **Big wins.** Tiers start at 50×: DEEP WIN, CRUSH DEPTH (100×), LEVIATHAN WIN (500×), HADAL WIN (1,000×) and THE ABYSS (max). A win at or below the stake is never celebrated (UKGC RTS 14F).

The authoritative numbers live in `slot_engine/config/symbols.py`, `weights.py` and `rtp_profiles.py`.

## Repository layout

| Path | What it holds |
|---|---|
| `slot_engine/api/app.py` | FastAPI app: `/api/slot/spin`, `/api/slot/buy-bonus`, `/api/slot/paytable`, `/api/slot/health`; serves the frontend |
| `slot_engine/core/` | Engine: state machine, grid, ways evaluator, depth progression, creature lifeline, vents, Undertow, RNG |
| `slot_engine/config/` | Paytable, pressure points, level thresholds, rules, reel weights, RTP profiles |
| `slot_engine/static/descent/design/Main.dc.html` | **The frontend source of truth**, a Claude Design canvas artboard |
| `slot_engine/static/descent/index.html`, `app.js` | **Generated** from the design file. Never edit these by hand |
| `slot_engine/static/assets/descent/` | Symbol atlases and the Leviathan mesh and textures |
| `slot_engine/static/work/` | Builder work copies of the design that are not merged yet (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)) |
| `scripts/descent/` | Build and asset pipeline: `dc_to_web.py`, `build_symbol_atlas.py`, `build_leviathan.py`, `pose_preview.py` |
| `tests/` | Engine, API and Undertow tests |
| `docs/` | Design notes and feature docs |

The many `fix_*.py`, `debug_*.py`, `check_*.py`, `test_*.py` and `measure_*.py` files at the repo root are one-off scripts from earlier iterations. They are kept for history and are not part of the build.

## Editing the frontend

1. Edit `slot_engine/static/descent/design/Main.dc.html`.
2. Rebuild:

   ```bash
   python3 scripts/descent/dc_to_web.py
   ```

3. Reload the page. The script adds a `?v=hash` cache-buster to `app.js`.

The build:
- converts the artboard template to htm/Preact;
- maps canvas asset ids to `/static/assets/descent/`;
- swaps the built-in JS engine copy for calls to the Python API. The copy stays as an offline fallback.

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): how the engine, event timeline, frontend and build fit together, and the current work in progress.
- [docs/undertow_feature.md](docs/undertow_feature.md): Undertow rules and maths.
- [docs/big_win_and_sound_design.md](docs/big_win_and_sound_design.md): big-win tiers, skip rules, sound design and research.
- Older planning notes: `docs/*_plan.md`, `docs/studio_visual_review_and_roadmap.md`, `docs/walkthrough.md`.
