"""Math gate for The Descent: simulate every mode with fixed seeds and fail on drift.

Run after every engine/config change:

    python scripts/math_check.py            # fast: 200k base spins, 40k xBet, 5k rounds per bonus buy (~35 s on 12 cores)
    python scripts/math_check.py --full     # 800k base spins, 160k xBet, 20k+ rounds per bonus buy (~2.5 min)
    python scripts/math_check.py --json out.json
    python scripts/math_check.py --api http://127.0.0.1:8080   # live check: buys one ULTRA round over HTTP,
                                                              # verifies the server runs this config and that
                                                              # DEAD_SEDIMENT <= 5% of the cells it dealt

Exit code is 1 when any mode's RTP is outside +/- RTP_TOLERANCE_PTS of the target (96.05% of that
mode's own cost) or when DEAD_SEDIMENT exceeds MAX_SEDIMENT_SHARE of generated cells at any level.

The base game and xBet are feature-driven (per-round std dev ~13x / ~8x the stake), so a finite
simulation carries sampling noise of its own. To keep the gate deterministic yet not flaky, the
pass window is widened by 2 standard errors of the mean, estimated from the spread of the per-seed
RTPs: |measured - target| <= RTP_TOLERANCE_PTS + 2 * SE. Both numbers are printed, so a mode that
passes only thanks to the SE term is visible (use --full to shrink it).
"""

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slot_engine.config.symbols import DepthLevel, FeatureBuyType  # noqa: E402
from slot_engine.config.rtp_profiles import FEATURE_BUY_COSTS, get_active_rtp_profile  # noqa: E402
from slot_engine.config.weights import MAX_SEDIMENT_SHARE  # noqa: E402
from slot_engine.simulation.monte_carlo import MonteCarloSimulator, SimulationReport  # noqa: E402

RTP_TOLERANCE_PTS = 2.0
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88]

# rounds per seed: (fast, full)
ROUNDS = {
    # Base and xBet are feature-driven (std dev ~13x and ~8x per round), so they need far more
    # rounds than the bonus buys (std dev ~1x) for the same confidence: 200k base rounds give a
    # standard error of ~3 pts, 800k ~1.5 pts.
    FeatureBuyType.NONE: (200_000, 800_000),
    FeatureBuyType.XBET_SONAR_2X: (40_000, 160_000),
    FeatureBuyType.STANDARD_BONUS_100X: (5_000, 24_000),
    FeatureBuyType.ULTRA_BONUS_350X: (5_000, 20_000),
    FeatureBuyType.MYSTERY_BUY_200X: (5_000, 20_000),
}


def _worker(args: Tuple[str, int, int]) -> Tuple[str, int, Dict[str, Any]]:
    mode, seed, spins = args
    sim = MonteCarloSimulator(seed=seed)
    report = sim.run(num_spins=spins, feature_buy=FeatureBuyType[mode])
    return mode, seed, report.__dict__


