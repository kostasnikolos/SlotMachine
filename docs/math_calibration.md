# Math calibration — The Descent

Scope: `slot_engine/config/weights.py`, `slot_engine/config/symbols.py` (paytable, depth thresholds,
natural free-spin awards), `slot_engine/config/rtp_profiles.py`, `slot_engine/simulation/monte_carlo.py`,
`scripts/math_check.py`. No engine logic (`state_machine.py`, `ways_evaluator.py`, `grid.py`, `creature.py`,
`vents.py`) and nothing under `slot_engine/static/` was changed.

## The problem

As the depth levels purged low symbols, the old weight tables filled the freed probability mass with
`DEAD_SEDIMENT` blockers: 110 / 150 / 200 weight at Levels 3 / 4 / 5, i.e. 48% of the cells in a Standard
Bonus and 67% of the cells in the Ultra Bonus were empty sediment. The owner's rule is that a purged low's
seat goes to a *higher-paying symbol*, with sediment at most a rare blocker (<= 5% of cells at any level).

The old model was also uncalibrated: base game 57% RTP at 77% hit frequency with a 36x max win and
no natural descent (Level 1 reached on 0.1% of spins, Level 3 never), Standard Bonus 117% of its 100x price,
Ultra Bonus 40% of its 350x price.

## Targets and assumptions

* Target RTP 96.05% (`rtp_profiles.py`, profile `default`).
* **Assumption (industry norm): every feature buy returns the same 96.05%, measured against its own price**:
  xBet 2x, Standard 100x, Ultra 350x, Mystery 200x (60% Standard / 40% Ultra, so 0.6*100 + 0.4*350 = 200;
  Mystery is therefore automatically on target when Standard and Ultra are). This is now recorded as
  `FEATURE_BUY_COSTS` / `feature_rtp_target()` in `rtp_profiles.py`.
* Max win cap 15,000x bet, unchanged.
* High volatility: most buys return well under their price, the top of the distribution is rare and large.

## Results: before / after

Measured with `scripts/math_check.py --full` (gate seeds 11-88: 800k base rounds, 160k xBet, 24k Standard,
20k Ultra, 20k Mystery) pooled with the calibration harness on independent seeds 1-16 (800k base, 320k xBet).
RTP is expressed as % of the mode's own cost; the +/- is one standard error of the pooled estimate.

| Mode | Cost | RTP before | RTP after | Hit freq after | Max win after (x bet) | Sediment share before | after |
|---|---|---|---|---|---|---|---|
| Base game (NONE) | 1x | 57.2% | **97.4%** (±1.0; gate 98.2, harness 96.6) | 30.7% (49.4% before crush depth) | ~3,400x | 0% | 0% at L0, 0.5% of all base cells |
| XBET_SONAR_2X | 2x | 85.6% | **94.8%** (±1.5; gate 92.6, harness 95.9) | 76.3% | ~2,900x | 0.04% | 1.9% |
| STANDARD_BONUS_100X | 100x | 114.7% | **95.8%** (±1.1) | 100% | ~4,200x (42x cost) | 47.8% | 2.1% |
| ULTRA_BONUS_350X | 350x | 36.6% | **95.2%** (±0.5) | 100% | 15,000x cap (1 in 20k rounds) | 67.3% | 3.0% |
| MYSTERY_BUY_200X | 200x | 61.5% | **96.6%** (±0.7) | 100% | ~4,900x | 56.3% | 2.5% |

"Before" figures come from the original `monte_carlo.py` runs of the same seeds (3 x 15k base, 3 x 6k xBet,
3 x 1.2k per bonus). The latest full-gate table is kept in `artifacts/math_gate_full.txt` /
`artifacts/math_gate_full.json`.

Depth reach per round after calibration:

| Mode | L0 | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|---|
| Base | 95.3% | 1.8% | 0.9% | 1.67% | 0.32% | 0.04% |
| xBet | — | 90.3% | 4.6% | 4.7% | 0.35% | 0.04% |
| Standard buy | — | — | — | 41% | 47% | 12% |
| Ultra buy | — | — | — | — | — | 100% |

