"""V5-K1' (`docs/v5_spec.md` Sec7/Sec8 M2): the damaged-lattice
restoration gate for `BalancedSwapTopologyRule` -- a PAIRED comparison,
A3 (`CorrelationSwapScorer`) vs A4 (`DistanceStratifiedSwapScorer`),
both restoring from the IDENTICAL damaged lattice for a given seed
index. `PASS` requires `R_edge(A3) > R_edge(A4)` (`docs/v5_spec.md`
Sec7).

Reuses V4's damage/`R_edge` infrastructure unchanged (`docs/v5_spec.md`
Sec9: "carries over"), and V4's own `run_adaptive_dynamics_v4` loop --
`BalancedSwapTopologyRule.update(graph, trajectory, dtau) ->
WeightedGraph` matches `StatefulTopologyRule`'s protocol exactly
(duck-typed), so the same validated fast-dynamics/adaptation/topology
loop applies unchanged, even though V5 never needs its while-active
truncation (connectivity cannot be lost by construction, Sec3).

Adds only the connectivity precondition check Sec8 requires --
`corrupt_lattice_edges` does not itself guarantee a connected result,
and V5's whole connectivity argument depends on starting from one.
"""

from dataclasses import dataclass

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation, StateTrajectory
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology_v5 import (
    BalancedSwapTopologyRule,
    CorrelationSwapScorer,
    DistanceStratifiedSwapScorer,
    SwapScorer,
)
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.seed_manager import SeedManager
from boyko_benchmark.experiment.v4_topology_pilot import run_adaptive_dynamics_v4
from boyko_benchmark.graphs.damage import Edge, corrupt_lattice_edges
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, lattice_coordinates
from boyko_benchmark.observables.edge_recovery import compute_edge_recovery
from boyko_benchmark.observables.propagation_front import hop_distances_from_source
from boyko_benchmark.types import WeightedGraph

_K1_DAMAGE_STREAM = 0
_K1_TIEBREAK_STREAM = 1
_K1_CONTROL_STREAM = 2

_MAX_CONNECTIVITY_RETRY_ATTEMPTS = 150
"""Same bounded-retry pattern as `graphs/generators.py`'s own constant
(`[A38]`) -- a disconnected damage draw is not evidence the request is
infeasible, just that this particular draw was unlucky."""


def _lattice_center_index(side_length: int) -> int:
    coords = lattice_coordinates(side_length)
    center_coord = np.array([side_length // 2, side_length // 2, side_length // 2])
    return int(np.argmin(np.sum((coords - center_coord) ** 2, axis=1)))


def _is_connected(mask: np.ndarray) -> bool:
    return bool(np.all(hop_distances_from_source(mask, 0) != -1))


def _damage_until_connected(
    graph: WeightedGraph, rng: np.random.Generator, fraction: float
) -> tuple[WeightedGraph, frozenset[Edge]]:
    """`docs/v5_spec.md` Sec8's explicit precondition: retries
    `corrupt_lattice_edges` (which reuses the same `rng`, so each
    attempt draws fresh internal seeds, not a repeat of the same bad
    draw) until the result is connected, bounded."""
    for _ in range(_MAX_CONNECTIVITY_RETRY_ATTEMPTS):
        damaged, damaged_out = corrupt_lattice_edges(graph, rng, fraction)
        if _is_connected(damaged.mask):
            return damaged, damaged_out
    raise RuntimeError(
        f"_damage_until_connected: no connected damaged draw found after "
        f"{_MAX_CONNECTIVITY_RETRY_ATTEMPTS} attempts."
    )


@dataclass(frozen=True)
class K1PrimeArmResult:
    r_edge: float
    wrong_removal_rate: float
    total_committed: int
    total_skipped: int


@dataclass(frozen=True)
class K1PrimeSeedResult:
    seed_index: int
    damaged_out: frozenset[Edge]
    arm_a3: K1PrimeArmResult
    arm_a4: K1PrimeArmResult


class _AccumulatingSwapRule:
    """Delegates to a real `BalancedSwapTopologyRule`, accumulating
    `last_committed`/`last_skipped_count` (per-window snapshots, same
    "last" naming convention as V4's own rules) across the WHOLE run --
    `docs/v5_spec.md` Sec7's `K_skip` is a whole-run fraction, not a
    per-window one. Same instrumenting-wrapper pattern K1c's `_Instru
    mentedBoundedRule` used, duck-typed against `StatefulTopologyRule`.
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


def _run_one_arm(
    damaged_graph: WeightedGraph,
    original_edges: frozenset[Edge],
    damaged_out: frozenset[Edge],
    psi0: np.ndarray,
    n_swaps: int,
    scorer: SwapScorer,
    tiebreak_seed: int,
    control_seed: int,
    eta: float,
    dt: float,
    k: int,
    dtau_steps: int,
) -> K1PrimeArmResult:
    inner_rule = BalancedSwapTopologyRule(
        n_swaps=n_swaps,
        score_scorer=scorer,
        tiebreak_seed=tiebreak_seed,
        control_seed=control_seed,
    )
    rule = _AccumulatingSwapRule(inner_rule)
    result = run_adaptive_dynamics_v4(
        damaged_graph,
        psi0,
        HebbianAdaptation(eta=eta),
        rule,
        dt,
        k,
        dtau_steps,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )
    recovery = compute_edge_recovery(original_edges, damaged_out, result.final_graph.mask)
    return K1PrimeArmResult(
        r_edge=recovery.r_edge,
        wrong_removal_rate=recovery.wrong_removal_rate,
        total_committed=rule.total_committed,
        total_skipped=rule.total_skipped,
    )


def run_k1_prime_gate_one_seed(
    side_length: int,
    damage_fraction: float,
    n_swaps: int,
    eta: float,
    dt: float,
    k: int,
    dtau_steps: int,
    seed_index: int,
    master_seed: int = 0,
) -> K1PrimeSeedResult:
    seed_manager = SeedManager(master_seed)
    graph = generate_periodic_cubic_lattice(side_length)
    original_edges = frozenset((int(i), int(j)) for i, j in np.argwhere(np.triu(graph.mask)))
    center_index = _lattice_center_index(side_length)
    psi0 = localized_psi0(graph.n_nodes, center_index)

    damage_rng = seed_manager.child_generator(seed_index, _K1_DAMAGE_STREAM)
    damaged_graph, damaged_out = _damage_until_connected(graph, damage_rng, damage_fraction)

    tiebreak_seed = int(
        seed_manager.child_seed(seed_index, _K1_TIEBREAK_STREAM).generate_state(1)[0]
    )
    control_seed = int(seed_manager.child_seed(seed_index, _K1_CONTROL_STREAM).generate_state(1)[0])

    arm_a3 = _run_one_arm(
        damaged_graph,
        original_edges,
        damaged_out,
        psi0,
        n_swaps,
        CorrelationSwapScorer(),
        tiebreak_seed,
        control_seed,
        eta,
        dt,
        k,
        dtau_steps,
    )
    arm_a4 = _run_one_arm(
        damaged_graph,
        original_edges,
        damaged_out,
        psi0,
        n_swaps,
        DistanceStratifiedSwapScorer(CorrelationSwapScorer()),
        tiebreak_seed,
        control_seed,
        eta,
        dt,
        k,
        dtau_steps,
    )

    return K1PrimeSeedResult(
        seed_index=seed_index, damaged_out=damaged_out, arm_a3=arm_a3, arm_a4=arm_a4
    )
