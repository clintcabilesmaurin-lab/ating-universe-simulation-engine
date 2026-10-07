"""Deterministic seed controller for test reproducibility."""

import random
from typing import Optional


class SeedController:
    """Manages pseudo-random seeds to guarantee reproducible execution paths."""

    def __init__(self, master_seed: int = 42) -> None:
        self.master_seed = master_seed
        self._rng = random.Random(master_seed)
        self._sequence_counter = 0

    def reset(self, new_seed: Optional[int] = None) -> None:
        """Reset the internal RNG to the original master seed or a new seed."""
        if new_seed is not None:
            self.master_seed = new_seed
        self._rng = random.Random(self.master_seed)
        self._sequence_counter = 0

    def get_child_rng(self, subkey: Optional[str] = None) -> random.Random:
        """Derive a reproducible isolated Random instance for a specific subsystem or operation."""
        if subkey is not None:
            # Deterministic hash mixing
            child_seed = (self.master_seed ^ hash(subkey)) & 0xFFFFFFFF
        else:
            self._sequence_counter += 1
            child_seed = self._rng.randint(0, 0xFFFFFFFF)
        return random.Random(child_seed)

    def next_float(self) -> float:
        """Generate next deterministic float in [0.0, 1.0)."""
        return self._rng.random()

    def next_int(self, a: int, b: int) -> int:
        """Generate next deterministic int in [a, b]."""
        return self._rng.randint(a, b)
