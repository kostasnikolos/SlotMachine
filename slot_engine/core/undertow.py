"""The Undertow: a helping feature that drags a small block of symbols under on a dead tumble.

On a stalled tumble (no wins) a 1x2, 2x1 or 2x2 block sinks into the water and fresh symbols
surface in its place (drawn from UNDERTOW_SYMBOL_WEIGHTS), after which the tumble is re-evaluated.
The state machine decides *when* it may act (see GAME_RULES["undertow_*"]); this module only
decides *where* and *what*.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from slot_engine.config.symbols import SymbolType, DepthLevel, GAME_RULES
from slot_engine.config.weights import LEVEL_WEIGHT_DISTRIBUTIONS, UNDERTOW_SYMBOL_WEIGHTS
from slot_engine.core.grid import GridMatrix, CellCoordinate
from slot_engine.core.rng import SlotRNG


@dataclass
class UndertowEvent:
    position: CellCoordinate          # top-left (row, col)
    size: Tuple[int, int]             # (height, width)
    swapped: List[Dict[str, Any]]     # {"coord": (r, c), "old_symbol": str, "new_symbol": str}

    def to_dict(self, grid: GridMatrix) -> Dict[str, Any]:
        return {
            "block": {"position": list(self.position), "size": list(self.size)},
            "swapped": self.swapped,
            "grid": grid.to_dict(),
        }


def _parse_shape(key: str) -> Tuple[int, int]:
    h, w = key.lower().split("x")
    return int(h), int(w)


class Undertow:
    """Sinks a block of symbols and surfaces replacements."""

    @staticmethod
    def chance_key(level: DepthLevel, bonus_phase: bool) -> str:
        """"core" at Level 5 (Ultra / 6x5), "bonus" in free spins, "deep" on a paid spin at
        Level 1-4, else "base" (paid spin at Level 0)."""
        if level == DepthLevel.LEVEL_5_CORE:
            return "core"
        if bonus_phase:
            return "bonus"
        return "deep" if level > DepthLevel.LEVEL_0_SUNLIGHT else "base"

    def roll(self, rng: SlotRNG, level: DepthLevel, bonus_phase: bool) -> bool:
        """True when the undertow triggers on this eligible dead tumble.

        No RNG is consumed when the chance is 0, so a disabled undertow leaves the random
        stream (and every seeded outcome) exactly as before the feature existed.
        """
        chance = GAME_RULES["undertow_chance"][self.chance_key(level, bonus_phase)]
        if chance <= 0:
            return False
        return rng.random_float() < chance

    def strike(self, grid: GridMatrix, level: DepthLevel, rng: SlotRNG) -> Optional[UndertowEvent]:
        """Pick a block that holds no wild and replace its symbols. None if no block fits."""
        shapes = [(_parse_shape(k), w) for k, w in GAME_RULES["undertow_block_weights"].items() if w > 0]
        h, w = rng.weighted_choice([s for s, _ in shapes], [wt for _, wt in shapes])
        # Wilds (and the multipliers that only ride on wilds) are never dragged under: they are
        # the player's help from the lifeline / reels, so the undertow works around them.
        spots = [
            (r, c)
            for r in range(grid.rows - h + 1)
            for c in range(grid.cols - w + 1)
            if all(grid.get_symbol(r + dr, c + dc) != SymbolType.WILD_MAW
                   and (r + dr, c + dc) not in grid.multipliers
                   for dr in range(h) for dc in range(w))
        ]
        if not spots:
            return None
        r0, c0 = rng.random_choice(spots)

        allowed = LEVEL_WEIGHT_DISTRIBUTIONS[level]
        swapped: List[Dict[str, Any]] = []
        for dr in range(h):
            for dc in range(w):
                r, c = r0 + dr, c0 + dc
                old = grid.get_symbol(r, c)
                pool = [(s, wt) for s, wt in UNDERTOW_SYMBOL_WEIGHTS.items()
                        if wt > 0 and s != old and allowed.get(s, 0) > 0]
                new = rng.weighted_choice([s for s, _ in pool], [wt for _, wt in pool])
                grid.set_symbol(r, c, new)
                swapped.append({"coord": (r, c), "old_symbol": old.value, "new_symbol": new.value})

        return UndertowEvent(position=(r0, c0), size=(h, w), swapped=swapped)
