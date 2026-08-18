"""`docs/v5_spec.md` Sec15: the Geometry Signal Audit -- runs fast
dynamics + Hebbian adaptation on the UNDAMAGED T7 positive-control
lattice, topology held FROZEN (`IdentityStatefulTopology`), NO damage
step at all (unlike every prior `K1'`-family gate). Since nothing else
in this loop is stochastic (`HebbianAdaptation` has no RNG,
`ClosedUnitaryBackend` with `noise_seed=None`/`gamma=sigma=0` is
deterministic), "trials" here vary the excitation SOURCE NODE rather
than a damage draw -- otherwise 10 identical "seeds" would produce one
identical result, silently, which would misrepresent this as having
10 independent samples when it has exactly 1.
"""

from dataclasses import dataclass

from boyko_benchmark.dynamics.adaptive import (
    HebbianAdaptation,
    StateTrajectory,
    time_averaged_correlation,
    time_averaged_correlation_magnitude,
)
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology_v4 import IdentityStatefulTopology, graph_distance_matrix
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.seed_manager import SeedManager
from boyko_benchmark.experiment.v4_topology_pilot import run_adaptive_dynamics_v4
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice
from boyko_benchmark.observables.geometry_signal_audit import (
    GeometrySignalAuditResult,
    compute_geometry_signal_audit,
)
from boyko_benchmark.types import WeightedGraph

SOURCE_NODE_STREAM = 0


@dataclass(frozen=True)
class GeometryAuditCheckpoint:
    window_count: int
    audit: GeometrySignalAuditResult
    """Based on `Re(<psi_i* psi_j>_K)` -- the SAME convention every
    scorer in this project uses elsewhere. Degenerate on an exactly-
    bipartite lattice, see `audit_magnitude`."""
    audit_magnitude: GeometrySignalAuditResult
    """Based on `|<psi_i* psi_j>_K|` (`time_averaged_correlation_
    magnitude`) -- added 2026-08-18 (reviewer-caught, `[A70]`/`[A71]`)
    specifically because `audit`'s Re-based score is analytically
    forced to ~0 for every cross-parity (d*=1) pair on this project's
    bipartite lattice, REGARDLESS of whether real coupling information
    exists -- not a substitute for `audit`, a companion that isn't
    blind to phase-encoded information."""


@dataclass(frozen=True)
class GeometryAuditTrialResult:
    trial_index: int
    source_node: int
    checkpoints: tuple[GeometryAuditCheckpoint, ...]


def run_geometry_signal_audit_one_trial(
    side_length: int,
    checkpoint_windows: tuple[int, ...],
    eta: float,
    dt: float,
    k: int,
    trial_index: int,
    master_seed: int = 0,
) -> GeometryAuditTrialResult:
    seed_manager = SeedManager(master_seed)
    graph = generate_periodic_cubic_lattice(side_length)
    distances = graph_distance_matrix(graph.mask)

    source_rng = seed_manager.child_generator(trial_index, SOURCE_NODE_STREAM)
    source_node = int(source_rng.integers(0, graph.n_nodes))
    psi0 = localized_psi0(graph.n_nodes, source_node)

    checkpoint_set = set(checkpoint_windows)
    checkpoints: list[GeometryAuditCheckpoint] = []

    def on_window(window_index: int, graph_now: WeightedGraph, trajectory: StateTrajectory) -> None:
        window_count = window_index + 1
        if window_count not in checkpoint_set:
            return
        c_ij = time_averaged_correlation(trajectory)
        c_ij_mag = time_averaged_correlation_magnitude(trajectory)
        audit = compute_geometry_signal_audit(distances, c_ij)
        audit_magnitude = compute_geometry_signal_audit(distances, c_ij_mag)
        checkpoints.append(
            GeometryAuditCheckpoint(
                window_count=window_count, audit=audit, audit_magnitude=audit_magnitude
            )
        )

    run_adaptive_dynamics_v4(
        graph,
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

    return GeometryAuditTrialResult(
        trial_index=trial_index, source_node=source_node, checkpoints=tuple(checkpoints)
    )
