"""Configurable RTP Profiles and regulatory margin settings for The Descent."""

from dataclasses import dataclass
from typing import Dict, Optional


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
        base_game_rtp_budget=0.3350,
        creature_lifeline_rtp_budget=0.2025,
        standard_bonus_rtp_budget=0.2580,
        ultra_bonus_rtp_budget=0.1650,
        hit_frequency_target=0.284,
        max_win_multiplier=15000.0,
        description="Default Nolimit City-style high action profile with 15,000x hard cap."
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
        description="Configured for jurisdictions with strict operator margin requirements."
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
        description="High hit-rate profile tuned for promotions, tournaments, and marketing demos."
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
