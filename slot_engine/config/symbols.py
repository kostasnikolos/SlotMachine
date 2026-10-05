"""Symbol definitions, paytable multipliers, and depth metadata for The Descent."""

from enum import Enum
from typing import Dict, List, Any


class SymbolCategory(str, Enum):
    LOW = "LOW"
    MID = "MID"
    HIGH = "HIGH"
    APEX = "APEX"
    WILD = "WILD"
    SPECIAL = "SPECIAL"


class SymbolType(str, Enum):
    # Low-paying oceanic runes (0 pressure points)
    LOW_10 = "LOW_10"
    LOW_J = "LOW_J"
    LOW_Q = "LOW_Q"
    LOW_K = "LOW_K"
    LOW_A = "LOW_A"

    # Mid-paying expedition equipment (1 pressure point)
    MID_HELMET = "MID_HELMET"
    MID_COMPASS = "MID_COMPASS"

    # High-paying abyssal predators (2 pressure points)
    HIGH_VIPER = "HIGH_VIPER"
    HIGH_ANGLER = "HIGH_ANGLER"
    HIGH_SQUID = "HIGH_SQUID"

    # Apex Eldritch Core (3 pressure points)
    HIGH_LEVIATHAN = "HIGH_LEVIATHAN"

    # Special Symbols
    WILD_MAW = "WILD_MAW"          # Wild substitute (5 pressure points)
    PEARL_TOKEN = "PEARL_TOKEN"    # Overlay token in Bonus (Ascension trigger)
    DEAD_SEDIMENT = "DEAD_SEDIMENT"# Abyssal Blocker / Silt (destroyed by adjacent wins)


class DepthLevel(int, Enum):
    LEVEL_0_SUNLIGHT = 0   # 0m, Base state
    LEVEL_1_TWILIGHT = 1   # 500m, 15 pts, 10 removed, 1x1 Maw, +1 spin
    LEVEL_2_MIDNIGHT = 2   # 2,000m, 80 pts, J removed, 2x1 Maw, +1 spin
    LEVEL_3_ABYSS = 3      # 5,000m, 225 pts, Q removed, 2x2 Maelstrom, Vents (+4 natural / 6 bought)
    LEVEL_4_HADAL = 4      # 8,000m, 585 pts, K removed, 3x3 Tentacles, +2 spins (xSplit NOT implemented)
    LEVEL_5_CORE = 5       # 11,000m, 1130 pts, A removed, 6x5 grid (15,625 ways), +4 / Ultra 8 spins


class FeatureBuyType(str, Enum):
    NONE = "NONE"
    XBET_SONAR_2X = "XBET_SONAR_2X"                 # 2.0x bet (starts at Level 1 with 10s removed)
    STANDARD_BONUS_100X = "STANDARD_BONUS_100X"     # 100x bet (Level 3 Abyssal Descent, 6 spins)
    ULTRA_BONUS_350X = "ULTRA_BONUS_350X"           # 350x bet (Level 5 Leviathan Awakening, 8 spins)
    MYSTERY_BUY_200X = "MYSTERY_BUY_200X"           # 200x bet (Standard / Ultra split: GAME_RULES["mystery_ultra_probability"])


# Symbol categories for quick validation & filtering
SYMBOL_CATEGORIES: Dict[SymbolType, SymbolCategory] = {
    SymbolType.LOW_10: SymbolCategory.LOW,
    SymbolType.LOW_J: SymbolCategory.LOW,
    SymbolType.LOW_Q: SymbolCategory.LOW,
    SymbolType.LOW_K: SymbolCategory.LOW,
    SymbolType.LOW_A: SymbolCategory.LOW,
    SymbolType.MID_HELMET: SymbolCategory.MID,
    SymbolType.MID_COMPASS: SymbolCategory.MID,
    SymbolType.HIGH_VIPER: SymbolCategory.HIGH,
    SymbolType.HIGH_ANGLER: SymbolCategory.HIGH,
    SymbolType.HIGH_SQUID: SymbolCategory.HIGH,
    SymbolType.HIGH_LEVIATHAN: SymbolCategory.APEX,
    SymbolType.WILD_MAW: SymbolCategory.WILD,
    SymbolType.PEARL_TOKEN: SymbolCategory.SPECIAL,
    SymbolType.DEAD_SEDIMENT: SymbolCategory.SPECIAL,
}