Where the base RTP comes from: flat Level-0 pays ~1.5 pts, Level 1-2 descents ~0.5 pts, natural Level 3-4
rounds ~79 pts, natural Level 5 rounds ~15 pts. The base game is feature-driven: 61% of spins lose,
37% pay under 1x, 1.9% of spins (the descents) carry the RTP, and the largest observed base wins are
2,000-3,200x. The `default` profile budgets in `rtp_profiles.py` were updated to this measured split.

## Final weights per level

Weights are relative integers; compare shares within a level. `DEAD_SEDIMENT` share of *generated cells*
is measured by the gate (L1 2.0%, L2 2.0%, L3 2.1%, L4 2.2%, L5 3.5% max; limit 5%).

| Symbol | L0 (x32 scale) | L1 (x8 scale) | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|---|
| LOW_10 | 384 | 0 | 0 | 0 | 0 | 0 |
| LOW_J | 384 | 112 | 0 | 0 | 0 | 0 |
| LOW_Q | 384 | 104 | 16 | 0 | 0 | 0 |
| LOW_K | 384 | 104 | 15 | 11 | 0 | 0 |
| LOW_A | 384 | 96 | 14 | 11 | 13 | 0 |
| MID_HELMET | 320 | 112 | 16 | 12 | 14 | 21 |
| MID_COMPASS | 320 | 104 | 15 | 12 | 14 | 19 |
| HIGH_VIPER | 288 | 64 | 9 | 13 | 15 | 17 |
| HIGH_ANGLER | 256 | 56 | 8 | 13 | 14 | 16 |
| HIGH_SQUID | 160 | 40 | 6 | 12 | 13 | 14 |
| HIGH_LEVIATHAN | 96 | 24 | 3 | 10 | 12 | 10 |
| WILD_MAW | 67 | 9 | 2 | 4 | 5 | 1 |
| DEAD_SEDIMENT | 0 | 16 | 2 | 2 | 2 | 3 |
| *sediment share* | 0% | 1.9% | 1.9% | 2.0% | 2.0% | 3.0% |

Share by class: L0 lows 56% / mids 19% / highs+apex 23% / wild 2.0%; L5 mids 40% / highs 47% / apex 10% /
wild 1% / sediment 3%.

### Paytable (x bet per way)

| Symbol | 3 | 4 | 5 | 6 |
|---|---|---|---|---|
| HIGH_LEVIATHAN | 0.0135 | 0.0405 | 0.135 | 0.27 |
| HIGH_SQUID | 0.0081 | 0.0216 | 0.0675 | 0.135 |
| HIGH_ANGLER | 0.0054 | 0.0135 | 0.0405 | 0.081 |
| HIGH_VIPER | 0.00405 | 0.0108 | 0.027 | 0.054 |
| MID_COMPASS | 0.00216 | 0.0054 | 0.0135 | 0.027 |
| MID_HELMET | 0.00162 | 0.00405 | 0.0108 | 0.0216 |
| LOW_A | — | 0.0027 | 0.0081 | 0.0162 |
| LOW_K | — | 0.00216 | 0.00675 | 0.0135 |
| LOW_Q | — | 0.00162 | 0.0054 | 0.0108 |
| LOW_J | — | 0.00135 | 0.00405 | 0.0081 |
| LOW_10 | — | 0.00108 | 0.00324 | 0.00675 |

Depth thresholds (pressure points): L1 6, L2 13, L3 24, L4 100, L5 200 (were 15 / 35 / 65 / 160 / 260).
Natural free spins on level-up: L1 +2, L2 +2 (were +1 each), L3 +2, L4 +2, L5 +4 (unchanged).
Vent multiplier odds, pearl odds, bought-bonus spin counts (6 / 8) and the 15,000x cap are unchanged.

## What changed and why

