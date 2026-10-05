import unittest
from slot_engine.config.symbols import SymbolType, DepthLevel, SYMBOL_PAYTABLE, SYMBOL_PRESSURE_POINTS
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
        # 3-reel HIGH_LEVIATHAN pays (read from the paytable so re-tuning doesn't break the test)
        self.assertEqual(lev_wins[0].base_payout_multiplier, SYMBOL_PAYTABLE[SymbolType.HIGH_LEVIATHAN][3])
        # Pressure points for HIGH_LEVIATHAN per winning combo
        self.assertEqual(lev_wins[0].pressure_points, SYMBOL_PRESSURE_POINTS[SymbolType.HIGH_LEVIATHAN])

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
        # Total payout = 6 ways * 3-reel ANGLER pay * $2.00 bet
        expected = 6 * SYMBOL_PAYTABLE[SymbolType.HIGH_ANGLER][3] * 2.0
        self.assertAlmostEqual(angler_wins[0].total_payout, expected, places=4)

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

    def test_wild_assisted_win_adds_wild_pressure_points(self):
        grid = GridMatrix(rows=5, cols=5)
        for r in range(5):
            for c in range(5):
                grid.set_symbol(r, c, SymbolType.LOW_10)
        grid.set_symbol(0, 0, SymbolType.MID_HELMET)
        grid.set_symbol(0, 1, SymbolType.WILD_MAW)
        grid.set_symbol(0, 2, SymbolType.MID_HELMET)
        summary = WaysEvaluator().evaluate(grid, base_bet=1.0)
        helmet = [w for w in summary.wins if w.symbol == SymbolType.MID_HELMET][0]
        self.assertEqual(
            helmet.pressure_points,
            SYMBOL_PRESSURE_POINTS[SymbolType.MID_HELMET] + SYMBOL_PRESSURE_POINTS[SymbolType.WILD_MAW],
        )

    def test_vents_never_erupt_on_dead_steps_and_cap_emits_final_win(self):
        from slot_engine.config.symbols import FeatureBuyType
        from slot_engine.core.state_machine import SlotStateMachine
        engine = SlotStateMachine(rng=SlotRNG(seed=7))
        for _ in range(200):
            outcome = engine.execute_spin(1.0, FeatureBuyType.STANDARD_BONUS_100X)
            evs = outcome.events
            for i, ev in enumerate(evs):
                if ev.event_type == "VENTS_ERUPTED":
                    self.assertEqual(evs[i + 1].event_type, "WIN_EVALUATION")
                if ev.event_type == "MAX_WIN_CAP_TRIGGERED":
                    self.assertEqual(evs[i - 1].event_type, "WIN_EVALUATION")
                if ev.event_type == "CREATURE_LIFELINE_STRIKE":
                    self.assertEqual(ev.data["respins_awarded"], 0)
            self.assertAlmostEqual(outcome.win_x_base_bet, outcome.total_payout / 1.0, delta=0.006)


if __name__ == "__main__":
    unittest.main()
