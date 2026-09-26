"""DepthGauge progression tracker for Pressure Points, Depth Levels, and Free Spins."""

from dataclasses import dataclass
from typing import List, Optional
from slot_engine.config.symbols import DepthLevel, DEPTH_LEVEL_THRESHOLDS, DEPTH_METADATA


@dataclass
class LevelUpEvent:
    old_level: DepthLevel
    new_level: DepthLevel
    level_name: str
    depth_meters: int
    points_required: int
    spins_awarded: int
    unlocked_features: str


class DepthGauge:
    """Tracks the player's bathysphere depth and progressive unlocks."""

    def __init__(self, starting_level: DepthLevel = DepthLevel.LEVEL_0_SUNLIGHT) -> None:
        self.starting_level: DepthLevel = starting_level
        self.current_level: DepthLevel = starting_level
        self.highest_level: DepthLevel = starting_level
        self.accumulated_points: int = 0
        self.spins_banked: int = 0
        self.pending_lifeline: bool = False
        self.pearls_collected: int = 0

    def reset_for_new_spin(self, xbet_active: bool = False) -> None:
        """Reset the gauge for a new paid game round.
        
        If xBet ('Abyssal Sonar') is active, the round begins at Level 1 with 15 pts and +2 spins.
        """
        if xbet_active:
            self.starting_level = DepthLevel.LEVEL_1_TWILIGHT
            self.current_level = DepthLevel.LEVEL_1_TWILIGHT
            self.highest_level = DepthLevel.LEVEL_1_TWILIGHT
            self.accumulated_points = DEPTH_LEVEL_THRESHOLDS[DepthLevel.LEVEL_1_TWILIGHT]
            self.spins_banked = 0
            self.pending_lifeline = True
        else:
            self.starting_level = DepthLevel.LEVEL_0_SUNLIGHT
            self.current_level = DepthLevel.LEVEL_0_SUNLIGHT
            self.highest_level = DepthLevel.LEVEL_0_SUNLIGHT
            self.accumulated_points = 0
            self.spins_banked = 0
            self.pending_lifeline = False

        self.pearls_collected = 0

    def add_points(self, points: int) -> List[LevelUpEvent]:
        """Add pressure points earned from symbol burns and evaluate level-ups."""
        if points <= 0:
            return []

        self.accumulated_points += points
        events: List[LevelUpEvent] = []

        # Check each level threshold sequentially
        for target_level in [
            DepthLevel.LEVEL_1_TWILIGHT,
            DepthLevel.LEVEL_2_MIDNIGHT,
            DepthLevel.LEVEL_3_ABYSS,
            DepthLevel.LEVEL_4_HADAL,
            DepthLevel.LEVEL_5_CORE,
        ]:
            if target_level > self.current_level:
                thresh = DEPTH_LEVEL_THRESHOLDS[target_level]
                if self.accumulated_points >= thresh:
                    meta = DEPTH_METADATA[target_level]
                    spins = meta.get("spins_awarded_natural", 2)
                    self.spins_banked += spins
                    self.pending_lifeline = True
                    old_lvl = self.current_level
                    self.current_level = target_level
                    if target_level > self.highest_level:
                        self.highest_level = target_level

                    events.append(
                        LevelUpEvent(
                            old_level=old_lvl,
                            new_level=target_level,
                            level_name=meta["name"],
                            depth_meters=meta["depth_meters"],
                            points_required=thresh,
                            spins_awarded=spins,
                            unlocked_features=meta["description"],
                        )
                    )

        return events

    def add_pearls(self, count: int) -> bool:
        """Add pearls collected during bonus. Returns True if ascended to Level 5 Ultra."""
        if count <= 0:
            return False

        self.pearls_collected += count
        if self.pearls_collected >= 5 and self.current_level < DepthLevel.LEVEL_5_CORE:
            # Ascend immediately to Level 5!
            self.current_level = DepthLevel.LEVEL_5_CORE
            self.highest_level = DepthLevel.LEVEL_5_CORE
            self.spins_banked += 2  # +2 Oxygen respins awarded upon Ultra Ascension!
            self.pending_lifeline = True
            return True
        return False

    def consume_spin(self) -> bool:
        """Consume 1 banked spin. Returns True if a spin was available."""
        if self.spins_banked > 0:
            self.spins_banked -= 1
            return True
        return False
