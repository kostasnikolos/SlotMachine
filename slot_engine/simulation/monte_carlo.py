"""Headless Monte Carlo RTP & Volatility Simulator for The Descent."""

import argparse
import json
import sys
import time
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from slot_engine.config.symbols import DepthLevel, FeatureBuyType, SymbolType
from slot_engine.core.state_machine import SlotStateMachine
from slot_engine.core.rng import SlotRNG
from slot_engine.config.rtp_profiles import FEATURE_BUY_COSTS


# Cost of each mode in multiples of the base bet (used to express RTP per its own price).
FEATURE_COST_MULTIPLIER: Dict[FeatureBuyType, float] = FEATURE_BUY_COSTS


@dataclass
class SimulationReport:
    spins_run: int
    total_bet: float
    total_payout: float
    measured_rtp: float
    hit_frequency: float
    max_win_observed: float
    max_win_multiplier: float
    caps_triggered: int
    elapsed_seconds: float
    spins_per_second: float
    level_counts: Dict[str, int]
    win_buckets: Dict[str, int]
    cells_generated: int = 0
    sediment_cells: int = 0
    sediment_share: float = 0.0          # % of generated cells that were DEAD_SEDIMENT
    sediment_share_by_level: Optional[Dict[str, float]] = None
    avg_free_spins: float = 0.0          # average free spins consumed per round
    std_dev_multiplier: float = 0.0      # volatility: std dev of per-round multiplier
    seed: Optional[int] = None
    mode: str = "NONE"


