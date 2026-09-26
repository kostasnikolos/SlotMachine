"""Headless Monte Carlo RTP & Volatility Simulator for The Descent."""

import argparse
import time
from dataclasses import dataclass, field
from typing import Dict, List
from slot_engine.config.symbols import DepthLevel, FeatureBuyType
from slot_engine.core.state_machine import SlotStateMachine
from slot_engine.core.rng import SlotRNG


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


class MonteCarloSimulator:
    """Executes high-speed headless simulations to verify math model calibration."""

    def __init__(self, seed: int = 42) -> None:
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

        level_counts: Dict[str, int] = {
            DepthLevel.LEVEL_0_SUNLIGHT.name: 0,
            DepthLevel.LEVEL_1_TWILIGHT.name: 0,
            DepthLevel.LEVEL_2_MIDNIGHT.name: 0,
            DepthLevel.LEVEL_3_ABYSS.name: 0,
            DepthLevel.LEVEL_4_HADAL.name: 0,
            DepthLevel.LEVEL_5_CORE.name: 0,
        }

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

            # Categorize win bucket
            mult = outcome.payout_multiplier
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
        hit_freq = (hit_count / num_spins) * 100

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
        )


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
    args = parser.parse_args()

    buy_type = FeatureBuyType[args.buy]
    print("=" * 70)
    print(f"🌊 SIMULATING {args.spins:,} SPINS FOR 'THE DESCENT' [MODE: {args.buy}]")
    print("=" * 70)

    sim = MonteCarloSimulator()
    report = sim.run(num_spins=args.spins, base_bet=args.bet, feature_buy=buy_type)

    print(f"\n📊 MATHEMATICAL RESULTS:")
    print(f"• Total Spins:        {report.spins_run:,}")
    print(f"• Total Wagered:      ${report.total_bet:,.2f}")
    print(f"• Total Paid Out:     ${report.total_payout:,.2f}")
    print(f"• Measured RTP:       {report.measured_rtp:.2f}% (Target: 96.05%)")
    print(f"• Hit Frequency:      {report.hit_frequency:.2f}% (Target: ~28%)")
    print(f"• Max Win Observed:   ${report.max_win_observed:,.2f} ({report.max_win_multiplier:,.1f}x bet)")
    print(f"• Win Caps Reached:   {report.caps_triggered}")
    print(f"• Performance:        {report.spins_per_second:,.0f} spins/sec in {report.elapsed_seconds:.2f}s")

    print("\n🏔️ DEPTH REACH DISTRIBUTION:")
    for lvl, count in report.level_counts.items():
        pct = (count / report.spins_run) * 100
        print(f"• {lvl:<25}: {count:7,d} ({pct:5.2f}%)")

    print("\n💰 WIN MAGNITUDE BUCKETS:")
    for bkt, count in report.win_buckets.items():
        pct = (count / report.spins_run) * 100
        print(f"• {bkt:<25}: {count:7,d} ({pct:5.2f}%)")
    print("=" * 70)


if __name__ == "__main__":
    main()
