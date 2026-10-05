"""Configuration package for The Descent slot engine."""

from slot_engine.config.symbols import (
    SymbolType,
    DepthLevel,
    FeatureBuyType,
    SYMBOL_PAYTABLE,
    SYMBOL_PRESSURE_POINTS,
    DEPTH_LEVEL_THRESHOLDS,
    DEPTH_METADATA,
    GAME_RULES,
)
from slot_engine.config.weights import LEVEL_WEIGHT_DISTRIBUTIONS
from slot_engine.config.rtp_profiles import RTPProfile, RTP_PROFILES, get_active_rtp_profile

__all__ = [
    "SymbolType",
    "DepthLevel",
    "FeatureBuyType",
    "SYMBOL_PAYTABLE",
    "SYMBOL_PRESSURE_POINTS",
    "DEPTH_LEVEL_THRESHOLDS",
    "DEPTH_METADATA",
    "GAME_RULES",
    "LEVEL_WEIGHT_DISTRIBUTIONS",
    "RTPProfile",
    "RTP_PROFILES",
    "get_active_rtp_profile",
]
