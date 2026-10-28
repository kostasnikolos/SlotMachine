# UNDERTOW — helping feature

On a **dead tumble** (no wins), a 1×2, 2×1 or 2×2 block of symbols is dragged under the water and fresh symbols surface in its place. The tumble is then re-evaluated, so a win may follow. It works in the base game and in the bonus, at 5×5 and 6×5.

## Rules (engine: `slot_engine/core/undertow.py`, `state_machine.py`)
- **Ordering:** the Leviathan lifeline always acts first. The undertow can only answer a dead tumble when no lifeline is armed: at Level 0, or after the lifeline has been spent this spin. It can trigger at most `undertow_max_per_spin` (1) times per spin. Every free spin counts separately.
- **Chance per eligible dead tumble:** `GAME_RULES["undertow_chance"]`
  - `base` 0.13: paid spin at Level 0
  - `deep` 0.05: paid spin at Level 1–4 (xBet, or after a level-up)
  - `bonus` 0.125: free spins or bought bonus at Level 1–4
  - `core` 0.25: any spin at Level 5
- **Block shape weights:** `undertow_block_weights` = {1x2: 35, 2x1: 35, 2x2: 30}. A block never contains a wild or a multiplier cell. If no such block fits, nothing happens.
- **Replacement symbols:** drawn from `weights.UNDERTOW_SYMBOL_WEIGHTS`, which leans toward mids and highs and makes wilds rare.
  - Symbols purged at the current depth are excluded.
  - The symbol that just sank is excluded, so every cell visibly changes.
  - Pearl tokens stay on their cells.
- **No RNG use at chance 0:** when a chance is 0, no random number is drawn, so a disabled undertow reproduces the old seeded results exactly.
- **Event:** `UNDERTOW` = `{block: {position: [r, c], size: [h, w]}, swapped: [{coord, old_symbol, new_symbol}], grid}`.
- **Existing events:** their shapes are unchanged.

## RTP retune
Every paytable value is now **×0.96** of the previous 96% ladder (rounded to 4 decimal places). I then solved the four chances so that each mode lands back at about 96%. Measurements use the 1.0 base bet; ± is one standard error.

| Mode | Before (no undertow) | After (×0.96 pays + undertow) | Undertows per round |
|---|---|---|---|
| Base | 96.11 ±0.24 (3M) | 96.15 ±0.25 (3M)* | 0.15 |
| xBet 2× | 95.99 ±0.45 (1M) | 95.71 ±0.47 (1M) | 0.10 |
| Standard 100× | 95.92 ±0.36 (60k) | 95.64 ±0.36 (60k), 95.98 ±0.37 (60k)* | 0.97 |
| Ultra 350× | 95.48 ±0.28 (25k) | 96.28 ±0.22 (40k) | 2.0 |

\* Measured with `deep` = 0.07 and `core` = 0.21, before the final tweak of those two values. Base and Standard depend on them only slightly.

Roughly 18% (base) to 30% (Ultra) of undertows lead straight into a win.

Sensitivity for retuning: each extra 0.1 of chance adds about +3 pts in Base (`base`), +6 pts in xBet (`deep`), +2.5–3 pts in Standard (`bonus`) and +2 pts in Ultra (`core`). The gain per 0.1 is steeper at low chances.

## Frontend (`static/work/undertow/Main.dc.html`)
- **Engine copy:** `undertowDefs` / `engUndertowRoll` / `engUndertow` mirror the Python rules, and `engRound` emits `UNDERTOW` in the same place as the engine.
- **Presentation:** `playEvent` `case 'UNDERTOW'` calls `undertowSeq`, which runs in about 2.8 s:
  1. The screen shakes and the block is highlighted.
  2. Water rises over the block, with a ripple and spray.
  3. The symbols sink.
  4. A foam overlay covers the block.
  5. The new symbols surface.
- **Director:** an **UNDERTOW** button plays the sequence on the current grid.
