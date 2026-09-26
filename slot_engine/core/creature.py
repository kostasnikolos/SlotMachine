"""The Leviathan's Maw: Evolving roaming predator AI with symbol devouring and transmutation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from slot_engine.config.symbols import (
    SymbolType,
    SymbolCategory,
    SYMBOL_CATEGORIES,
    DepthLevel,
)
from slot_engine.core.grid import GridMatrix, CellCoordinate
from slot_engine.core.rng import SlotRNG


@dataclass
class CreatureActionEvent:
    level: DepthLevel
    creature_name: str
    size: Tuple[int, int]                  # (height, width)
    top_left_coord: CellCoordinate
    consumed_coords: List[CellCoordinate]
    transmuted_coords: List[Dict[str, Any]] # {"coord": (r, c), "old_sym": sym, "new_sym": sym, "multiplier": m}
    respins_awarded: int


class LeviathansMaw:
    """The predatory entity living beneath the grid that strikes when cascades stall."""

    def __init__(self) -> None:
        self.current_position: CellCoordinate = (0, 0)
        self.is_active: bool = False

    def strike_lifeline(
        self,
        grid: GridMatrix,
        level: DepthLevel,
        rng: SlotRNG
    ) -> Optional[CreatureActionEvent]:
        """Executes the predatory strike when a tumble sequence stalls."""
        if level == DepthLevel.LEVEL_0_SUNLIGHT:
            return None

        # Level 1: The Lurker (1x1)
        if level == DepthLevel.LEVEL_1_TWILIGHT:
            return self._execute_level_1_lurker(grid, rng)

        # Level 2: The Stalker (2x1)
        elif level == DepthLevel.LEVEL_2_MIDNIGHT:
            return self._execute_level_2_stalker(grid, rng)

        # Level 3: The Abyssal Maelstrom (2x2)
        elif level == DepthLevel.LEVEL_3_ABYSS:
            return self._execute_level_3_maelstrom(grid, rng)

        # Level 4: The Kraken's Tentacles (3x3)
        elif level == DepthLevel.LEVEL_4_HADAL:
            return self._execute_level_4_tentacles(grid, rng)

        # Level 5: The Leviathan Awakened (2x2 Sticky Roaming Wild)
        elif level == DepthLevel.LEVEL_5_CORE:
            return self._execute_level_5_awakened(grid, rng)

        return None

    def _execute_level_1_lurker(self, grid: GridMatrix, rng: SlotRNG) -> CreatureActionEvent:
        """1x1 Maw eats adjacent Low Runes and transmutes them into Mid Equipment."""
        r = rng.random_int(0, grid.rows - 1)
        c = rng.random_int(0, grid.cols - 1)
        self.current_position = (r, c)

        consumed: List[CellCoordinate] = []
        transmuted: List[Dict[str, Any]] = []

        # Find adjacent low-paying symbols (up, down, left, right)
        adjacent_coords = [
            (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)
        ]
        
        # Place 1x1 Maw at (r, c)
        old_center = grid.get_symbol(r, c)
        grid.set_symbol(r, c, SymbolType.WILD_MAW)
        transmuted.append({
            "coord": (r, c),
            "old_symbol": old_center.value,
            "new_symbol": SymbolType.WILD_MAW.value,
            "multiplier": 1,
        })

        for ar, ac in adjacent_coords:
            if 0 <= ar < grid.rows and 0 <= ac < grid.cols:
                sym = grid.get_symbol(ar, ac)
                if SYMBOL_CATEGORIES.get(sym) == SymbolCategory.LOW:
                    consumed.append((ar, ac))
                    mid_replacement = rng.random_choice([SymbolType.MID_HELMET, SymbolType.MID_COMPASS])
                    grid.set_symbol(ar, ac, mid_replacement)
                    transmuted.append({
                        "coord": (ar, ac),
                        "old_symbol": sym.value,
                        "new_symbol": mid_replacement.value,
                        "multiplier": 1,
                    })

        return CreatureActionEvent(
            level=DepthLevel.LEVEL_1_TWILIGHT,
            creature_name="The Lurker (1x1 Maw)",
            size=(1, 1),
            top_left_coord=(r, c),
            consumed_coords=consumed,
            transmuted_coords=transmuted,
            respins_awarded=2,
        )

    def _execute_level_2_stalker(self, grid: GridMatrix, rng: SlotRNG) -> CreatureActionEvent:
        """2x1 Maw expands, eats Mid Equipment, and transmutes to High Predators."""
        r = rng.random_int(0, grid.rows - 2)
        c = rng.random_int(0, grid.cols - 1)
        self.current_position = (r, c)

        consumed: List[CellCoordinate] = []
        transmuted: List[Dict[str, Any]] = []

        # Maw covers 2 rows on column c
        for maw_r in (r, r + 1):
            old_sym = grid.get_symbol(maw_r, c)
            grid.set_symbol(maw_r, c, SymbolType.WILD_MAW)
            transmuted.append({
                "coord": (maw_r, c),
                "old_symbol": old_sym.value,
                "new_symbol": SymbolType.WILD_MAW.value,
                "multiplier": 1,
            })

        # Scan surrounding 3x3 perimeter for Mid Equipment to devour
        for dr in (-1, 0, 1, 2):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid.rows and 0 <= nc < grid.cols:
                    if (nr, nc) not in [(r, c), (r + 1, c)]:
                        sym = grid.get_symbol(nr, nc)
                        if SYMBOL_CATEGORIES.get(sym) == SymbolCategory.MID:
                            consumed.append((nr, nc))
                            high_rep = rng.random_choice([
                                SymbolType.HIGH_VIPER, SymbolType.HIGH_ANGLER, SymbolType.HIGH_SQUID
                            ])
                            grid.set_symbol(nr, nc, high_rep)
                            transmuted.append({
                                "coord": (nr, nc),
                                "old_symbol": sym.value,
                                "new_symbol": high_rep.value,
                                "multiplier": 1,
                            })

        return CreatureActionEvent(
            level=DepthLevel.LEVEL_2_MIDNIGHT,
            creature_name="The Stalker (2x1 Maw)",
            size=(2, 1),
            top_left_coord=(r, c),
            consumed_coords=consumed,
            transmuted_coords=transmuted,
            respins_awarded=2,
        )

    def _execute_level_3_maelstrom(self, grid: GridMatrix, rng: SlotRNG) -> CreatureActionEvent:
        """2x2 Abyssal Maelstrom: Roams to a 2x2 area, injecting Wild Multipliers (2x-5x)."""
        max_r = grid.rows - 2
        max_c = grid.cols - 2
        r = rng.random_int(0, max_r)
        c = rng.random_int(0, max_c)
        self.current_position = (r, c)

        transmuted: List[Dict[str, Any]] = []

        # Engulf all 4 cells in the 2x2 footprint into Wild Multipliers
        for dr in range(2):
            for dc in range(2):
                cell_r, cell_c = r + dr, c + dc
                old_sym = grid.get_symbol(cell_r, cell_c)
                multiplier = rng.sample_vent_multiplier() # 2x, 3x, or 5x
                grid.set_symbol(cell_r, cell_c, SymbolType.WILD_MAW)
                grid.set_multiplier(cell_r, cell_c, multiplier)
                transmuted.append({
                    "coord": (cell_r, cell_c),
                    "old_symbol": old_sym.value,
                    "new_symbol": SymbolType.WILD_MAW.value,
                    "multiplier": multiplier,
                })

        return CreatureActionEvent(
            level=DepthLevel.LEVEL_3_ABYSS,
            creature_name="Abyssal Maelstrom (2x2 Wild Multiplier)",
            size=(2, 2),
            top_left_coord=(r, c),
            consumed_coords=[],
            transmuted_coords=transmuted,
            respins_awarded=2,
        )

    def _execute_level_4_tentacles(self, grid: GridMatrix, rng: SlotRNG) -> CreatureActionEvent:
        """3x3 Eldritch Tentacles: Covers 3x3 footprint, converting cells to Wilds and Highs."""
        max_r = grid.rows - 3
        max_c = grid.cols - 3
        r = rng.random_int(0, max_r)
        c = rng.random_int(0, max_c)
        self.current_position = (r, c)

        transmuted: List[Dict[str, Any]] = []

        # Center cell is guaranteed Wild 3x, edge cells convert to Apex or Highs
        for dr in range(3):
            for dc in range(3):
                cell_r, cell_c = r + dr, c + dc
                old_sym = grid.get_symbol(cell_r, cell_c)
                if dr == 1 and dc == 1:
                    grid.set_symbol(cell_r, cell_c, SymbolType.WILD_MAW)
                    grid.set_multiplier(cell_r, cell_c, 3)
                    new_sym = SymbolType.WILD_MAW
                    mult = 3
                elif (dr + dc) % 2 == 0:
                    new_sym = SymbolType.HIGH_LEVIATHAN
                    grid.set_symbol(cell_r, cell_c, new_sym)
                    mult = 1
                else:
                    new_sym = SymbolType.HIGH_SQUID
                    grid.set_symbol(cell_r, cell_c, new_sym)
                    mult = 1

                transmuted.append({
                    "coord": (cell_r, cell_c),
                    "old_symbol": old_sym.value,
                    "new_symbol": new_sym.value,
                    "multiplier": mult,
                })

        return CreatureActionEvent(
            level=DepthLevel.LEVEL_4_HADAL,
            creature_name="The Kraken's Grasp (3x3 Tentacle Zone)",
            size=(3, 3),
            top_left_coord=(r, c),
            consumed_coords=[],
            transmuted_coords=transmuted,
            respins_awarded=2,
        )

    def _execute_level_5_awakened(self, grid: GridMatrix, rng: SlotRNG) -> CreatureActionEvent:
        """Level 5 Ultra Bonus: Persistent 2x2 Sticky Roaming Wild with 2x multiplier."""
        max_r = grid.rows - 2
        max_c = grid.cols - 2
        r = rng.random_int(0, max_r)
        c = rng.random_int(0, max_c)
        self.current_position = (r, c)

        transmuted: List[Dict[str, Any]] = []
        for dr in range(2):
            for dc in range(2):
                cell_r, cell_c = r + dr, c + dc
                old_sym = grid.get_symbol(cell_r, cell_c)
                grid.set_symbol(cell_r, cell_c, SymbolType.WILD_MAW)
                grid.set_multiplier(cell_r, cell_c, 2)
                transmuted.append({
                    "coord": (cell_r, cell_c),
                    "old_symbol": old_sym.value,
                    "new_symbol": SymbolType.WILD_MAW.value,
                    "multiplier": 2,
                })

        return CreatureActionEvent(
            level=DepthLevel.LEVEL_5_CORE,
            creature_name="The Leviathan Awakened (2x2 Sticky Roaming)",
            size=(2, 2),
            top_left_coord=(r, c),
            consumed_coords=[],
            transmuted_coords=transmuted,
            respins_awarded=2,
        )