# Paytable expressed as multiplier of total base bet for 3, 4, 5, and 6 consecutive matching reels
# (Reels 1-5 in base, Reels 1-6 in Ultra Bonus 6x5 mode)
SYMBOL_PAYTABLE: Dict[SymbolType, Dict[int, float]] = {
    # REBALANCE: flatter ladder (apex 5-reel ~6x a low instead of 20x) and 6-reel pays only
    # just above 5-reel pays. Deep levels are rich because they are dense in mids/highs and
    # multipliers, not because individual symbols pay 10-20x more than lows.
    SymbolType.HIGH_LEVIATHAN: {3: 0.10, 4: 0.25, 5: 0.50, 6: 0.52},
    SymbolType.HIGH_SQUID:     {3: 0.07, 4: 0.16, 5: 0.32, 6: 0.33},
    SymbolType.HIGH_ANGLER:    {3: 0.06, 4: 0.13, 5: 0.26, 6: 0.27},
    SymbolType.HIGH_VIPER:     {3: 0.05, 4: 0.11, 5: 0.22, 6: 0.23},
    SymbolType.MID_COMPASS:    {3: 0.04, 4: 0.09, 5: 0.18, 6: 0.19},
    SymbolType.MID_HELMET:     {3: 0.035, 4: 0.08, 5: 0.15, 6: 0.16},
    SymbolType.LOW_A:          {3: 0.03, 4: 0.06, 5: 0.12, 6: 0.13},
    SymbolType.LOW_K:          {3: 0.025, 4: 0.05, 5: 0.10, 6: 0.11},
    SymbolType.LOW_Q:          {3: 0.025, 4: 0.05, 5: 0.10, 6: 0.11},
    SymbolType.LOW_J:          {3: 0.02, 4: 0.04, 5: 0.08, 6: 0.09},
    SymbolType.LOW_10:         {3: 0.02, 4: 0.04, 5: 0.08, 6: 0.09},
}


# Round-level rules for feature buys, multipliers and the creature (single source of truth;
# previously hard-coded in state_machine.py / creature.py).
GAME_RULES: Dict[str, Any] = {
    "standard_bonus_spins": 6,          # STANDARD_BONUS_100X free spins (starts at Level 3)
    "ultra_bonus_spins": 8,             # ULTRA_BONUS_350X free spins (starts at Level 5, 6x5)
    "mystery_ultra_probability": 0.40,  # MYSTERY_BUY_200X -> Ultra share (rest Standard)
    "xbet_start_points": 55,            # XBET_SONAR_2X starts at Level 1 with 55/80 pts toward Level 2
    "core_global_multiplier": 2,        # Level 5 / Ultra global win multiplier
    "core_wild_multiplier": 1,          # Level 5 2x2 Leviathan wild cell multiplier (global 2x still applies)
    "hadal_center_wild_multiplier": 3,  # Level 4 3x3 Tentacle centre wild multiplier
    "creature_respins_awarded": 0,      # Reported in CREATURE_LIFELINE_STRIKE; strikes do NOT add spins
    "pearls_for_ascension": 5,          # Pearls needed in a round to ascend to Level 5
    "ascension_spins": 2,               # Spins added on pearl ascension
}


# Pressure points awarded to Depth Gauge when symbols are burned in cascades
# NOTE: Low-paying symbols award 0 points (cash only), protecting base-game payouts!
SYMBOL_PRESSURE_POINTS: Dict[SymbolType, int] = {
    # Awarded once per winning combination (symbol), not per cell. The WILD_MAW value is the
    # bonus added to any wild-assisted combination. Scaled x5 vs. the original 1/2/3/+1.
    SymbolType.LOW_10: 0,
    SymbolType.LOW_J: 0,
    SymbolType.LOW_Q: 0,
    SymbolType.LOW_K: 0,
    SymbolType.LOW_A: 0,
    SymbolType.MID_HELMET: 5,
    SymbolType.MID_COMPASS: 5,
    SymbolType.HIGH_VIPER: 10,
    SymbolType.HIGH_ANGLER: 10,
    SymbolType.HIGH_SQUID: 10,
    SymbolType.HIGH_LEVIATHAN: 15,
    SymbolType.WILD_MAW: 5,
    SymbolType.PEARL_TOKEN: 0,
    SymbolType.DEAD_SEDIMENT: 0,
}


