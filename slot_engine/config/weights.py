"""Dynamic symbol probability weight distributions for Levels 0 through 5 and Bonus modes.

Calibration notes (see docs/math_calibration.md):

* Weights are relative integers; each level's table has its own scale, so compare
  shares (weight / level total), not raw numbers across levels.
* Owner's rule: when a depth level purges a low symbol, that symbol's probability
  mass goes to the *remaining paying symbols* (mids and highs), never to empty
  DEAD_SEDIMENT seats. Sediment is a rare blocker only (<= 5% of cells at any level;
  it is 0% in the base game and 2-3% at depth).
* On a 5-row ways grid the cascade chain stalls only when every symbol is individually
  rare in each reel, so the deep levels use a near-flat spread over the surviving
  symbols (the pyramid is kept gently: mids >= highs >= apex, wilds small). A
  concentrated distribution would make cascades effectively endless.
* WILD_MAW at Levels 0 and 1 is the most sensitive single lever in the whole model
  (it feeds both ways-count and pressure points): +1 wild unit at Level 0 nearly doubles the
  base RTP. It is tuned to fractional shares (1.5 and 1.125 units), which is why those two
  tables carry a larger integer scale (x32 and x8).
* Pressure package (2026-11-06): with the pressure multiplier on, the Level-0 table carries less
  wild (2.09 -> 1.5 units) and its high-symbol mass moved to the mids (mids pay from 3 reels like
  the highs, so the hit rate holds, but earn 1 pressure point instead of 2-3, so natural descents
  are rarer). The Level-5 table lost its 1% wild and runs 4% sediment: that is what pays for the
  bite retrigger inside the Ultra, the only mode the retrigger alone reaches.
"""

from typing import Dict, List, Tuple
from slot_engine.config.symbols import SymbolType, DepthLevel


