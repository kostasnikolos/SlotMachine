import copy
import unittest

from slot_engine.config.symbols import SymbolType, DepthLevel, FeatureBuyType, GAME_RULES
from slot_engine.config.weights import LEVEL_WEIGHT_DISTRIBUTIONS
from slot_engine.core.grid import GridMatrix
from slot_engine.core.rng import SlotRNG
from slot_engine.core.state_machine import SlotStateMachine
from slot_engine.core.undertow import Undertow


class _RulesPatch:
    """Temporarily override GAME_RULES keys."""

    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        self.saved = {k: copy.deepcopy(GAME_RULES[k]) for k in self.kw}
        GAME_RULES.update(self.kw)

    def __exit__(self, *exc):
        GAME_RULES.update(self.saved)


class TestUndertow(unittest.TestCase):

    def test_strike_replaces_a_block_and_never_touches_wilds(self):
        rng = SlotRNG(seed=3)
        ut = Undertow()
        for _ in range(300):
            grid = GridMatrix(5, 5)
            grid.populate(rng, DepthLevel.LEVEL_0_SUNLIGHT)
            grid.set_symbol(2, 2, SymbolType.WILD_MAW)
            before = grid.clone()
            ev = ut.strike(grid, DepthLevel.LEVEL_0_SUNLIGHT, rng)
            self.assertIsNotNone(ev)
            h, w = ev.size
            self.assertIn((h, w), [(1, 2), (2, 1), (2, 2)])
            r0, c0 = ev.position
            block = {(r0 + dr, c0 + dc) for dr in range(h) for dc in range(w)}
            self.assertNotIn((2, 2), block)
            self.assertEqual({tuple(s["coord"]) for s in ev.swapped}, block)
            for s in ev.swapped:
                r, c = s["coord"]
                self.assertEqual(s["old_symbol"], before.get_symbol(r, c).value)
                self.assertEqual(s["new_symbol"], grid.get_symbol(r, c).value)
                self.assertNotEqual(s["old_symbol"], s["new_symbol"])
            # cells outside the block are untouched
            for r in range(5):
                for c in range(5):
                    if (r, c) not in block:
                        self.assertEqual(grid.get_symbol(r, c), before.get_symbol(r, c))

    def test_strike_respects_purged_symbols_and_6x5_grid(self):
        rng = SlotRNG(seed=11)
        ut = Undertow()
        allowed = LEVEL_WEIGHT_DISTRIBUTIONS[DepthLevel.LEVEL_5_CORE]
        for _ in range(300):
            grid = GridMatrix(5, 6)
            grid.populate(rng, DepthLevel.LEVEL_5_CORE)
            ev = ut.strike(grid, DepthLevel.LEVEL_5_CORE, rng)
            if ev is None:
                continue
            r0, c0 = ev.position
            self.assertLessEqual(r0 + ev.size[0], 5)
            self.assertLessEqual(c0 + ev.size[1], 6)
            for s in ev.swapped:
                self.assertGreater(allowed[SymbolType(s["new_symbol"])], 0)

    def test_no_block_when_grid_is_all_wild(self):
        grid = GridMatrix(5, 5)
        for r in range(5):
            for c in range(5):
                grid.set_symbol(r, c, SymbolType.WILD_MAW)
        self.assertIsNone(Undertow().strike(grid, DepthLevel.LEVEL_0_SUNLIGHT, SlotRNG(seed=1)))

    def test_zero_chance_consumes_no_randomness(self):
        with _RulesPatch(undertow_chance={"base": 0.0, "deep": 0.0, "bonus": 0.0, "core": 0.0}):
            a, b = SlotRNG(seed=5), SlotRNG(seed=5)
            self.assertFalse(Undertow().roll(a, DepthLevel.LEVEL_0_SUNLIGHT, bonus_phase=False))
            self.assertEqual(a.random_float(), b.random_float())

    def test_chance_key_by_phase(self):
        self.assertEqual(Undertow.chance_key(DepthLevel.LEVEL_0_SUNLIGHT, False), "base")
        self.assertEqual(Undertow.chance_key(DepthLevel.LEVEL_1_TWILIGHT, False), "deep")
        self.assertEqual(Undertow.chance_key(DepthLevel.LEVEL_3_ABYSS, True), "bonus")
        self.assertEqual(Undertow.chance_key(DepthLevel.LEVEL_5_CORE, True), "core")
        self.assertEqual(Undertow.chance_key(DepthLevel.LEVEL_5_CORE, False), "core")

    def test_state_machine_event_timeline(self):
        with _RulesPatch(undertow_chance={"base": 1.0, "deep": 1.0, "bonus": 1.0, "core": 1.0}, undertow_max_per_spin=1):
            engine = SlotStateMachine(rng=SlotRNG(seed=21))
            seen = {FeatureBuyType.NONE: 0, FeatureBuyType.STANDARD_BONUS_100X: 0, FeatureBuyType.ULTRA_BONUS_350X: 0}
            for mode in seen:
                for _ in range(40 if mode == FeatureBuyType.NONE else 8):
                    outcome = engine.execute_spin(1.0, mode)
                    evs = outcome.events
                    level, lifeline_seen, per_spin, last_grid = 0, False, 0, None
                    for i, ev in enumerate(evs):
                        t, d = ev.event_type, ev.data
                        if t == "SPIN_STARTED":
                            level, lifeline_seen, per_spin = d["depth_level"], False, 0
                        elif t == "LEVEL_UP":
                            level, lifeline_seen = d["new_level"], False
                        elif t == "ULTRA_ASCENSION_ACHIEVED":
                            level, lifeline_seen = 5, False
                        elif t == "CREATURE_LIFELINE_STRIKE":
                            lifeline_seen = True
                        if t in ("GRID_DROP",):
                            last_grid = d
                        elif t in ("CASCADE_DROP", "CREATURE_LIFELINE_STRIKE"):
                            last_grid = d["grid"]
                        if t != "UNDERTOW":
                            continue
                        seen[mode] += 1
                        per_spin += 1
                        self.assertLessEqual(per_spin, 1)
                        # the lifeline always acts first when it is armed at depth
                        if level >= 1:
                            self.assertTrue(lifeline_seen)
                        self.assertEqual(set(d), {"block", "swapped", "grid"})
                        h, w = d["block"]["size"]
                        self.assertIn(h * w, (2, 4))
                        self.assertEqual(len(d["swapped"]), h * w)
                        g = d["grid"]["grid"]
                        for s in d["swapped"]:
                            r, c = s["coord"]
                            self.assertEqual(g[r][c], s["new_symbol"])
                            self.assertEqual(last_grid["grid"][r][c], s["old_symbol"])
                        last_grid = d["grid"]
                        # the tumble is re-evaluated: a win follows, or the step stays dead
                        self.assertIn(evs[i + 1].event_type, ("VENTS_ERUPTED", "WIN_EVALUATION", "SPIN_STARTED", "SPIN_COMPLETE"))
            for mode, n in seen.items():
                self.assertGreater(n, 0, mode)


if __name__ == "__main__":
    unittest.main()