# Thresholds of accumulated pressure points required to breach each depth level
DEPTH_LEVEL_THRESHOLDS: Dict[DepthLevel, int] = {
    DepthLevel.LEVEL_0_SUNLIGHT: 0,
    DepthLevel.LEVEL_1_TWILIGHT: 15,   # base: ~1 in 5 rounds
    DepthLevel.LEVEL_2_MIDNIGHT: 80,   # base: ~1 in 29 rounds
    DepthLevel.LEVEL_3_ABYSS: 225,     # Unlocks Abyssal Descent (Standard Bonus Milestone), base ~1 in 690
    DepthLevel.LEVEL_4_HADAL: 585,     # Standard bonus reaches it ~50% of the time
    DepthLevel.LEVEL_5_CORE: 1130,     # Leviathan Awakening (Ultra Milestone), Standard ~12%
}


# Rich metadata for UI, rendering, audio cues, and state machine transitions
DEPTH_METADATA: Dict[DepthLevel, Dict[str, Any]] = {
    DepthLevel.LEVEL_0_SUNLIGHT: {
        "name": "Sunlight Zone",
        "depth_meters": 0,
        "color_theme": "#1B3B5F",
        "ambient_lighting": 1.0,
        "creature_footprint": (0, 0),
        "purged_symbols": [],
        "spins_awarded_natural": 0,
        "audio_cue": "AMBIENT_SURFACE_WATERS",
        "description": "Clear shallow waters. All 11 symbols active on 5x5 grid."
    },
    DepthLevel.LEVEL_1_TWILIGHT: {
        "name": "Twilight Zone",
        "depth_meters": 500,
        "color_theme": "#0A2239",
        "ambient_lighting": 0.8,
        "creature_footprint": (1, 1),
        "purged_symbols": [SymbolType.LOW_10],
        "spins_awarded_natural": 1,
        "audio_cue": "CREAKING_HULL_TWILIGHT",
        "description": "Low 10 removed. 1x1 Lurker Maw attacks on stall to eat lows and transmute to mid equipment (+1 spin)."
    },
    DepthLevel.LEVEL_2_MIDNIGHT: {
        "name": "Midnight Zone",
        "depth_meters": 2000,
        "color_theme": "#04101E",
        "ambient_lighting": 0.6,
        "creature_footprint": (2, 1),
        "purged_symbols": [SymbolType.LOW_10, SymbolType.LOW_J],
        "spins_awarded_natural": 1,
        "audio_cue": "DEEP_SUB_BASS_PULSE",
        "description": "Low J removed. 2x1 Tentacle Stalker eats mid equipment and transmutes to high predators (+1 spin)."
    },
    DepthLevel.LEVEL_3_ABYSS: {
        "name": "The Abyssal Plains",
        "depth_meters": 5000,
        "color_theme": "#020810",
        "ambient_lighting": 0.4,
        "creature_footprint": (2, 2),
        "purged_symbols": [SymbolType.LOW_10, SymbolType.LOW_J, SymbolType.LOW_Q],
        "spins_awarded_natural": 4,
        "spins_awarded_buy": 6,
        "audio_cue": "VENT_ERUPTION_WARNING",
        "description": "Low Q removed. Standard Bonus Milestone: 2x2 Maelstrom Wild with multipliers + Hydrothermal Vents erupt under reels 2, 3, 4!"
    },
    DepthLevel.LEVEL_4_HADAL: {
        "name": "Hadal Trench",
        "depth_meters": 8000,
        "color_theme": "#1A050B",
        "ambient_lighting": 0.3,
        "creature_footprint": (3, 3),
        "purged_symbols": [SymbolType.LOW_10, SymbolType.LOW_J, SymbolType.LOW_Q, SymbolType.LOW_K],
        "spins_awarded_natural": 2,
        "audio_cue": "EMERGENCY_ALARM_RED",
        "description": "Low K removed. 3x3 Eldritch Tentacles convert a zone to Apex/Squid around a 3x wild."
    },
    DepthLevel.LEVEL_5_CORE: {
        "name": "The Leviathan's Core",
        "depth_meters": 11000,
        "color_theme": "#2A0008",
        "ambient_lighting": 0.2,
        "creature_footprint": (2, 2),
        "purged_symbols": [SymbolType.LOW_10, SymbolType.LOW_J, SymbolType.LOW_Q, SymbolType.LOW_K, SymbolType.LOW_A],
        "spins_awarded_natural": 4,
        "spins_awarded_buy": 8,
        "audio_cue": "LEVIATHAN_ROAR_SHATTER",
        "description": "ULTRA BONUS: Viewport breaks! 6x5 grid (6 reels x 5 rows = 15,625 ways), 100% low runes purged, 2x global multiplier, 2x2 Leviathan wild strike on each dead spin."
    },
}
