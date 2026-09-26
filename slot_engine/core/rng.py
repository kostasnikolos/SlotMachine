"""RNG Provider with deterministic seeding and cumulative weighted sampling."""

import random
from typing import Dict, List, Optional, Sequence, Tuple, TypeVar
from slot_engine.config.symbols import SymbolType, DepthLevel
from slot_engine.config.weights import LEVEL_WEIGHT_DISTRIBUTIONS, VENT_MULTIPLIER_WEIGHTS

T = TypeVar("T")


class SlotRNG:
    """Deterministic and CSPRNG-capable random generator for the slot engine."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self._seed = seed
        self._rng = random.Random(seed)
        self._cached_weights: Dict[DepthLevel, Tuple[List[SymbolType], List[int]]] = {}
        self._precompute_weights()

    def _precompute_weights(self) -> None:
        """Precomputes lists and cumulative weights for high-throughput sampling."""
        for level, weight_dict in LEVEL_WEIGHT_DISTRIBUTIONS.items():
            symbols: List[SymbolType] = []
            weights: List[int] = []
            for sym, w in weight_dict.items():
                if w > 0:
                    symbols.append(sym)
                    weights.append(w)
            self._cached_weights[level] = (symbols, weights)

    def reseed(self, seed: Optional[int]) -> None:
        """Reset internal generator state with a new seed."""
        self._seed = seed
        self._rng.seed(seed)

    def sample_symbol(self, level: DepthLevel) -> SymbolType:
        """Sample a single symbol according to the active level's weight table."""
        symbols, weights = self._cached_weights[level]
        return self._rng.choices(symbols, weights=weights, k=1)[0]

    def sample_symbols(self, level: DepthLevel, count: int) -> List[SymbolType]:
        """Sample multiple symbols in a single call."""
        symbols, weights = self._cached_weights[level]
        return self._rng.choices(symbols, weights=weights, k=count)

    def sample_vent_multiplier(self) -> int:
        """Sample a Hydrothermal Vent multiplier (2x, 3x, or 5x)."""
        values = [v for v, _ in VENT_MULTIPLIER_WEIGHTS]
        weights = [w for _, w in VENT_MULTIPLIER_WEIGHTS]
        return self._rng.choices(values, weights=weights, k=1)[0]

    def random_choice(self, sequence: Sequence[T]) -> T:
        """Pick a random element uniformly from sequence."""
        return self._rng.choice(sequence)

    def random_sample(self, sequence: Sequence[T], k: int) -> List[T]:
        """Sample k unique elements uniformly without replacement."""
        return self._rng.sample(sequence, k)

    def random_float(self) -> float:
        """Uniform float in [0.0, 1.0)."""
        return self._rng.random()

    def random_int(self, a: int, b: int) -> int:
        """Uniform integer in [a, b]."""
        return self._rng.randint(a, b)
