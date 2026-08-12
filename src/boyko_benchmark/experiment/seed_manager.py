"""Deterministic seed management [A11].

Child seeds are derived from a master seed via ``numpy.random.SeedSequence``'s
``spawn_key`` constructor argument, keyed by an explicit path (e.g. arm
index, size index, replicate index) rather than by call order. This makes
seed derivation order-independent: requesting the same ``(master_seed,
path)`` pair always yields the same child seed regardless of what other
seeds were requested first, in what order, or in what part of the codebase.
"""

import numpy as np


class SeedManager:
    """Derives reproducible child seeds from a single master seed."""

    def __init__(self, master_seed: int) -> None:
        self._master_seed = master_seed

    def child_seed(self, *path: int) -> np.random.SeedSequence:
        """Return the child SeedSequence for the given path, keyed by path."""
        return np.random.SeedSequence(entropy=self._master_seed, spawn_key=path)

    def child_generator(self, *path: int) -> np.random.Generator:
        """Return a ready-to-use Generator seeded from the given path."""
        return np.random.default_rng(self.child_seed(*path))
