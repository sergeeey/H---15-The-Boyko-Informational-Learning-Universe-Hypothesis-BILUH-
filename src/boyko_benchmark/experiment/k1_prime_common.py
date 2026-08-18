"""Shared helpers for the `V5-K1'` family of gates (`docs/v5_spec.md`
Sec7/Sec8/Sec13) -- extracted out of `k1_prime_damage_gate.py` when
`k1_prime_exposure_gate.py` (Sec13, `V5-K1'-Exposure`) needed the exact
same damage/lattice-center/connectivity plumbing, to avoid the
cross-module private-import duplication this project's own reviewer
already flagged once before (`observables/capacity_matching.py`'s
extraction, `docs/assumptions.md` `[A61]`/`[A63]`)."""

import numpy as np

from boyko_benchmark.dynamics.adaptive import StateTrajectory
from boyko_benchmark.dynamics.topology_v5 import BalancedSwapTopologyRule
from boyko_benchmark.graphs.damage import Edge, corrupt_lattice_edges
from boyko_benchmark.graphs.lattice import lattice_coordinates
from boyko_benchmark.observables.propagation_front import hop_distances_from_source
from boyko_benchmark.types import WeightedGraph

K1_DAMAGE_STREAM = 0
K1_TIEBREAK_STREAM = 1
K1_CONTROL_STREAM = 2

MAX_CONNECTIVITY_RETRY_ATTEMPTS = 150
"""Same bounded-retry pattern as `graphs/generators.py`'s own constant
(`[A38]`) -- a disconnected damage draw is not evidence the request is
infeasible, just that this particular draw was unlucky."""


def lattice_center_index(side_length: int) -> int:
    coords = lattice_coordinates(side_length)
    center_coord = np.array([side_length // 2, side_length // 2, side_length // 2])
    return int(np.argmin(np.sum((coords - center_coord) ** 2, axis=1)))


def is_connected(mask: np.ndarray) -> bool:
    return bool(np.all(hop_distances_from_source(mask, 0) != -1))


def damage_until_connected(
    graph: WeightedGraph, rng: np.random.Generator, fraction: float
) -> tuple[WeightedGraph, frozenset[Edge]]:
    """`docs/v5_spec.md` Sec8's explicit precondition: retries
    `corrupt_lattice_edges` (which reuses the same `rng`, so each
    attempt draws fresh internal seeds, not a repeat of the same bad
    draw) until the result is connected, bounded."""
    for _ in range(MAX_CONNECTIVITY_RETRY_ATTEMPTS):
        damaged, damaged_out = corrupt_lattice_edges(graph, rng, fraction)
        if is_connected(damaged.mask):
            return damaged, damaged_out
    raise RuntimeError(
        f"damage_until_connected: no connected damaged draw found after "
        f"{MAX_CONNECTIVITY_RETRY_ATTEMPTS} attempts."
    )


class AccumulatingSwapRule:
    """Delegates to a real `BalancedSwapTopologyRule`, accumulating
    `last_committed`/`last_skipped_count` (per-window snapshots, same
    "last" naming convention as V4's own rules) across the WHOLE run --
    `docs/v5_spec.md` Sec7's `K_skip` is a whole-run fraction, not a
    per-window one. Same instrumenting-wrapper pattern K1c's
    `_InstrumentedBoundedRule` used, duck-typed against
    `StatefulTopologyRule`. Shared by `k1_prime_damage_gate.py` (K1')
    and `k1_prime_exposure_gate.py` (Sec13) -- both need the SAME
    running-total semantics, `k1_prime_exposure_gate.py` additionally
    reads `total_committed`/`total_skipped` mid-run at each checkpoint.
    """

    def __init__(self, inner: BalancedSwapTopologyRule) -> None:
        self._inner = inner
        self.total_committed = 0
        self.total_skipped = 0

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        result = self._inner.update(graph, trajectory, dtau)
        self.total_committed += len(self._inner.last_committed)
        self.total_skipped += self._inner.last_skipped_count
        return result
