"""Master Spin State Machine and Event Timeline Generator for The Descent."""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from slot_engine.config.symbols import (
    SymbolType,
    DepthLevel,
    FeatureBuyType,
    DEPTH_METADATA,
    DEPTH_LEVEL_THRESHOLDS,
)
from slot_engine.config.rtp_profiles import get_active_rtp_profile
from slot_engine.core.grid import GridMatrix, CellCoordinate
from slot_engine.core.rng import SlotRNG
from slot_engine.core.ways_evaluator import WaysEvaluator, EvaluationSummary
from slot_engine.core.creature import LeviathansMaw
from slot_engine.core.vents import HydrothermalVents
from slot_engine.core.progression import DepthGauge


@dataclass
class SpinEvent:
    step: int
    event_type: str
    data: Dict[str, Any]


@dataclass
class SpinOutcome:
    spin_id: str
    bet: float
    feature_type: FeatureBuyType
    total_payout: float
    payout_multiplier: float
    max_win_capped: bool
    final_depth_level: DepthLevel
    depth_name: str
    total_cascades: int
    events: List[SpinEvent]


class SlotStateMachine:
    """Orchestrates the entire spin lifecycle, cascades, lifelines, and bonuses."""

    def __init__(self, rng: Optional[SlotRNG] = None) -> None:
        self.rng = rng or SlotRNG()
        self.evaluator = WaysEvaluator()
        self.vents = HydrothermalVents()
        self.creature = LeviathansMaw()
        self.gauge = DepthGauge()

    def execute_spin(
        self,
        base_bet: float = 1.0,
        feature_buy: FeatureBuyType = FeatureBuyType.NONE
    ) -> SpinOutcome:
        """Executes a complete game round and returns the full JSON-serializable event timeline."""
        spin_id = f"descent_{uuid.uuid4().hex[:12]}"
        rtp_profile = get_active_rtp_profile()
        max_win_cap = base_bet * rtp_profile.max_win_multiplier

        events: List[SpinEvent] = []
        step_counter = 1

        def emit(event_type: str, data: Dict[str, Any]) -> None:
            nonlocal step_counter
            events.append(SpinEvent(step=step_counter, event_type=event_type, data=data))
            step_counter += 1

        # 1. Reset Depth Gauge state for the new spin/round
        self.gauge.reset_for_new_spin(xbet_active=(feature_buy == FeatureBuyType.XBET_SONAR_2X))

        # 2. Initialize Feature Mode or Base Game
        is_bonus = False
        is_ultra = False
        grid_rows, grid_cols = 5, 5

        if feature_buy == FeatureBuyType.XBET_SONAR_2X:
            actual_bet = base_bet * 2.0
            emit("FEATURE_ACTIVATED", {"type": "XBET_SONAR_2X", "cost": actual_bet, "start_level": 1})
        elif feature_buy == FeatureBuyType.STANDARD_BONUS_100X:
            actual_bet = base_bet * 100.0
            is_bonus = True
            self.gauge.starting_level = DepthLevel.LEVEL_3_ABYSS
            self.gauge.current_level = DepthLevel.LEVEL_3_ABYSS
            self.gauge.highest_level = DepthLevel.LEVEL_3_ABYSS
            self.gauge.accumulated_points = DEPTH_LEVEL_THRESHOLDS[DepthLevel.LEVEL_3_ABYSS]
            self.gauge.spins_banked = 6
            emit("FEATURE_ACTIVATED", {"type": "STANDARD_BONUS_100X", "cost": actual_bet, "spins": 6})
        elif feature_buy == FeatureBuyType.ULTRA_BONUS_350X:
            actual_bet = base_bet * 350.0
            is_bonus = True
            is_ultra = True
            grid_cols = 6
            self.gauge.starting_level = DepthLevel.LEVEL_5_CORE
            self.gauge.current_level = DepthLevel.LEVEL_5_CORE
            self.gauge.highest_level = DepthLevel.LEVEL_5_CORE
            self.gauge.accumulated_points = DEPTH_LEVEL_THRESHOLDS[DepthLevel.LEVEL_5_CORE]
            self.gauge.spins_banked = 8
            emit("FEATURE_ACTIVATED", {"type": "ULTRA_BONUS_350X", "cost": actual_bet, "spins": 8, "grid": "6x5"})
            emit("GRID_EXPANSION_6X5", {
                "new_rows": 5,
                "new_cols": 6,
                "new_ways": 7776,
                "doubled_multiplier": 2,
            })
        elif feature_buy == FeatureBuyType.MYSTERY_BUY_200X:
            actual_bet = base_bet * 200.0
            if self.rng.random_float() < 0.40:
                # 40% chance Ultra Bonus (60% Standard) for exact 96% mathematical parity
                is_bonus = True
                is_ultra = True
                grid_cols = 6
                self.gauge.starting_level = DepthLevel.LEVEL_5_CORE
                self.gauge.current_level = DepthLevel.LEVEL_5_CORE
                self.gauge.highest_level = DepthLevel.LEVEL_5_CORE
                self.gauge.accumulated_points = DEPTH_LEVEL_THRESHOLDS[DepthLevel.LEVEL_5_CORE]
                self.gauge.spins_banked = 8
                emit("FEATURE_ACTIVATED", {"type": "MYSTERY_ULTRA_AWARDED", "cost": actual_bet, "spins": 8})
                emit("GRID_EXPANSION_6X5", {
                    "new_rows": 5,
                    "new_cols": 6,
                    "new_ways": 7776,
                    "doubled_multiplier": 2,
                })
            else:
                # 65% chance Standard Bonus
                is_bonus = True
                self.gauge.starting_level = DepthLevel.LEVEL_3_ABYSS
                self.gauge.current_level = DepthLevel.LEVEL_3_ABYSS
                self.gauge.highest_level = DepthLevel.LEVEL_3_ABYSS
                self.gauge.accumulated_points = DEPTH_LEVEL_THRESHOLDS[DepthLevel.LEVEL_3_ABYSS]
                self.gauge.spins_banked = 6
                emit("FEATURE_ACTIVATED", {"type": "MYSTERY_STANDARD_AWARDED", "cost": actual_bet, "spins": 6})
        else:
            actual_bet = base_bet

        grid = GridMatrix(rows=grid_rows, cols=grid_cols)
        total_payout = 0.0
        total_cascades = 0
        max_win_hit = False

        # 2. Main Game Execution Loop (Spins & Cascades)
        while True:
            # Check if this is the start of a free spin from the bank
            is_free_spin = self.gauge.spins_banked > 0
            if is_free_spin:
                self.gauge.consume_spin()

            # Active spin multiplier: base 1x, or 2x in Ultra Mode
            current_spin_base_mult = 2 if (is_ultra or self.gauge.current_level == DepthLevel.LEVEL_5_CORE) else 1
            tumble_step = 0

            # Re-arm the Leviathan creature assistance for every spin at depth!
            if self.gauge.current_level > DepthLevel.LEVEL_0_SUNLIGHT:
                self.gauge.pending_lifeline = True

            current_meta = DEPTH_METADATA[self.gauge.current_level]
            emit("SPIN_STARTED", {
                "is_free_spin": is_free_spin,
                "spins_remaining": self.gauge.spins_banked,
                "depth_level": self.gauge.current_level.value,
                "depth_name": current_meta["name"],
                "depth_meters": current_meta["depth_meters"],
                "spin_multiplier": current_spin_base_mult,
                "accumulated_points": self.gauge.accumulated_points,
                "purged_symbols": [s.value for s in current_meta.get("purged_symbols", [])],
            })

            # Check if entering Ultra Mode (Grid Expansion to 6x5)
            if self.gauge.current_level == DepthLevel.LEVEL_5_CORE and grid.cols < 6:
                grid.expand_grid(5, 6, self.rng, self.gauge.current_level)
                is_ultra = True
                current_spin_base_mult = 2
                emit("GRID_EXPANSION_6X5", {
                    "new_rows": 5,
                    "new_cols": 6,
                    "new_ways": 7776,
                    "doubled_multiplier": 2,
                })

            # Populate initial grid for this spin (Pearls only spawn at Level 3+ or in Bonus mode)
            is_bonus_phase = is_bonus or (self.gauge.current_level >= DepthLevel.LEVEL_3_ABYSS)
            grid.populate(self.rng, self.gauge.current_level, is_bonus=is_bonus_phase)
            emit("GRID_DROP", grid.to_dict())

            # Cascade Tumble Loop for the current spin
            while True:
                total_cascades += 1

                # Hydrothermal Vents check (Only active at Level 3+)
                active_vents = self.vents.trigger_eruptions(
                    self.gauge.current_level,
                    is_bonus=(is_bonus or is_free_spin),
                    rng=self.rng
                )
                if active_vents:
                    emit("VENTS_ERUPTED", {"active_vents": active_vents})

                # Multiplier configuration:
                # Level 5 (Ultra Mode): 2x base multiplier across 6x5 grid (plus Vents & Roaming Wild).
                # Level 0-4: 1x base multiplier (Hydrothermal Vents active at Level 3+).
                if self.gauge.current_level == DepthLevel.LEVEL_5_CORE or is_ultra:
                    active_mult = 2
                else:
                    active_mult = 1

                summary: EvaluationSummary = self.evaluator.evaluate(
                    grid=grid,
                    base_bet=base_bet,
                    column_multipliers=active_vents,
                    global_multiplier=active_mult,
                )

                if summary.wins:
                    total_payout += summary.total_payout
                    tumble_step += 1

                    # Check Max Win Cap
                    if total_payout >= max_win_cap:
                        total_payout = max_win_cap
                        max_win_hit = True
                        emit("MAX_WIN_CAP_TRIGGERED", {"max_win": max_win_cap})
                        break

                    # Emit Win Event
                    # Add points to Depth Gauge
                    level_events = self.gauge.add_points(summary.total_pressure_points)

                    # Emit Win Event with real-time progression telemetry
                    emit("WIN_EVALUATION", {
                        "wins": [
                            {
                                "symbol": w.symbol.value,
                                "reels": w.reels_matched,
                                "ways": w.ways_count,
                                "payout": w.total_payout,
                                "coords": w.winning_coordinates,
                            }
                            for w in summary.wins
                        ],
                        "step_payout": summary.total_payout,
                        "cumulative_payout": total_payout,
                        "points_earned": summary.total_pressure_points,
                        "accumulated_points": self.gauge.accumulated_points,
                        "depth_level": self.gauge.current_level.value,
                        "depth_meters": DEPTH_METADATA[self.gauge.current_level]["depth_meters"],
                        "cascade_multiplier": active_mult,
                    })

                    for lev_ev in level_events:
                        purged_syms = [s.value for s in DEPTH_METADATA[lev_ev.new_level].get("purged_symbols", [])]
                        emit("LEVEL_UP", {
                            "old_level": lev_ev.old_level.value,
                            "new_level": lev_ev.new_level.value,
                            "name": lev_ev.level_name,
                            "depth": lev_ev.depth_meters,
                            "spins_added": lev_ev.spins_awarded,
                            "accumulated_points": self.gauge.accumulated_points,
                            "purged": purged_syms,
                        })

                    # Check for Pearl Tokens collected on winning cells
                    pearls_on_wins = sum(1 for coord in summary.all_winning_coords if grid.has_pearl(*coord))
                    if pearls_on_wins > 0:
                        ascended = self.gauge.add_pearls(pearls_on_wins)
                        emit("PEARLS_COLLECTED", {
                            "pearls_found": pearls_on_wins,
                            "total_pearls": self.gauge.pearls_collected,
                            "ascension_triggered": ascended,
                        })
                        if ascended and not is_ultra:
                            grid.expand_grid(5, 6, self.rng, DepthLevel.LEVEL_5_CORE)
                            is_ultra = True
                            current_spin_base_mult = 2
                            emit("ULTRA_ASCENSION_ACHIEVED", {
                                "doubled_multiplier": 2,
                                "grid": "6x5",
                            })

                    # Destroy winning symbols and cascade gravity drop
                    cascade_event = grid.destroy_and_cascade(
                        summary.all_winning_coords,
                        self.rng,
                        self.gauge.current_level,
                        is_bonus=is_bonus_phase
                    )
                    emit("CASCADE_DROP", {
                        "removed_coords": cascade_event.removed_coords,
                        "shifted_cells": cascade_event.shifted_cells,
                        "newly_dropped": cascade_event.newly_dropped,
                        "grid": grid.to_dict(),
                    })

                else:
                    # Cascade STALLED (No wins found)
                    # Check if pending Lifeline Creature action is available
                    if self.gauge.pending_lifeline and self.gauge.current_level > DepthLevel.LEVEL_0_SUNLIGHT:
                        creature_ev = self.creature.strike_lifeline(grid, self.gauge.current_level, self.rng)
                        if creature_ev:
                            self.gauge.pending_lifeline = False
                            emit("CREATURE_LIFELINE_STRIKE", {
                                "creature": creature_ev.creature_name,
                                "size": creature_ev.size,
                                "position": creature_ev.top_left_coord,
                                "transmuted": creature_ev.transmuted_coords,
                                "respins_awarded": creature_ev.respins_awarded,
                                "grid": grid.to_dict(),
                            })
                            # Re-ignite cascade tumble loop!
                            continue

                    # No more actions for this spin step
                    break

            if max_win_hit:
                break

            # If there are no more banked spins, game round finishes!
            if self.gauge.spins_banked <= 0:
                break

        # 3. Final Settlement
        final_meta = DEPTH_METADATA[self.gauge.current_level]
        emit("SPIN_COMPLETE", {
            "total_payout": round(total_payout, 4),
            "final_multiplier": round(total_payout / actual_bet, 2),
            "final_level": self.gauge.current_level.value,
            "depth_meters": final_meta["depth_meters"],
        })

        return SpinOutcome(
            spin_id=spin_id,
            bet=actual_bet,
            feature_type=feature_buy,
            total_payout=round(total_payout, 4),
            payout_multiplier=round(total_payout / actual_bet, 2),
            max_win_capped=max_win_hit,
            final_depth_level=self.gauge.current_level,
            depth_name=final_meta["name"],
            total_cascades=total_cascades,
            events=events,
        )
