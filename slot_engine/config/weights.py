"""Dynamic symbol probability weight distributions for Levels 0 through 5 and Bonus modes."""

from typing import Dict, List, Tuple
from slot_engine.config.symbols import SymbolType, DepthLevel


# Raw probability weights for symbol drop generation across each DepthLevel.
# Higher weight = higher probability of landing on the grid during initial drop or cascade refill.
LEVEL_WEIGHT_DISTRIBUTIONS: Dict[DepthLevel, Dict[SymbolType, int]] = {
    # Level 0: Sunlight Zone (All 11 symbols present, Lows dominate ~67% of mass)
    DepthLevel.LEVEL_0_SUNLIGHT: {
        SymbolType.LOW_10: 32,
        SymbolType.LOW_J: 28,
        SymbolType.LOW_Q: 25,
        SymbolType.LOW_K: 22,
        SymbolType.LOW_A: 18,
        SymbolType.MID_HELMET: 12,
        SymbolType.MID_COMPASS: 10,
        SymbolType.HIGH_VIPER: 7,
        SymbolType.HIGH_ANGLER: 5,
        SymbolType.HIGH_SQUID: 3,
        SymbolType.HIGH_LEVIATHAN: 2,
        SymbolType.WILD_MAW: 3,
        SymbolType.DEAD_SEDIMENT: 0,
    },

    # Level 1: Twilight Zone (LOW_10 purged, mass shifted to mid and high)
    DepthLevel.LEVEL_1_TWILIGHT: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 32,
        SymbolType.LOW_Q: 28,
        SymbolType.LOW_K: 25,
        SymbolType.LOW_A: 20,
        SymbolType.MID_HELMET: 16,
        SymbolType.MID_COMPASS: 14,
        SymbolType.HIGH_VIPER: 9,
        SymbolType.HIGH_ANGLER: 7,
        SymbolType.HIGH_SQUID: 4,
        SymbolType.HIGH_LEVIATHAN: 2,
        SymbolType.WILD_MAW: 4,
        SymbolType.DEAD_SEDIMENT: 0,
    },

    # Level 2: Midnight Zone (LOW_J purged)
    DepthLevel.LEVEL_2_MIDNIGHT: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 32,
        SymbolType.LOW_K: 28,
        SymbolType.LOW_A: 24,
        SymbolType.MID_HELMET: 18,
        SymbolType.MID_COMPASS: 16,
        SymbolType.HIGH_VIPER: 12,
        SymbolType.HIGH_ANGLER: 9,
        SymbolType.HIGH_SQUID: 6,
        SymbolType.HIGH_LEVIATHAN: 3,
        SymbolType.WILD_MAW: 5,
        SymbolType.DEAD_SEDIMENT: 0,
    },

    # Level 3: Abyssal Plains (LOW_Q purged, Maelstrom Wild & Vents activate)
    DepthLevel.LEVEL_3_ABYSS: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 0,
        SymbolType.LOW_K: 30,
        SymbolType.LOW_A: 26,
        SymbolType.MID_HELMET: 22,
        SymbolType.MID_COMPASS: 20,
        SymbolType.HIGH_VIPER: 16,
        SymbolType.HIGH_ANGLER: 12,
        SymbolType.HIGH_SQUID: 8,
        SymbolType.HIGH_LEVIATHAN: 4,
        SymbolType.WILD_MAW: 7,
        SymbolType.DEAD_SEDIMENT: 0,
    },

    # Level 4: Hadal Trench (LOW_K purged, xSplit tentacles active)
    DepthLevel.LEVEL_4_HADAL: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 0,
        SymbolType.LOW_K: 0,
        SymbolType.LOW_A: 28,
        SymbolType.MID_HELMET: 26,
        SymbolType.MID_COMPASS: 24,
        SymbolType.HIGH_VIPER: 20,
        SymbolType.HIGH_ANGLER: 16,
        SymbolType.HIGH_SQUID: 12,
        SymbolType.HIGH_LEVIATHAN: 6,
        SymbolType.WILD_MAW: 9,
        SymbolType.DEAD_SEDIMENT: 0,
    },

    # Level 5: The Core / Ultra Bonus (100% of Low Runes Purged! Pure Highs, Mids, Apex & Wilds + Dead Sediment)
    DepthLevel.LEVEL_5_CORE: {
        SymbolType.LOW_10: 0,
        SymbolType.LOW_J: 0,
        SymbolType.LOW_Q: 0,
        SymbolType.LOW_K: 0,
        SymbolType.LOW_A: 0,
        SymbolType.MID_HELMET: 32,
        SymbolType.MID_COMPASS: 28,
        SymbolType.HIGH_VIPER: 22,
        SymbolType.HIGH_ANGLER: 16,
        SymbolType.HIGH_SQUID: 10,
        SymbolType.HIGH_LEVIATHAN: 5,
        SymbolType.WILD_MAW: 4,
        SymbolType.DEAD_SEDIMENT: 55,
    },
}


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
