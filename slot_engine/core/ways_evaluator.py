"""243-Ways (and 7,776-Ways) Left-to-Right Evaluation Engine with Multi-Way Multipliers."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from slot_engine.config.symbols import (
    SymbolType,
    SYMBOL_PAYTABLE,
    SYMBOL_PRESSURE_POINTS,
)
from slot_engine.core.grid import GridMatrix, CellCoordinate


@dataclass
class WinResult:
    symbol: SymbolType
    reels_matched: int
    ways_count: int
    base_payout_multiplier: float
    compound_multiplier: float
    total_payout: float
    winning_coordinates: List[CellCoordinate]
    pressure_points: int


@dataclass
class EvaluationSummary:
    total_payout: float
    total_pressure_points: int
    wins: List[WinResult]
    all_winning_coords: Set[CellCoordinate]


class WaysEvaluator:
    """Evaluates left-to-right ways-to-win combinations with Wild substitution and multipliers."""

    def __init__(self, paytable: Optional[Dict[SymbolType, Dict[int, float]]] = None) -> None:
        self.paytable = paytable or SYMBOL_PAYTABLE

    def evaluate(
        self,
        grid: GridMatrix,
        base_bet: float = 1.0,
        column_multipliers: Optional[Dict[int, int]] = None,
        global_multiplier: int = 1,
    ) -> EvaluationSummary:
        """Evaluates the grid for all winning ways.
        
        Args:
            grid: The 2D GridMatrix.
            base_bet: The player's base bet amount.
            column_multipliers: Optional dict mapping column index -> Hydrothermal Vent multiplier.
            global_multiplier: Multiplier accumulated during bonus cascades.
        """
        col_mults = column_multipliers or {}
        wins: List[WinResult] = []
        all_winning_coords: Set[CellCoordinate] = set()
        total_payout: float = 0.0
        total_points: int = 0

        # We evaluate each standard paying symbol (excluding Wild, Token, and Blocker from being the primary match)
        evaluated_symbols = [
            s for s in SymbolType if s not in (SymbolType.WILD_MAW, SymbolType.PEARL_TOKEN, SymbolType.DEAD_SEDIMENT)
        ]

        for target_symbol in evaluated_symbols:
            matching_cells_per_col: List[List[Tuple[int, int, int]]] = []  # (row, col, cell_mult)

            # Traverse reels left to right starting from col 0
            for c in range(grid.cols):
                col_matches: List[Tuple[int, int, int]] = []
                for r in range(grid.rows):
                    cell_sym = grid.get_symbol(r, c)
                    if cell_sym == target_symbol or cell_sym == SymbolType.WILD_MAW:
                        cell_mult = grid.get_multiplier(r, c)
                        col_matches.append((r, c, cell_mult))

                if col_matches:
                    matching_cells_per_col.append(col_matches)
                else:
                    # Break on the first reel with no matches (left-to-right requirement)
                    break

            reels_matched = len(matching_cells_per_col)
            if reels_matched < 3:
                continue  # Minimum 3 consecutive reels required for a payout


            # Check if this symbol pays for this number of reels
            symbol_payout_table = self.paytable.get(target_symbol, {})
            base_multiplier = symbol_payout_table.get(reels_matched, 0.0)
            if base_multiplier <= 0.0:
                continue
                
            # BUG FIX: Prevent pure Wild combinations from paying out for every symbol.
            # A combination must contain at least one instance of the target symbol,
            # UNLESS the target symbol is the highest paying symbol (HIGH_LEVIATHAN),
            # which we use as the default payout for pure Wilds.
            has_target_symbol = False
            for c_idx in range(reels_matched):
                for r, c, _ in matching_cells_per_col[c_idx]:
                    if grid.get_symbol(r, c) == target_symbol:
                        has_target_symbol = True
                        break
                if has_target_symbol:
                    break
                    
            if not has_target_symbol and target_symbol != SymbolType.HIGH_LEVIATHAN:
                continue

            # Calculate total ways and sum of compound path multipliers
            # Calculate total ways and sum of compound path multipliers
            ways_count = 1
            path_multiplier_sum = 1.0
            winning_coords_for_symbol: List[CellCoordinate] = []

            for c_idx in range(reels_matched):
                matches = matching_cells_per_col[c_idx]
                col_vent = col_mults.get(c_idx, 1)
                ways_count *= len(matches)

                col_path_contribution = 0.0
                for r, c, cell_m in matches:
                    winning_coords_for_symbol.append((r, c))
                    all_winning_coords.add((r, c))
                    col_path_contribution += (cell_m * col_vent)

                path_multiplier_sum *= col_path_contribution

            # Total payout for this winning symbol combination
            payout = (base_multiplier * path_multiplier_sum * global_multiplier * base_bet)
            total_payout += payout

            # Nolimit City rule: Points are awarded per winning combination (not per coordinate)
            # Lows = 0 pts, Mids = 1 pt, Highs = 2 pts, Apex = 3 pts
            points_for_win = SYMBOL_PRESSURE_POINTS.get(target_symbol, 0)
            # Wild-assisted win: bonus pressure from the WILD_MAW entry of the points table
            # (previously a hard-coded +1 while the table's WILD_MAW value was never read)
            if any(grid.get_symbol(r, c) == SymbolType.WILD_MAW for r, c in winning_coords_for_symbol):
                points_for_win += SYMBOL_PRESSURE_POINTS.get(SymbolType.WILD_MAW, 0)
            total_points += points_for_win

            wins.append(
                WinResult(
                    symbol=target_symbol,
                    reels_matched=reels_matched,
                    ways_count=ways_count,
                    base_payout_multiplier=base_multiplier,
                    compound_multiplier=path_multiplier_sum * global_multiplier,
                    total_payout=round(payout, 4),
                    winning_coordinates=winning_coords_for_symbol,
                    pressure_points=points_for_win,
                )
            )

        return EvaluationSummary(
            total_payout=round(total_payout, 4),
            total_pressure_points=total_points,
            wins=wins,
            all_winning_coords=all_winning_coords,
        )
