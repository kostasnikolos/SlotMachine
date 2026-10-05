"""Grid Matrix data structure with 2D gravity drops, refills, and cell mutation tracking."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from slot_engine.config.symbols import SymbolType, DepthLevel
from slot_engine.config import weights as _weights
from slot_engine.core.rng import SlotRNG

CellCoordinate = Tuple[int, int]  # (row, col)


@dataclass
class CascadeDropEvent:
    removed_coords: List[CellCoordinate]
    shifted_cells: List[Dict[str, Any]]   # from_coord, to_coord, symbol
    newly_dropped: List[Dict[str, Any]]   # coord, symbol, has_pearl


class GridMatrix:
    """Represents the 2D grid matrix of reels and rows."""

    def __init__(self, rows: int = 5, cols: int = 5) -> None:
        self.rows: int = rows
        self.cols: int = cols
        self.cells: List[List[SymbolType]] = [
            [SymbolType.LOW_10 for _ in range(cols)] for _ in range(rows)
        ]
        self.multipliers: Dict[CellCoordinate, int] = {}
        self.pearl_tokens: Set[CellCoordinate] = set()

    def populate(self, rng: SlotRNG, level: DepthLevel, is_bonus: bool = False) -> None:
        """Fill all cells with symbols sampled from the active depth level's weights."""
        self.multipliers.clear()
        self.pearl_tokens.clear()
        for r in range(self.rows):
            for c in range(self.cols):
                sym = rng.sample_symbol(level)
                self.cells[r][c] = sym
                if is_bonus and rng.random_float() < _weights.BONUS_PEARL_TOKEN_PROBABILITY:
                    self.pearl_tokens.add((r, c))

    def get_symbol(self, row: int, col: int) -> SymbolType:
        return self.cells[row][col]

    def set_symbol(self, row: int, col: int, symbol: SymbolType) -> None:
        self.cells[row][col] = symbol

    def set_multiplier(self, row: int, col: int, multiplier: int) -> None:
        if multiplier > 1:
            self.multipliers[(row, col)] = multiplier
        elif (row, col) in self.multipliers:
            del self.multipliers[(row, col)]

    def get_multiplier(self, row: int, col: int) -> int:
        return self.multipliers.get((row, col), 1)

    def has_pearl(self, row: int, col: int) -> bool:
        return (row, col) in self.pearl_tokens

    def expand_grid(self, new_rows: int, new_cols: int, rng: SlotRNG, level: DepthLevel) -> None:
        """Expands the matrix (e.g., from 5x5 to 6x5 in Ultra Bonus)."""
        new_cells: List[List[SymbolType]] = []
        for r in range(new_rows):
            row_symbols: List[SymbolType] = []
            for c in range(new_cols):
                if r < self.rows and c < self.cols:
                    row_symbols.append(self.cells[r][c])
                else:
                    row_symbols.append(rng.sample_symbol(level))
            new_cells.append(row_symbols)
        self.rows = new_rows
        self.cols = new_cols
        self.cells = new_cells

    def destroy_and_cascade(
        self,
        winning_coords: Set[CellCoordinate],
        rng: SlotRNG,
        level: DepthLevel,
        is_bonus: bool = False
    ) -> CascadeDropEvent:
        """Executes column-by-column gravity drop for destroyed symbols and refills from top.
        
        Returns a CascadeDropEvent containing exact animation transition coordinates.
        """
        total_destroyed = set(winning_coords)
        for r, c in winning_coords:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.cells[nr][nc] == SymbolType.DEAD_SEDIMENT:
                        total_destroyed.add((nr, nc))

        removed_list = sorted(list(total_destroyed))
        shifted_cells: List[Dict[str, Any]] = []
        newly_dropped: List[Dict[str, Any]] = []

        # Remove multipliers & pearl tokens from destroyed cells
        for coord in total_destroyed:
            self.multipliers.pop(coord, None)
            self.pearl_tokens.discard(coord)

        # Process column by column
        for c in range(self.cols):
            # Collect surviving symbols from bottom up
            surviving: List[Tuple[SymbolType, int, Optional[int], bool]] = []
            for r in range(self.rows - 1, -1, -1):
                if (r, c) not in total_destroyed:
                    sym = self.cells[r][c]
                    mult = self.multipliers.get((r, c))
                    has_p = (r, c) in self.pearl_tokens
                    surviving.append((sym, r, mult, has_p))

            # Clear column multipliers & pearls for recalculation
            for r in range(self.rows):
                self.multipliers.pop((r, c), None)
                self.pearl_tokens.discard((r, c))

            # Place surviving symbols starting from bottom
            target_row = self.rows - 1
            for sym, orig_row, mult, has_p in surviving:
                if orig_row != target_row:
                    shifted_cells.append({
                        "from": (orig_row, c),
                        "to": (target_row, c),
                        "symbol": sym.value,
                    })
                self.cells[target_row][c] = sym
                if mult and mult > 1:
                    self.multipliers[(target_row, c)] = mult
                if has_p:
                    self.pearl_tokens.add((target_row, c))
                target_row -= 1

            # Fill remaining empty spaces at top of column with new symbols
            while target_row >= 0:
                new_sym = rng.sample_symbol(level)
                self.cells[target_row][c] = new_sym
                has_p = False
                if is_bonus and rng.random_float() < _weights.BONUS_PEARL_TOKEN_PROBABILITY:
                    has_p = True
                    self.pearl_tokens.add((target_row, c))

                newly_dropped.append({
                    "coord": (target_row, c),
                    "symbol": new_sym.value,
                    "has_pearl": has_p,
                })
                target_row -= 1

        return CascadeDropEvent(
            removed_coords=removed_list,
            shifted_cells=shifted_cells,
            newly_dropped=newly_dropped,
        )

    def clone(self) -> "GridMatrix":
        """Deep copy of current grid state."""
        cloned = GridMatrix(self.rows, self.cols)
        cloned.cells = [row[:] for row in self.cells]
        cloned.multipliers = dict(self.multipliers)
        cloned.pearl_tokens = set(self.pearl_tokens)
        return cloned

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "rows": self.rows,
            "cols": self.cols,
            "grid": [[sym.value for sym in row] for row in self.cells],
            "multipliers": {f"{r},{c}": m for (r, c), m in self.multipliers.items()},
            "pearl_tokens": [list(coord) for coord in sorted(list(self.pearl_tokens))],
        }