class MonteCarloSimulator:
    """Executes high-speed headless simulations to verify math model calibration."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = SlotRNG(seed=seed)
        self.engine = SlotStateMachine(rng=self.rng)

    def run(
        self,
        num_spins: int = 50000,
        base_bet: float = 1.0,
        feature_buy: FeatureBuyType = FeatureBuyType.NONE,
    ) -> SimulationReport:
        total_bet = 0.0
        total_payout = 0.0
        hit_count = 0
        max_win = 0.0
        max_win_mult = 0.0
        caps_hit = 0
        sum_mult = 0.0
        sum_sq_mult = 0.0
        free_spins_total = 0

        # Cell composition tracking (initial drops + cascade refills)
        cells_total = 0
        sediment_total = 0
        cells_by_level: Dict[str, int] = {lvl.name: 0 for lvl in DepthLevel}
        sediment_by_level: Dict[str, int] = {lvl.name: 0 for lvl in DepthLevel}
        sediment_value = SymbolType.DEAD_SEDIMENT.value

        level_counts: Dict[str, int] = {lvl.name: 0 for lvl in DepthLevel}

        win_buckets: Dict[str, int] = {
            "0x (Loss)": 0,
            "0.01x - 1x (Micro)": 0,
            "1x - 5x (Small)": 0,
            "5x - 20x (Medium)": 0,
            "20x - 100x (Big)": 0,
            "100x - 500x (Super)": 0,
            "500x+ (Mega/Epic)": 0,
        }

        start_time = time.time()

        for _ in range(num_spins):
            outcome = self.engine.execute_spin(base_bet=base_bet, feature_buy=feature_buy)
            total_bet += outcome.bet
            total_payout += outcome.total_payout

            if outcome.total_payout > 0:
                hit_count += 1

            if outcome.total_payout > max_win:
                max_win = outcome.total_payout
                max_win_mult = outcome.payout_multiplier

            if outcome.max_win_capped:
                caps_hit += 1

            level_counts[outcome.final_depth_level.name] += 1

            mult = outcome.payout_multiplier
            sum_mult += mult
            sum_sq_mult += mult * mult

            # Walk the event timeline for cell composition and free spin usage
            current_level_name = DepthLevel.LEVEL_0_SUNLIGHT.name
            for ev in outcome.events:
                et = ev.event_type
                if et == "SPIN_STARTED":
                    current_level_name = DepthLevel(ev.data["depth_level"]).name
                    if ev.data.get("is_free_spin"):
                        free_spins_total += 1
                elif et == "GRID_DROP":
                    for row in ev.data["grid"]:
                        n = len(row)
                        s = row.count(sediment_value)
                        cells_total += n
                        sediment_total += s
                        cells_by_level[current_level_name] += n
                        sediment_by_level[current_level_name] += s
                elif et == "CASCADE_DROP":
                    for dropped in ev.data["newly_dropped"]:
                        cells_total += 1
                        cells_by_level[current_level_name] += 1
                        if dropped["symbol"] == sediment_value:
                            sediment_total += 1
                            sediment_by_level[current_level_name] += 1
                elif et == "LEVEL_UP":
                    current_level_name = DepthLevel(ev.data["new_level"]).name

            # Categorize win bucket
            if mult == 0:
                win_buckets["0x (Loss)"] += 1
            elif mult <= 1.0:
                win_buckets["0.01x - 1x (Micro)"] += 1
            elif mult <= 5.0:
                win_buckets["1x - 5x (Small)"] += 1
            elif mult <= 20.0:
                win_buckets["5x - 20x (Medium)"] += 1
            elif mult <= 100.0:
                win_buckets["20x - 100x (Big)"] += 1
            elif mult <= 500.0:
                win_buckets["100x - 500x (Super)"] += 1
            else:
                win_buckets["500x+ (Mega/Epic)"] += 1

        elapsed = time.time() - start_time
        rtp = (total_payout / total_bet) * 100 if total_bet > 0 else 0.0
        hit_freq = (hit_count / num_spins) * 100 if num_spins else 0.0
        mean_mult = sum_mult / num_spins if num_spins else 0.0
        variance = max(0.0, (sum_sq_mult / num_spins) - mean_mult * mean_mult) if num_spins else 0.0

        sediment_share_by_level = {
            lvl: (round(sediment_by_level[lvl] / cells_by_level[lvl] * 100, 2) if cells_by_level[lvl] else 0.0)
            for lvl in cells_by_level
        }

        return SimulationReport(
            spins_run=num_spins,
            total_bet=round(total_bet, 2),
            total_payout=round(total_payout, 2),
            measured_rtp=round(rtp, 2),
            hit_frequency=round(hit_freq, 2),
            max_win_observed=round(max_win, 2),
            max_win_multiplier=round(max_win_mult, 2),
            caps_triggered=caps_hit,
            elapsed_seconds=round(elapsed, 2),
            spins_per_second=round(num_spins / elapsed, 1) if elapsed > 0 else 0.0,
            level_counts=level_counts,
            win_buckets=win_buckets,
            cells_generated=cells_total,
            sediment_cells=sediment_total,
            sediment_share=round(sediment_total / cells_total * 100, 2) if cells_total else 0.0,
            sediment_share_by_level=sediment_share_by_level,
            avg_free_spins=round(free_spins_total / num_spins, 3) if num_spins else 0.0,
            std_dev_multiplier=round(variance ** 0.5, 3),
            seed=self.seed,
            mode=feature_buy.value,
        )


def _configure_stdout() -> None:
    """Make console output safe on Windows code pages (cp1252 etc.)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Monte Carlo Simulator for The Descent Slot")
    parser.add_argument("--spins", type=int, default=20000, help="Number of spins to simulate")
    parser.add_argument("--bet", type=float, default=1.0, help="Base bet per spin")
    parser.add_argument(
        "--buy",
        type=str,
        default="NONE",
        choices=["NONE", "XBET_SONAR_2X", "STANDARD_BONUS_100X", "ULTRA_BONUS_350X", "MYSTERY_BUY_200X"],
        help="Feature buy mode to simulate"
    )
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (deterministic runs)")
    parser.add_argument("--json", action="store_true", help="Emit the report as a JSON object instead of text")
    args = parser.parse_args()

    _configure_stdout()
    buy_type = FeatureBuyType[args.buy]

    sim = MonteCarloSimulator(seed=args.seed)
    report = sim.run(num_spins=args.spins, base_bet=args.bet, feature_buy=buy_type)

    if args.json:
        print(json.dumps(asdict(report), indent=2))
        return

    cost_mult = FEATURE_COST_MULTIPLIER[buy_type]
    print("=" * 70)
    print(f"SIMULATING {args.spins:,} SPINS FOR 'THE DESCENT' [MODE: {args.buy}] [SEED: {args.seed}]")
    print("=" * 70)

    print("\nMATHEMATICAL RESULTS:")
    print(f"- Total Spins:        {report.spins_run:,}")
    print(f"- Mode Cost:          {cost_mult:g}x base bet")
    print(f"- Total Wagered:      ${report.total_bet:,.2f}")
    print(f"- Total Paid Out:     ${report.total_payout:,.2f}")
    print(f"- Measured RTP:       {report.measured_rtp:.2f}% of mode cost (Target: 96.05%)")
    print(f"- Hit Frequency:      {report.hit_frequency:.2f}%")
    print(f"- Std Dev (x cost):   {report.std_dev_multiplier:.3f}")
    print(f"- Avg Free Spins:     {report.avg_free_spins:.3f} per round")
    print(f"- Max Win Observed:   ${report.max_win_observed:,.2f} ({report.max_win_multiplier:,.1f}x cost)")
    print(f"- Win Caps Reached:   {report.caps_triggered}")
    print(f"- Dead Sediment:      {report.sediment_share:.2f}% of {report.cells_generated:,} generated cells")
    print(f"- Performance:        {report.spins_per_second:,.0f} spins/sec in {report.elapsed_seconds:.2f}s")

    print("\nDEPTH REACH DISTRIBUTION:")
    for lvl, count in report.level_counts.items():
        pct = (count / report.spins_run) * 100
        sed = (report.sediment_share_by_level or {}).get(lvl, 0.0)
        print(f"- {lvl:<25}: {count:7,d} ({pct:5.2f}%)  sediment {sed:5.2f}%")

    print("\nWIN MAGNITUDE BUCKETS:")
    for bkt, count in report.win_buckets.items():
        pct = (count / report.spins_run) * 100
        print(f"- {bkt:<25}: {count:7,d} ({pct:5.2f}%)")
    print("=" * 70)


if __name__ == "__main__":
    main()
