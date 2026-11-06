"""Configurable RTP Profiles and regulatory margin settings for The Descent."""

from dataclasses import dataclass
from typing import Dict, Optional
from slot_engine.config.symbols import FeatureBuyType


# Feature buys are priced in multiples of the base bet. Industry-norm assumption used by the
# calibration (docs/math_calibration.md): every buy returns the SAME RTP as the base game,
# measured against its own price (e.g. ULTRA_BONUS_350X pays ~0.9605 * 350 = 336x bet on average).
FEATURE_BUY_COSTS: Dict[FeatureBuyType, float] = {
    FeatureBuyType.NONE: 1.0,
    FeatureBuyType.XBET_SONAR_2X: 2.0,
    FeatureBuyType.STANDARD_BONUS_100X: 100.0,
    FeatureBuyType.ULTRA_BONUS_350X: 350.0,
    FeatureBuyType.MYSTERY_BUY_200X: 200.0,   # 60% Standard / 40% Ultra: 0.6*100 + 0.4*350 = 200
}


def feature_rtp_target(feature: FeatureBuyType, profile: Optional["RTPProfile"] = None) -> float:
    """Target RTP (fraction of the feature's own cost) for a mode under the active/given profile."""
    prof = profile or get_active_rtp_profile()
    return prof.target_rtp


@dataclass(frozen=True)
class RTPProfile:
    profile_id: str
    name: str
    target_rtp: float
    base_game_rtp_budget: float
    creature_lifeline_rtp_budget: float
    standard_bonus_rtp_budget: float
    ultra_bonus_rtp_budget: float
    hit_frequency_target: float
    max_win_multiplier: float
    description: str


RTP_PROFILES: Dict[str, RTPProfile] = {
    "default": RTPProfile(
        profile_id="default",
        name="Profile A — High Volatility / Industry Standard",
        target_rtp=0.9605,
        # Measured split of base-game RTP after calibration (docs/math_calibration.md):
        # flat Level-0 pays ~1.5%, Level 1-2 descents ~0.5%, natural Level 3-4 rounds ~79%,
        # natural Level 5 (Ultra) rounds ~15%. The base game is feature-driven by design.
        base_game_rtp_budget=0.0150,
        creature_lifeline_rtp_budget=0.0050,
        standard_bonus_rtp_budget=0.7900,
        ultra_bonus_rtp_budget=0.1500,
        # Hit frequency: 30.7% measured after crush depth (features.py); 49% before it (the 28% aspiration was not reachable
        # with 11 symbols on 5 rows; see the trade-off section of docs/math_calibration.md).
        hit_frequency_target=0.31,
        max_win_multiplier=15000.0,
        description="Default high-volatility profile with 15,000x hard cap. Only this profile is calibrated."
    ),
    "regulatory_94": RTPProfile(
        profile_id="regulatory_94",
        name="Profile B — Regulatory / Land-Based Margin",
        target_rtp=0.9410,
        base_game_rtp_budget=0.3200,
        creature_lifeline_rtp_budget=0.1980,
        standard_bonus_rtp_budget=0.2550,
        ultra_bonus_rtp_budget=0.1680,
        hit_frequency_target=0.261,
        max_win_multiplier=15000.0,
        description="Configured for jurisdictions with strict operator margin requirements. NOT yet calibrated: shares the default weights/paytable."
    ),
    "promo_966": RTPProfile(
        profile_id="promo_966",
        name="Profile C — Promo Mode / Player-Friendly",
        target_rtp=0.9660,
        base_game_rtp_budget=0.3400,
        creature_lifeline_rtp_budget=0.2080,
        standard_bonus_rtp_budget=0.2560,
        ultra_bonus_rtp_budget=0.1620,
        hit_frequency_target=0.302,
        max_win_multiplier=15000.0,
        description="High hit-rate profile tuned for promotions, tournaments, and marketing demos. NOT yet calibrated: shares the default weights/paytable."
    ),
}

_ACTIVE_PROFILE_KEY = "default"


def set_active_rtp_profile(profile_key: str) -> None:
    global _ACTIVE_PROFILE_KEY
    if profile_key not in RTP_PROFILES:
        raise ValueError(f"Unknown RTP profile: {profile_key}. Available: {list(RTP_PROFILES.keys())}")
    _ACTIVE_PROFILE_KEY = profile_key


def get_active_rtp_profile() -> RTPProfile:
    return RTP_PROFILES[_ACTIVE_PROFILE_KEY]
