import re

with open('slot_engine/core/ways_evaluator.py', 'r') as f:
    code = f.read()

replacement = """
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
"""

code = re.sub(
    r'            # Check if this symbol pays for this number of reels\n.*?(?=            # Calculate total ways)',
    replacement,
    code,
    flags=re.DOTALL
)

with open('slot_engine/core/ways_evaluator.py', 'w') as f:
    f.write(code)
