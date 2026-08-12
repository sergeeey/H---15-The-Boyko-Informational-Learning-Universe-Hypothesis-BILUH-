"""Full [A17] multi-source propagation-front average -- probes an arm's
FINAL adapted graph with a fresh pulse from EACH stored source node, then
averages the resulting r_q(t) trajectories.

[A27] (new, docs/assumptions.md): this measures the FINAL graph's static
propagation-front behavior, not the evolving-during-adaptation trajectory
`gate_a_observables.py`'s single-source G5 uses. Replaying the identical
per-window evolving-Hamiltonian history for the other 4 sources would
need intermediate per-window graphs captured nowhere else in this
codebase -- a materially larger change than this module's own scope. The
final-graph probe answers a well-defined, simpler question ("how does a
fresh pulse spread through the final geometry, averaged over independent
starting points") that satisfies [A17]'s own goal (remove single-node
degree bias) without being numerically identical to a full-history
replay.
"""

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.classical import evolve_classical_trajectory
from boyko_benchmark.dynamics.fast import evolve_trajectory
from boyko_benchmark.experiment.arms_runner import ArmRunResult
from boyko_benchmark.experiment.runner import localized_p0, localized_psi0
from boyko_benchmark.observables.propagation_front import (
    average_over_sources,
    hop_distances_from_source,
    propagation_front_trajectory,
)
from boyko_benchmark.types import WeightedGraph


def compute_g5_multisource(
    arm_result: ArmRunResult,
    laplacian_fn: Callable[[WeightedGraph], NDArray[np.floating]],
    is_classical: bool,
    dt: float,
    n_steps: int,
    q: float,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Returns (mean, std) of r_q(t) across `arm_result.source_nodes`,
    each a fresh pulse on the FINAL graph. `laplacian_fn` selects the
    operator (normalized_laplacian for quantum arms, combinatorial_
    laplacian for Arm CD/the OI-diagnostic's L-driven case); `is_classical`
    selects the carrier (Arm CD only)."""
    graph = arm_result.dynamics_result.final_graph
    laplacian = laplacian_fn(graph)
    trajectories: list[NDArray[np.floating]] = []
    for source_node in arm_result.source_nodes:
        hop_distances = hop_distances_from_source(arm_result.initial_graph.mask, source_node)
        if is_classical:
            p0 = localized_p0(graph.n_nodes, source_node)
            density = evolve_classical_trajectory(laplacian, p0, dt, n_steps)
        else:
            psi0 = localized_psi0(graph.n_nodes, source_node)
            states = evolve_trajectory(laplacian, psi0, dt, n_steps)
            density = np.abs(states) ** 2
        trajectory = propagation_front_trajectory(density, hop_distances, q)
        trajectories.append(trajectory.astype(float))
    return average_over_sources(trajectories)
