"""`V5-K1'-Exposure` (`docs/v5_spec.md` Sec13): a dose-response follow-up
to `K1'` (`k1_prime_damage_gate.py`) -- was `[A66]`'s weak result caused
by an insufficient number of structural opportunities (starvation), or
does state-driven selection genuinely not beat the matched null even at
`B=D` (as many committed swaps as damaged edges)?

ONE continuous run per arm/seed records `R_edge` and cumulative
committed/skipped counts at several frozen window counts, via
`run_adaptive_dynamics_v4`'s `on_window` hook -- never by restarting the
run at different `dtau_steps` values, which would require ASSUMING (not
verifying) that the first N windows of a longer run reproduce a
standalone N-window run exactly (Sec13.1).
"""

from dataclasses import dataclass

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology_v5 import (
    BalancedSwapTopologyRule,
    CorrelationSwapScorer,
    DistanceStratifiedSwapScorer,
    SwapScorer,
)
from boyko_benchmark.experiment.k1_prime_common import (
    K1_CONTROL_STREAM,
    K1_DAMAGE_STREAM,
    K1_TIEBREAK_STREAM,
    AccumulatingSwapRule,
    damage_until_connected,
    lattice_center_index,
)
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.seed_manager import SeedManager
from boyko_benchmark.experiment.v4_topology_pilot import run_adaptive_dynamics_v4
from boyko_benchmark.graphs.damage import Edge
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice
from boyko_benchmark.observables.edge_recovery import compute_edge_recovery
from boyko_benchmark.types import WeightedGraph


@dataclass(frozen=True)
class K1PrimeExposureCheckpoint:
    window_count: int
    r_edge: float
    wrong_removal_rate: float
    cumulative_committed: int
    cumulative_skipped: int


@dataclass(frozen=True)
class K1PrimeExposureArmResult:
    checkpoints: tuple[K1PrimeExposureCheckpoint, ...]


@dataclass(frozen=True)
class K1PrimeExposureSeedResult:
    seed_index: int
    damaged_out: frozenset[Edge]
    arm_a3: K1PrimeExposureArmResult
    arm_a4: K1PrimeExposureArmResult


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
    checkpoint_windows: tuple[int, ...],
) -> K1PrimeExposureArmResult:
    inner_rule = BalancedSwapTopologyRule(
        n_swaps=n_swaps,
        score_scorer=scorer,
        tiebreak_seed=tiebreak_seed,
        control_seed=control_seed,
    )
    rule = AccumulatingSwapRule(inner_rule)
    checkpoint_set = set(checkpoint_windows)
    checkpoints: list[K1PrimeExposureCheckpoint] = []

    def on_window(window_index: int, graph: WeightedGraph) -> None:
        window_count = window_index + 1
        if window_count not in checkpoint_set:
            return
        recovery = compute_edge_recovery(original_edges, damaged_out, graph.mask)
        checkpoints.append(
            K1PrimeExposureCheckpoint(
                window_count=window_count,
                r_edge=recovery.r_edge,
                wrong_removal_rate=recovery.wrong_removal_rate,
                cumulative_committed=rule.total_committed,
                cumulative_skipped=rule.total_skipped,
            )
        )

    run_adaptive_dynamics_v4(
        damaged_graph,
        psi0,
        HebbianAdaptation(eta=eta),
        rule,
        dt,
        k,
        max(checkpoint_windows),
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
        on_window=on_window,
    )
    return K1PrimeExposureArmResult(checkpoints=tuple(checkpoints))


def run_k1_prime_exposure_gate_one_seed(
    side_length: int,
    damage_fraction: float,
    n_swaps: int,
    checkpoint_windows: tuple[int, ...],
    eta: float,
    dt: float,
    k: int,
    seed_index: int,
    master_seed: int = 0,
) -> K1PrimeExposureSeedResult:
    seed_manager = SeedManager(master_seed)
    graph = generate_periodic_cubic_lattice(side_length)
    original_edges = frozenset((int(i), int(j)) for i, j in np.argwhere(np.triu(graph.mask)))
    center_index = lattice_center_index(side_length)
    psi0 = localized_psi0(graph.n_nodes, center_index)

    damage_rng = seed_manager.child_generator(seed_index, K1_DAMAGE_STREAM)
    damaged_graph, damaged_out = damage_until_connected(graph, damage_rng, damage_fraction)

    tiebreak_seed = int(
        seed_manager.child_seed(seed_index, K1_TIEBREAK_STREAM).generate_state(1)[0]
    )
    control_seed = int(seed_manager.child_seed(seed_index, K1_CONTROL_STREAM).generate_state(1)[0])

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
        checkpoint_windows,
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
        checkpoint_windows,
    )

    return K1PrimeExposureSeedResult(
        seed_index=seed_index, damaged_out=damaged_out, arm_a3=arm_a3, arm_a4=arm_a4
    )
