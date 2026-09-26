import unittest
from slot_engine.config.symbols import SymbolType, DepthLevel, SYMBOL_PAYTABLE
from slot_engine.core.grid import GridMatrix
from slot_engine.core.rng import SlotRNG
from slot_engine.core.ways_evaluator import WaysEvaluator


class TestCoreSlotEngine(unittest.TestCase):

    def test_grid_initialization_and_populate(self):
        rng = SlotRNG(seed=42)
        grid = GridMatrix(rows=5, cols=5)
        grid.populate(rng, DepthLevel.LEVEL_0_SUNLIGHT)

        self.assertEqual(grid.rows, 5)
        self.assertEqual(grid.cols, 5)
        for r in range(5):
            for c in range(5):
                self.assertIsInstance(grid.get_symbol(r, c), SymbolType)

    def test_ways_evaluator_3_reels_match(self):
        grid = GridMatrix(rows=5, cols=5)
        # Clear grid to LOW_10
        for r in range(5):
            for c in range(5):
                grid.set_symbol(r, c, SymbolType.LOW_10)

        # Place HIGH_LEVIATHAN on Reel 0, Reel 1, Reel 2
        grid.set_symbol(0, 0, SymbolType.HIGH_LEVIATHAN)
        grid.set_symbol(1, 1, SymbolType.HIGH_LEVIATHAN)
        grid.set_symbol(2, 2, SymbolType.HIGH_LEVIATHAN)

        evaluator = WaysEvaluator()
        summary = evaluator.evaluate(grid, base_bet=1.0)

        # Must find HIGH_LEVIATHAN 3-reel match and LOW_10 full matches
        lev_wins = [w for w in summary.wins if w.symbol == SymbolType.HIGH_LEVIATHAN]
        self.assertEqual(len(lev_wins), 1)
        self.assertEqual(lev_wins[0].reels_matched, 3)
        self.assertEqual(lev_wins[0].ways_count, 1)
        # 3-reel HIGH_LEVIATHAN pays 0.15x
        self.assertEqual(lev_wins[0].base_payout_multiplier, 0.15)
        # Pressure points for HIGH_LEVIATHAN is 3 per winning combo
        self.assertEqual(lev_wins[0].pressure_points, 3)

    def test_ways_multiplication_with_multiple_symbols_per_reel(self):
        grid = GridMatrix(rows=5, cols=5)
        for r in range(5):
            for c in range(5):
                grid.set_symbol(r, c, SymbolType.LOW_A)

        # Reel 0: 2 HIGH_ANGLER
        grid.set_symbol(0, 0, SymbolType.HIGH_ANGLER)
        grid.set_symbol(1, 0, SymbolType.HIGH_ANGLER)

        # Reel 1: 3 HIGH_ANGLER
        grid.set_symbol(0, 1, SymbolType.HIGH_ANGLER)
        grid.set_symbol(1, 1, SymbolType.HIGH_ANGLER)
        grid.set_symbol(2, 1, SymbolType.HIGH_ANGLER)

        # Reel 2: 1 HIGH_ANGLER
        grid.set_symbol(0, 2, SymbolType.HIGH_ANGLER)

        evaluator = WaysEvaluator()
        summary = evaluator.evaluate(grid, base_bet=2.0)

        angler_wins = [w for w in summary.wins if w.symbol == SymbolType.HIGH_ANGLER]
        self.assertEqual(len(angler_wins), 1)
        # Ways count should be 2 * 3 * 1 = 6 ways!
        self.assertEqual(angler_wins[0].ways_count, 6)
        # 3-reel ANGLER pays 0.08x per way. Total payout = 6 ways * 0.08x * $2.00 bet = $0.96
        self.assertAlmostEqual(angler_wins[0].total_payout, 0.96, places=2)

    def test_cascade_gravity(self):
        rng = SlotRNG(seed=123)
        grid = GridMatrix(rows=5, cols=5)
        for r in range(5):
            for c in range(5):
                grid.set_symbol(r, c, SymbolType.LOW_10)

        # Set bottom cell of column 0 to be destroyed
        grid.set_symbol(4, 0, SymbolType.HIGH_LEVIATHAN)
        winning_coords = {(4, 0)}

        cascade_event = grid.destroy_and_cascade(winning_coords, rng, DepthLevel.LEVEL_0_SUNLIGHT)
        self.assertIn((4, 0), cascade_event.removed_coords)
        self.assertEqual(len(cascade_event.newly_dropped), 1)
        self.assertEqual(cascade_event.newly_dropped[0]["coord"], (0, 0))


if __name__ == "__main__":
    unittest.main()
