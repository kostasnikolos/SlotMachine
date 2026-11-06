"""Feature switches and their tuning (docs/feature_ideas_brief.md, "the pressure package").

Every number here moves the math: change it, run `python scripts/math_check.py --full`, re-pin the baseline with
`--write-pin artifacts/math_baseline.json` in the same commit and update docs/math_calibration.md.
"""

# A. Crush depth (the Tombstone RIP "xRIP" idea in our fiction): in the base game, a round that never leaves the Sunlight
# Zone and returns less than CRUSH_THRESHOLD_X x the stake is crushed by pressure: it pays nothing and the front end shows
# the symbols imploding instead of a dust win. Measured 2026-11-06 on the calibrated engine: 44% of base rounds pay
# < 0.1x the stake; at 0.01x the crush voids 19% of rounds, hit frequency 49% -> ~31%, RTP sink < 0.1 pt. 0.015x -> 24%.
CRUSH_DEPTH_ENABLED: bool = True
CRUSH_THRESHOLD_X: float = 0.01       # fraction of the round's stake below which a Level-0 return is crushed

# B. Pressure multiplier, bounded by the fiction: the multiplier IS the depth. Inside a descent every win is multiplied by
# 1 + PRESSURE_PER_LEVEL x (levels descended in this round), capped. A bought bonus starts at its entry level with 1x and
# builds as it descends further. At the Core the fixed Ultra 2x and the pressure multiplier do not stack: the larger applies.
# (A first draft that added +1 per winning cascade sent every descent to the 15,000x cap: deep cascades chain 20+ steps.)
PRESSURE_MULT_ENABLED: bool = False     # measured 2026-11-06: 0.5/level -> base 239%, Standard 105%; 0.25/level cap 2 -> base 196%. Needs the descent frequency rebalanced first.
PRESSURE_PER_LEVEL: float = 0.5
PRESSURE_CAP: float = 4.0

# C. Second breath: a Leviathan bite during free spins has a chance to award extra spins, capped per round.
# (A retrigger on every bite never ends a bonus: the creature is re-armed every spin at depth.)
BITE_RETRIGGER_ENABLED: bool = False    # measured 2026-11-06: 20% chance cap 4 -> base 279%, Standard 189%, Ultra 116%; 5% cap 2 (with B 0.25) -> base 196%. Same rebalancing needed.
BITE_RETRIGGER_CHANCE: float = 0.2
BITE_RETRIGGER_SPINS: int = 1
BITE_RETRIGGER_MAX_PER_ROUND: int = 4