def _merge(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_bet = sum(r["total_bet"] for r in reports)
    total_pay = sum(r["total_payout"] for r in reports)
    spins = sum(r["spins_run"] for r in reports)
    hits = sum(r["hit_frequency"] / 100.0 * r["spins_run"] for r in reports)
    cells = sum(r["cells_generated"] for r in reports)
    sed = sum(r["sediment_cells"] for r in reports)
    levels: Dict[str, int] = {}
    buckets: Dict[str, int] = {}
    sed_by_level: Dict[str, float] = {}
    for r in reports:
        for k, v in r["level_counts"].items():
            levels[k] = levels.get(k, 0) + v
        for k, v in r["win_buckets"].items():
            buckets[k] = buckets.get(k, 0) + v
        for k, v in (r["sediment_share_by_level"] or {}).items():
            sed_by_level[k] = max(sed_by_level.get(k, 0.0), v)
    per_seed = [r["measured_rtp"] for r in reports]
    if len(per_seed) > 1:
        mean = sum(per_seed) / len(per_seed)
        sample_var = sum((x - mean) ** 2 for x in per_seed) / (len(per_seed) - 1)
        std_error = (sample_var / len(per_seed)) ** 0.5
    else:
        std_error = float("nan")
    return {
        "spins": spins,
        "rtp": total_pay / total_bet * 100 if total_bet else 0.0,
        "rtp_per_seed": per_seed,
        "rtp_std_error": std_error,
        "hit_frequency": hits / spins * 100 if spins else 0.0,
        "max_win_x_cost": max(r["max_win_multiplier"] for r in reports),
        "cap_hits": sum(r["caps_triggered"] for r in reports),
        "avg_free_spins": sum(r["avg_free_spins"] * r["spins_run"] for r in reports) / spins if spins else 0.0,
        "level_distribution": {k: v / spins * 100 for k, v in levels.items() if v},
        "win_buckets": {k: v / spins * 100 for k, v in buckets.items()},
        "sediment_share": sed / cells * 100 if cells else 0.0,
        "sediment_share_by_level": {k: v for k, v in sed_by_level.items() if v},
    }


def run_gate(full: bool, seeds: List[int], workers: int) -> Tuple[Dict[str, Any], bool]:
    jobs = []
    for mode, (fast_n, full_n) in ROUNDS.items():
        n = full_n if full else fast_n
        per_seed = max(1, n // len(seeds))
        for s in seeds:
            jobs.append((mode.value, s, per_seed))

    t0 = time.time()
    with Pool(min(workers, len(jobs))) as pool:
        raw = pool.map(_worker, jobs)

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for mode, _seed, rep in raw:
        grouped.setdefault(mode, []).append(rep)

    profile = get_active_rtp_profile()
    target = profile.target_rtp * 100
    results: Dict[str, Any] = {
        "profile": profile.profile_id,
        "target_rtp": target,
        "tolerance_pts": RTP_TOLERANCE_PTS,
        "max_sediment_share": MAX_SEDIMENT_SHARE * 100,
        "full": full,
        "seeds": seeds,
        "elapsed_seconds": 0.0,
        "modes": {},
    }
    ok = True
    for mode in ROUNDS:
        m = _merge(grouped[mode.value])
        m["cost_x_bet"] = FEATURE_BUY_COSTS[mode]
        m["target_rtp"] = target
        m["rtp_delta_pts"] = m["rtp"] - target
        se = m["rtp_std_error"] if m["rtp_std_error"] == m["rtp_std_error"] else 0.0
        m["rtp_window_pts"] = RTP_TOLERANCE_PTS + 2 * se
        m["rtp_ok"] = abs(m["rtp_delta_pts"]) <= m["rtp_window_pts"]
        m["sediment_ok"] = all(v <= MAX_SEDIMENT_SHARE * 100 for v in m["sediment_share_by_level"].values()) \
            and m["sediment_share"] <= MAX_SEDIMENT_SHARE * 100
        # payout_multiplier is rounded to 2 decimals by the engine, so allow that rounding (0.005 x cost)
        m["cap_ok"] = (m["max_win_x_cost"] - 0.005) * FEATURE_BUY_COSTS[mode] <= profile.max_win_multiplier
        m["ok"] = m["rtp_ok"] and m["sediment_ok"] and m["cap_ok"]
        ok = ok and m["ok"]
        results["modes"][mode.value] = m
    results["elapsed_seconds"] = round(time.time() - t0, 1)
    results["passed"] = ok
    return results, ok


def print_table(results: Dict[str, Any]) -> None:
    target = results["target_rtp"]
    print("=" * 124)
    print(f"THE DESCENT MATH GATE  profile={results['profile']}  target={target:.2f}% of mode cost  "
          f"tolerance=+/-{results['tolerance_pts']:.1f} pts  sediment<={results['max_sediment_share']:.0f}%  "
          f"{'FULL' if results['full'] else 'FAST'} run, {results['elapsed_seconds']}s")
    print("=" * 124)
    hdr = f"{'mode':<22}{'cost':>6}{'rounds':>9}{'RTP%':>8}{'delta':>7}{'+/-SE':>6}{'hit%':>7}{'maxWin':>9}{'caps':>5}{'sed%':>6}  {'levels reached %':<38}{'status':>8}"
    print(hdr)
    print("-" * 124)
    short = {lvl.name: f"L{lvl.value}" for lvl in DepthLevel}
    for mode, m in results["modes"].items():
        lv = " ".join(f"{short[k]}:{v:.2f}" for k, v in sorted(m["level_distribution"].items()))
        status = "PASS" if m["ok"] else "FAIL"
        print(f"{mode:<22}{m['cost_x_bet']:>5.0f}x{m['spins']:>9,}{m['rtp']:>8.2f}{m['rtp_delta_pts']:>+7.2f}{m['rtp_std_error']:>6.2f}"
              f"{m['hit_frequency']:>7.2f}{m['max_win_x_cost']:>8.1f}x{m['cap_hits']:>5}{m['sediment_share']:>6.2f}  {lv:<38}{status:>8}")
    print("-" * 124)
    print("Win buckets (% of rounds, x cost):  " + " | ".join(results["modes"]["NONE"]["win_buckets"].keys()))
    for mode, m in results["modes"].items():
        print(f"  {mode:<22}" + "  ".join(f"{v:6.2f}" for v in m["win_buckets"].values()))
    print("Per-seed RTP (pass window = tolerance + 2*SE):")
    for mode, m in results["modes"].items():
        print(f"  {mode:<22}window +/-{m['rtp_window_pts']:.2f}  {m['rtp_per_seed']}")
    sed = {}
    for m in results["modes"].values():
        for k, v in m["sediment_share_by_level"].items():
            sed[short[k]] = max(sed.get(short[k], 0.0), v)
    print("Max DEAD_SEDIMENT share of generated cells by level: " + ", ".join(f"{k}={v:.2f}%" for k, v in sorted(sed.items())))
    print("=" * 124)
    print("RESULT:", "PASS" if results["passed"] else "FAIL")


def api_check(base_url: str, rounds: int = 1) -> bool:
    """Call the running API, buy ULTRA rounds and count the symbols in every dealt grid cell."""
    import collections
    import urllib.request
    from slot_engine.config.symbols import DEPTH_LEVEL_THRESHOLDS, SYMBOL_PAYTABLE, SymbolType

    def get(path: str) -> Any:
        with urllib.request.urlopen(base_url + path, timeout=30) as resp:
            return json.load(resp)

    def post(path: str, body: Dict[str, Any]) -> Any:
        req = urllib.request.Request(base_url + path, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.load(resp)

    ok = True
    pt = get("/api/slot/paytable")
    server_thresholds = {int(k): v for k, v in pt["depth_thresholds"].items()}
    local_thresholds = {lvl.value: v for lvl, v in DEPTH_LEVEL_THRESHOLDS.items()}
    server_lev = {int(k): v for k, v in pt["paytable"][SymbolType.HIGH_LEVIATHAN.value].items()}
    local_lev = SYMBOL_PAYTABLE[SymbolType.HIGH_LEVIATHAN]
    if server_thresholds != local_thresholds or server_lev != local_lev:
        print(f"API CONFIG MISMATCH: server thresholds={server_thresholds} paytable(LEV)={server_lev}; "
              f"local={local_thresholds} / {local_lev}. Restart the server so it loads the current config.")
        ok = False
    else:
        print(f"API config matches local config (thresholds {local_thresholds}).")

    counts: collections.Counter = collections.Counter()
    cells = 0
    payouts: List[float] = []
    for _ in range(rounds):
        out = post("/api/slot/buy-bonus", {"bet": 1.0, "feature_type": FeatureBuyType.ULTRA_BONUS_350X.value})
        payouts.append(out.get("total_payout", 0.0))
        for ev in out.get("events", []):
            et = ev.get("event_type")
            data = ev.get("data", {})
            if et == "GRID_DROP":
                for row in data["grid"]:
                    for sym in row:
                        counts[sym] += 1
                        cells += 1
            elif et == "CASCADE_DROP":
                for dropped in data["newly_dropped"]:
                    counts[dropped["symbol"]] += 1
                    cells += 1
    sed_share = counts[SymbolType.DEAD_SEDIMENT.value] / cells * 100 if cells else 0.0
    print(f"ULTRA_BONUS_350X via API: rounds={rounds} payouts(x bet)={payouts} cells dealt={cells}")
    for sym, n in counts.most_common():
        print(f"  {sym:<16}{n:6d}  {n / cells * 100:5.2f}%")
    sed_ok = sed_share <= MAX_SEDIMENT_SHARE * 100
    print(f"DEAD_SEDIMENT share: {sed_share:.2f}% -> {'OK' if sed_ok else 'FAIL'} (limit {MAX_SEDIMENT_SHARE * 100:.0f}%)")
    return ok and sed_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Math calibration gate for The Descent")
    parser.add_argument("--full", action="store_true", help="Large run (800k base spins, 160k xBet, 20k+ rounds per bonus buy)")
    parser.add_argument("--json", type=str, default=None, help="Also write the results to this JSON file")
    parser.add_argument("--workers", type=int, default=max(1, min(12, os.cpu_count() or 1)))
    parser.add_argument("--seeds", type=str, default=",".join(str(s) for s in SEEDS))
    parser.add_argument("--api", type=str, default=None,
                        help="Skip the simulation; buy ULTRA rounds from a running API at this base URL and check sediment")
    parser.add_argument("--api-rounds", type=int, default=1)
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

    if args.api:
        return 0 if api_check(args.api.rstrip("/"), args.api_rounds) else 1

    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    results, ok = run_gate(full=args.full, seeds=seeds, workers=args.workers)
    print_table(results)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        print(f"JSON written to {args.json}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
