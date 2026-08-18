"""V4-K1c (`docs/v4_spec.md` Sec7d, Revision 2): the same paired A3-vs-A4
damaged-lattice orchestration as `k1_damage_gate.py`, but using
`BoundedIncidenceTopologyRule` and instrumented to compute Sec7d's three
K1c-specific ICE gates (Exposure, Cap Activity) plus P5's cap-enforcement
sanity check and regrowth-concentration logging -- all diagnostic-only
additions layered around the SAME `run_adaptive_dynamics_v4` loop
(reused unchanged, including its existing while-active connectivity
truncation, ICE-2) via a lightweight instrumenting wrapper rather than
a second copy of the fast-dynamics loop.
"""

from dataclasses import dataclass

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation, StateTrajectory
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology_v4 import (
    BoundedIncidenceTopologyRule,
    CorrelationScorer,
    DistanceStratifiedShuffleScorer,
    RegrowScorer,
)
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.seed_manager import SeedManager
from boyko_benchmark.experiment.v4_topology_pilot import run_adaptive_dynamics_v4
from boyko_benchmark.graphs.damage import Edge, corrupt_lattice_edges
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, lattice_coordinates
from boyko_benchmark.observables.edge_recovery import compute_edge_recovery
from boyko_benchmark.types import WeightedGraph

_K1_DAMAGE_STREAM = 0
_K1_TIEBREAK_STREAM = 1
_K1_REGROWTH_STREAM = 2


@dataclass(frozen=True)
class WindowDiagnostic:
    window_index: int
    n_target: int
    n_eligible: int
    n_pruned: int
    max_node_prune: int
    max_node_regrow: int
    max_degree_pre_window: int
    """Highest node degree in the graph BEFORE this window's prune step
    -- an upper bound on any node's `b_i` this window (`b_i <= degree/2`
    at q=0.5), since regrowth is uncapped and can push a node's degree
    above its damage-time starting value (`docs/v4_spec.md` Sec7d:
    "regrowth concentration is logged, not capped") -- P5's `<=3`
    prediction assumes degree stays at the lattice's uniform 6, which
    only holds while regrowth hasn't yet concentrated onto any node."""


def _node_incidence_counts(edges: frozenset[Edge]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for i, j in edges:
        counts[i] = counts.get(i, 0) + 1
        counts[j] = counts.get(j, 0) + 1
    return counts


class _InstrumentedBoundedRule:
    """Delegates to a real `BoundedIncidenceTopologyRule`, recording one
    `WindowDiagnostic` per `update()` call -- satisfies `StatefulTopology
    Rule`'s Protocol structurally (duck-typed), so `run_adaptive_
    dynamics_v4` can drive it exactly as it would the undecorated rule,
    including that loop's own while-active truncation on disconnection.
    """

    def __init__(self, inner: BoundedIncidenceTopologyRule, rho: float) -> None:
        self._inner = inner
        self._rho = rho
        self._window_index = 0
        self.diagnostics: list[WindowDiagnostic] = []

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        n_edges = int(graph.mask.sum()) // 2
        n_target = max(1, round(self._rho * n_edges)) if n_edges > 0 else 0
        max_degree_pre_window = int(graph.mask.sum(axis=1).max()) if graph.n_nodes > 0 else 0

        result = self._inner.update(graph, trajectory, dtau)

        prune_counts = _node_incidence_counts(self._inner.last_pruned)
        regrow_counts = _node_incidence_counts(self._inner.last_regrown)
        self.diagnostics.append(
            WindowDiagnostic(
                window_index=self._window_index,
                n_target=n_target,
                n_eligible=len(self._inner.last_eligible),
                n_pruned=len(self._inner.last_pruned),
                max_node_prune=max(prune_counts.values(), default=0),
                max_node_regrow=max(regrow_counts.values(), default=0),
                max_degree_pre_window=max_degree_pre_window,
            )
        )
        self._window_index += 1
        return result


@dataclass(frozen=True)
class K1cArmResult:
    r_edge: float
    wrong_removal_rate: float
    truncated_at_window: int | None
    diagnostics: tuple[WindowDiagnostic, ...]


@dataclass(frozen=True)
class K1cSeedResult:
    seed_index: int
    damaged_out: frozenset[Edge]
    arm_a3: K1cArmResult
    arm_a4: K1cArmResult


def _lattice_center_index(side_length: int) -> int:
    coords = lattice_coordinates(side_length)
    center_coord = np.array([side_length // 2, side_length // 2, side_length // 2])
    return int(np.argmin(np.sum((coords - center_coord) ** 2, axis=1)))


def _run_one_arm(
    damaged_graph: WeightedGraph,
    original_edges: frozenset[Edge],
    damaged_out: frozenset[Edge],
    psi0: np.ndarray,
    rho: float,
    m: int,
    q: float,
    regrow_scorer: RegrowScorer,
    tiebreak_seed: int,
    regrowth_seed: int,
    eta: float,
    dt: float,
    k: int,
    dtau_steps: int,
) -> K1cArmResult:
    rule = BoundedIncidenceTopologyRule(
        rho=rho,
        m=m,
        q=q,
        regrow_scorer=regrow_scorer,
        topology_tiebreak_seed=tiebreak_seed,
        control_regrowth_seed=regrowth_seed,
    )
    instrumented = _InstrumentedBoundedRule(rule, rho)
    result = run_adaptive_dynamics_v4(
        damaged_graph,
        psi0,
        HebbianAdaptation(eta=eta),
        instrumented,
        dt,
        k,
        dtau_steps,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )
    recovery = compute_edge_recovery(original_edges, damaged_out, result.final_graph.mask)
    return K1cArmResult(
        r_edge=recovery.r_edge,
        wrong_removal_rate=recovery.wrong_removal_rate,
        truncated_at_window=result.truncated_at_window,
        diagnostics=tuple(instrumented.diagnostics),
    )


def run_k1c_gate_one_seed(
    side_length: int,
    damage_fraction: float,
    rho: float,
    m: int,
    q: float,
    eta: float,
    dt: float,
    k: int,
    dtau_steps: int,
    seed_index: int,
    master_seed: int = 0,
) -> K1cSeedResult:
    seed_manager = SeedManager(master_seed)
    graph = generate_periodic_cubic_lattice(side_length)
    original_edges = frozenset((int(i), int(j)) for i, j in np.argwhere(np.triu(graph.mask)))
    center_index = _lattice_center_index(side_length)
    psi0 = localized_psi0(graph.n_nodes, center_index)

    damage_rng = seed_manager.child_generator(seed_index, _K1_DAMAGE_STREAM)
    damaged_graph, damaged_out = corrupt_lattice_edges(graph, damage_rng, damage_fraction)

    tiebreak_seed = int(
        seed_manager.child_seed(seed_index, _K1_TIEBREAK_STREAM).generate_state(1)[0]
    )
    regrowth_seed = int(
        seed_manager.child_seed(seed_index, _K1_REGROWTH_STREAM).generate_state(1)[0]
    )

    arm_a3 = _run_one_arm(
        damaged_graph,
        original_edges,
        damaged_out,
        psi0,
        rho,
        m,
        q,
        CorrelationScorer(),
        tiebreak_seed,
        regrowth_seed,
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
        rho,
        m,
        q,
        DistanceStratifiedShuffleScorer(CorrelationScorer()),
        tiebreak_seed,
        regrowth_seed,
        eta,
        dt,
        k,
        dtau_steps,
    )

    return K1cSeedResult(
        seed_index=seed_index, damaged_out=damaged_out, arm_a3=arm_a3, arm_a4=arm_a4
    )
