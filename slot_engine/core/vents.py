"""Hydrothermal Vents column multiplier engine (Print Studios SuperSpinners™ style)."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from slot_engine.config.symbols import DepthLevel
from slot_engine.core.rng import SlotRNG
from slot_engine.config.weights import VENT_ERUPTION_PROBABILITY


@dataclass
class VentEruptionEvent:
    column_index: int
    multiplier: int


class HydrothermalVents:
    """Manages the erupting hydrothermal vents beneath columns 1, 2, and 3 (reels 2, 3, 4)."""

    def __init__(self, eligible_columns: Optional[List[int]] = None) -> None:
        # Columns 1, 2, 3 correspond to the center reels on a 5-column grid (or 6-column grid)
        self.eligible_columns: List[int] = eligible_columns or [1, 2, 3]

    def trigger_eruptions(
        self,
        current_level: DepthLevel,
        is_bonus: bool,
        rng: SlotRNG
    ) -> Dict[int, int]:
        """Determines which vents erupt on this tumble step and returns their multipliers.
        
        Vents activate only starting at Level 3 (The Abyss - 5,000m) or during Free Spins.
        """
        active_vents: Dict[int, int] = {}
        
        # Vents ONLY erupt starting at Level 3 (The Abyssal Plains) and deeper!
        if current_level < DepthLevel.LEVEL_3_ABYSS:
            return active_vents

        # In Level 3+ or bonus, calibrated eruption chance per eligible column
        if current_level == DepthLevel.LEVEL_5_CORE:
            eruption_probability = VENT_ERUPTION_PROBABILITY["core"]
        else:
            eruption_probability = VENT_ERUPTION_PROBABILITY["bonus" if is_bonus else "natural"]

        for col in self.eligible_columns:
            if rng.random_float() < eruption_probability:
                multiplier = rng.sample_vent_multiplier()
                active_vents[col] = multiplier

        return active_vents
