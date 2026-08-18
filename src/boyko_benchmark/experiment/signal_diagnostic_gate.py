"""`docs/v5_spec.md` Sec14: the C_ij Recall@D/AUPRC signal diagnostic --
H1 (signal problem) vs H2 (operator problem) after `[A68]`'s FAIL.

Runs fast dynamics + Hebbian adaptation on the DAMAGED graph with
topology held FROZEN (`IdentityStatefulTopology`) -- no swap operator
involved at all, so this is far cheaper than `K1'`/`K1'-Exposure`'s own
`O(|E|^2)` candidate enumeration cost (`[A65]`). Reuses `run_adaptive_
dynamics_v4`'s `on_window` hook (now trajectory-aware) to compute
`C_ij` and the signal diagnostic at each checkpoint from a single
continuous run per seed, same discipline as `k1_prime_exposure_gate.py`.
"""

from dataclasses import dataclass

from boyko_benchmark.dynamics.adaptive import (
    HebbianAdaptation,
    StateTrajectory,
    time_averaged_correlation,
)
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology_v4 import IdentityStatefulTopology
from boyko_benchmark.experiment.k1_prime_common import (
    K1_DAMAGE_STREAM,
    damage_until_connected,
    lattice_center_index,
)
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.seed_manager import SeedManager
from boyko_benchmark.experiment.v4_topology_pilot import run_adaptive_dynamics_v4
from boyko_benchmark.graphs.damage import Edge
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice
from boyko_benchmark.observables.signal_diagnostic import compute_signal_diagnostic
from boyko_benchmark.types import WeightedGraph


@dataclass(frozen=True)
class SignalDiagnosticCheckpoint:
    window_count: int
    recall_at_d: float
    auprc: float
    baseline_recall: float
    baseline_auprc: float
    d: int
    n_candidates: int


@dataclass(frozen=True)
class SignalDiagnosticSeedResult:
    seed_index: int
    damaged_out: frozenset[Edge]
    checkpoints: tuple[SignalDiagnosticCheckpoint, ...]


def run_signal_diagnostic_one_seed(
    side_length: int,
    damage_fraction: float,
    checkpoint_windows: tuple[int, ...],
    eta: float,
    dt: float,
    k: int,
    seed_index: int,
    master_seed: int = 0,
) -> SignalDiagnosticSeedResult:
    seed_manager = SeedManager(master_seed)
    graph = generate_periodic_cubic_lattice(side_length)
    center_index = lattice_center_index(side_length)
    psi0 = localized_psi0(graph.n_nodes, center_index)

    damage_rng = seed_manager.child_generator(seed_index, K1_DAMAGE_STREAM)
    damaged_graph, damaged_out = damage_until_connected(graph, damage_rng, damage_fraction)

    checkpoint_set = set(checkpoint_windows)
    checkpoints: list[SignalDiagnosticCheckpoint] = []

    def on_window(window_index: int, graph_now: WeightedGraph, trajectory: StateTrajectory) -> None:
        window_count = window_index + 1
        if window_count not in checkpoint_set:
            return
        c_ij = time_averaged_correlation(trajectory)
        diag = compute_signal_diagnostic(graph_now.mask, c_ij, damaged_out)
        checkpoints.append(
            SignalDiagnosticCheckpoint(
                window_count=window_count,
                recall_at_d=diag.recall_at_d,
                auprc=diag.auprc,
                baseline_recall=diag.baseline_recall,
                baseline_auprc=diag.baseline_auprc,
                d=diag.d,
                n_candidates=diag.n_candidates,
            )
        )

    run_adaptive_dynamics_v4(
        damaged_graph,
        psi0,
        HebbianAdaptation(eta=eta),
        IdentityStatefulTopology(),
        dt,
        k,
        max(checkpoint_windows),
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
        on_window=on_window,
    )

    return SignalDiagnosticSeedResult(
        seed_index=seed_index, damaged_out=damaged_out, checkpoints=tuple(checkpoints)
    )