1. **Sediment removed as filler (the owner's rule).** Every level's table is now a distribution over the
   *surviving paying symbols*; sediment is 0 at Level 0 and 2-3% at depth, where it still reads as the
   "silt that adjacent wins blow away" without acting as a brake on the math.

2. **Near-flat spreads at depth, not a steep pyramid.** On a 5-row ways grid a symbol with 30% weight is
   present in a reel 83% of the time, so a mid-heavy Level 5 never stalls: every refill wins again and
   every Ultra round runs into the 15,000x cap (measured: 73% of rounds capped). The cascade only stalls
   when each symbol is individually rare per reel, which means spreading the mass evenly over the 6-8
   survivors. The pyramid is kept gently (mids >= highs >= apex, wild small) and the *paytable* carries the
   value difference between symbols.

3. **Paytable rescaled (x0.027 of the old shape, lows pay from 4 reels).** The Ultra round (6 reels,
   7,776 ways, 2x global multiplier, 2x2 Leviathan wild each spin, vents on 3 reels) is the strongest
   state the engine can be in; its EV per spin fixes the paytable scale for the whole game. Removing the
   3-of-a-kind pay from the five low runes is what holds the base hit rate under 50% (3-reel low pays give
   ~77% on 5 rows).

4. **Depth thresholds lowered and L1/L2 descents give 2 spins.** This is the one lever outside the
   "weights, then paytable" order and it is flagged deliberately. With the Ultra fixing the paytable
   scale, a flat Level-0 spin is worth ~1.5% RTP; no weight table gets the base game to 96% without wilds so
   dense that every spin pays. The only honest source of base RTP is the designed mechanic itself, the
   natural descent, which the old thresholds (15 points when a winning combo earns 1-3) made unreachable.
   With 6 / 13 / 24 / 100 / 200 the base game descends to Level 3+ on 2.0% of spins and to the Ultra
   on 0.05%; a bought Standard Bonus climbs to Level 4 ~48% and ascends to Level 5 ~12% of the time, which
   is also what gives the Standard buy its top end. Thresholds are served by `/api/slot/paytable`, so the
   depth gauge in the front end follows automatically.

5. **xBet balanced against the base.** xBet (start at Level 1 with the Lurker armed) is extremely
   sensitive to the Level 1 wild share and to the L1->L2 gap (1.5 units -> 112%, 1.25 -> ~100%,
   1.125 -> ~95%); it is set to 1.125 wild units at Level 1 so that it returns ~2x the base EV for 2x the price.

6. **Tooling.** `monte_carlo.py` now prints ASCII only (UTF-8 reconfigured), takes `--seed`, emits `--json`,
   and reports sediment share per level, free spins per round and the per-round standard deviation.
   `scripts/math_check.py` is the gate.

## The gate

```
set PYTHONIOENCODING=utf-8                  (Git Bash: export PYTHONIOENCODING=utf-8)
python scripts/math_check.py                fast, ~20 s: 200k base, 40k xBet, 5k per bonus buy, seeds 11..88
python scripts/math_check.py --full         ~90 s: 800k base, 160k xBet, 24k/20k/20k bonus buys
python scripts/math_check.py --api http://127.0.0.1:8080
                                            live: checks the server runs this config, buys one ULTRA round,
                                            counts every dealt cell, fails if DEAD_SEDIMENT > 5%
```

Exit code 1 when a mode is outside +/-2 pts of 96.05% (window widened by 2 standard errors of the per-seed
spread, both printed, so the gate is deterministic without being flaky on the feature-driven modes), when
sediment exceeds 5% of generated cells at any level, or when a round exceeds the cap. Run it after every
change to `slot_engine/config/*` or `slot_engine/core/*`.

### Crush depth (2026-11-06): base hit frequency 49% → 30.7%

`slot_engine/config/features.py` `CRUSH_DEPTH_ENABLED` / `CRUSH_THRESHOLD_X = 0.01`: a base-game round that never leaves the
Sunlight Zone and returns less than 1% of its stake is crushed (`PRESSURE_CRUSH` event, payout 0). Measurement that
justified it: 44% of base rounds paid under 0.1× the stake (dust from the ×0.027 paytable scale), so the 49% "hit rate" was
mostly cents. At 0.01× the crush voids 19% of rounds; full gate after: base 98.09% (unchanged to the decimal: the crushed
cash is < 0.1 pt), hit 30.66%, every buy unchanged. The dial: 0.015× → 24%, 0.02× → 20%.

The pressure multiplier (B) and the bite retrigger (C) are implemented behind flags in the same file and **switched off**:
measured on the current weights, B at +0.5×/level sends the base to 239% and Standard to 105%; C at a 20% chance (cap 4)
sends the base to 279% and Ultra to 116%; even B 0.25/level cap 2 with C 5% cap 2 gives base 196%. The cause is structural:
~80% of the base RTP sits in the 2% of rounds that descend to Level 3+, so anything that scales deep rounds scales the RTP.
Turning them on needs the descent frequency rebalanced (thresholds up, deep weights down) and a full re-pin: its own job.

### The pinned baseline (added 2026-11-06)

`artifacts/math_baseline.json` holds every mode's RTP, hit frequency and max win from the fast gate (fixed seeds 11–88).
Because the seeds are fixed, an unchanged engine reproduces those numbers to the third decimal; any drift above 0.05 pts
means the math changed. Two automatic runs: the GitHub Actions job `.github/workflows/math-gate.yml` on every push or
pull request that touches `slot_engine/config`, `slot_engine/core`, `slot_engine/simulation` or the gate; and the local
pre-commit hook `.githooks/pre-commit` (enable once per clone with `git config core.hooksPath .githooks`). A deliberate
recalibration re-pins in the same commit: `python scripts/math_check.py --write-pin artifacts/math_baseline.json`, and
this document's results table is updated.

## Trade-offs and remaining risks

* **Base hit frequency is 49%, not the 25-32% aspiration.** It is a property of the grid, not of the
  weights: with 11 symbols on 5 rows the chance that *some* symbol lands on reels 1-3 is ~45% even with
  perfectly flat weights and no 3-reel low pays. Getting to ~30% needs either 3-4 rows, 15+ symbols, or
  blockers at Level 0 (which the owner's rule forbids). What the calibration does instead is make those
  hits almost all sub-1x (37% of spins) so they read as "the reels moved", while the real wins are the
  descents. If 49% is unacceptable the clean fix is a row/symbol change in the engine, not a weight change.
* **Base and xBet are high-variance (std dev ~13x and ~9x per round).** 200k spins measure them to
  +/-3 pts, 800k to +/-1.5 pts; the fast gate can show a +/-3 pt swing between seed sets that is noise, not
  drift (the gate seeds read base 98.2 / xBet 92.6, the harness seeds 96.6 / 95.9 on the same config).
  Use `--full` before signing off a config, and treat the pooled numbers (97.4 / 94.8) as the best estimate:
  both are within ~1 SE of 96.05, i.e. the model is on target to the resolution a 1M-spin simulation has.
* **Bonus top end is modest.** Standard buys return <= 1x their price 73% of the time and 1-5x 25%;
  >5x (500x bet) is ~0.03%, and the Ultra reaches the cap only ~1 in 20,000 rounds. The engine has no
  retrigger, sticky-multiplier or progressive mechanic inside a bonus, so the long tail comes only from
  the Maelstrom / vent compounding and from ascension. Adding one of those would be the next step for a
  "rare 500x+" feel inside buys.
* **Weights at L0 / L1 use x32 / x8 integer scales** because the wild share has to be tuned in
  fractions of a unit (2.09 and 1.125). Doubling `WILD_MAW` at Level 0 from 2 to 3 units moves the base RTP
  from ~92% to ~168%, so treat that cell as the most dangerous number in the config.
* **Only the `default` profile is calibrated.** `regulatory_94` and `promo_966` carry targets but share
  the same weights/paytable; they need their own paytable scale (roughly x0.98 and x1.006) before use.
* **Pearl ascension** is left at 0.1% per cell and contributes negligibly; it is a tunable reserve.
* The thresholds and +2 spins at L1/L2 change how often the front end plays level-up choreography in the
  base game (Level 1 on 1.7% of spins instead of 0.1%). This was verified only in simulation, not visually.