# Raw probability weights for symbol drop generation across each DepthLevel.
# Higher weight = higher probability of landing on the grid during initial drop or cascade refill.
LEVEL_WEIGHT_DISTRIBUTIONS: Dict[DepthLevel, Dict[SymbolType, int]] = {
    # Level 0: Sunlight Zone (all 11 paying symbols; lows ~56%, mids ~24%, highs ~18%, wild ~1.4%)
    # Scale x32 so that WILD_MAW can sit at 1.5 "units" (48/32). Total = 3408.
    DepthLevel.LEVEL_0_SUNLIGHT: {
        SymbolType.LOW_10: 384,
        SymbolType.LOW_J: 384,
        SymbolType.LOW_Q: 384,
        SymbolType.LOW_K: 384,
        SymbolType.LOW_A: 384,
        SymbolType.MID_HELMET: 416,
        SymbolType.MID_COMPASS: 416,
        SymbolType.HIGH_VIPER: 240,
        SymbolType.HIGH_ANGLER: 208,
        SymbolType.HIGH_SQUID: 112,
        SymbolType.HIGH_LEVIATHAN: 48,
        SymbolType.WILD_MAW: 48,
        SymbolType.DEAD_SEDIMENT: 0,
    },

    # Level 1: Twilight Zone (LOW_10 purged; its mass goes to mids/highs; sediment 1.9%)
    # Scale x8 so that WILD_MAW can sit at 1.125 units (9/8). Total = 841.
    DepthLevel.LEVEL_1_TWILIGHT: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 112,
        SymbolType.LOW_Q: 104,
        SymbolType.LOW_K: 104,
        SymbolType.LOW_A: 96,
        SymbolType.MID_HELMET: 112,
        SymbolType.MID_COMPASS: 104,
        SymbolType.HIGH_VIPER: 64,
        SymbolType.HIGH_ANGLER: 56,
        SymbolType.HIGH_SQUID: 40,
        SymbolType.HIGH_LEVIATHAN: 24,
        SymbolType.WILD_MAW: 9,
        SymbolType.DEAD_SEDIMENT: 16,
    },

    # Level 2: Midnight Zone (LOW_J purged; sediment 1.9%). Total = 106.
    DepthLevel.LEVEL_2_MIDNIGHT: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 16,
        SymbolType.LOW_K: 15,
        SymbolType.LOW_A: 14,
        SymbolType.MID_HELMET: 16,
        SymbolType.MID_COMPASS: 15,
        SymbolType.HIGH_VIPER: 9,
        SymbolType.HIGH_ANGLER: 8,
        SymbolType.HIGH_SQUID: 6,
        SymbolType.HIGH_LEVIATHAN: 3,
        SymbolType.WILD_MAW: 2,
        SymbolType.DEAD_SEDIMENT: 2,
    },

    # Level 3: Abyssal Plains (LOW_Q purged, Maelstrom Wild & Vents active; sediment 2.0%).
    # Near-flat spread over the 8 surviving paying symbols. Total = 100.
    DepthLevel.LEVEL_3_ABYSS: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 0,
        SymbolType.LOW_K: 11,
        SymbolType.LOW_A: 11,
        SymbolType.MID_HELMET: 12,
        SymbolType.MID_COMPASS: 12,
        SymbolType.HIGH_VIPER: 13,
        SymbolType.HIGH_ANGLER: 13,
        SymbolType.HIGH_SQUID: 12,
        SymbolType.HIGH_LEVIATHAN: 10,
        SymbolType.WILD_MAW: 4,
        SymbolType.DEAD_SEDIMENT: 2,
    },

    # Level 4: Hadal Trench (LOW_K purged, xSplit tentacles active; sediment 2.0%). Total = 102.
    DepthLevel.LEVEL_4_HADAL: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 0,
        SymbolType.LOW_K: 0,
        SymbolType.LOW_A: 13,
        SymbolType.MID_HELMET: 14,
        SymbolType.MID_COMPASS: 14,
        SymbolType.HIGH_VIPER: 15,
        SymbolType.HIGH_ANGLER: 14,
        SymbolType.HIGH_SQUID: 13,
        SymbolType.HIGH_LEVIATHAN: 12,
        SymbolType.WILD_MAW: 5,
        SymbolType.DEAD_SEDIMENT: 2,
    },

    # Level 5: The Core / Ultra Bonus (all lows purged: only mids, highs, apex; sediment 4%, no table wild:
    # the Leviathan itself is the Core's wild). Total = 101.
    DepthLevel.LEVEL_5_CORE: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 0,
        SymbolType.LOW_K: 0,
        SymbolType.LOW_A: 0,
        SymbolType.MID_HELMET: 21,
        SymbolType.MID_COMPASS: 19,
        SymbolType.HIGH_VIPER: 17,
        SymbolType.HIGH_ANGLER: 16,
        SymbolType.HIGH_SQUID: 14,
        SymbolType.HIGH_LEVIATHAN: 10,
        SymbolType.WILD_MAW: 0,
        SymbolType.DEAD_SEDIMENT: 4,
    },
}


# Hard ceiling enforced by scripts/math_check.py: DEAD_SEDIMENT share of generated cells per level.
MAX_SEDIMENT_SHARE: float = 0.05


# Bonus Mode Overlays: In Free Spins, symbols have a chance to carry an Abyssal Pearl token
# Pearl token appearance chance per symbol cell: 0.1% (calibrated for rare exciting ascension)
BONUS_PEARL_TOKEN_PROBABILITY: float = 0.001


# Hydrothermal Vent Multiplier probabilities when a vent erupts beneath columns 2, 3, or 4
# Multipliers compound if a winning way crosses multiple active vents!
VENT_MULTIPLIER_WEIGHTS: List[Tuple[int, int]] = [
    (2, 60),  # 2x: 60% probability
    (3, 30),  # 3x: 30% probability
    (5, 10),  # 5x: 10% probability
]
