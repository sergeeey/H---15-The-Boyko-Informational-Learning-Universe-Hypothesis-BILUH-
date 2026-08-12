"""Computes the five Gate-A observables (mathematical_contract.md Sec5)
from one arm's dynamics result.

Operator-Matching Rule (Sec5, corrected 2026-08-11): G1/G2/G4 use
whichever Laplacian drove that specific run's OWN dynamics -- L_norm for
every quantum-carrier arm except the Operator-Independence Diagnostic,
L (combinatorial) for the Diagnostic and for Arm CD's classical carrier.
G3 always uses the combinatorial L, unconditionally, for every arm
(Sec5.4) -- it does not follow the operator-matching split.

**Scope note (Phase 9 Cycle 21):** G1's spectral dimension is reported as
the raw `d_s(t)` array over a caller-supplied `t_values` grid, NOT
collapsed to a single "plateau" scalar -- picking the right t-range /
plateau-detection heuristic is verdict-machine work (falsification_
gates.md's G1 criterion, Phase 9 Cycle 23), not this wiring step's job.
G5's propagation front uses only the FIRST stored source node (`arm_
result.source_nodes[0]`), reconstructed from the concatenated window
trajectories -- NOT YET the full `[A17]` 5-source average, which needs
additional SeedManager-drawn sources and their own dynamics reruns (a
larger addition, deliberately deferred and flagged here rather than
silently only half-implemented without a note).
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.experiment.arms_runner import ArmRunResult
from boyko_benchmark.graphs.weights import combinatorial_laplacian, normalized_laplacian
from boyko_benchmark.observables.graph_geometry import resistance_diameter
from boyko_benchmark.observables.ipr import inverse_participation_ratio, low_mode_eigenvectors
from boyko_benchmark.observables.laplacian_gap import laplacian_gap
from boyko_benchmark.observables.propagation_front import (
    hop_distances_from_source,
    propagation_front_trajectory,
)
from boyko_benchmark.observables.spectral_dimension import spectral_dimension


@dataclass(frozen=True)
class GateAObservables:
    g1_spectral_dimension: NDArray[np.floating]
    g2_laplacian_gap: float
    g3_resistance_diameter: float
    g4_ipr: float
    g5_propagation_front: NDArray[np.int64]


def _concatenated_density(arm_result: ArmRunResult) -> NDArray[np.floating]:
    """Stitch the per-window trajectories into one continuous rho_i(t)
    series -- window boundaries duplicate a point (window[i]'s last state
    == window[i+1]'s first, verified Phase 8 Cycle 15), so every window
    after the first drops its own first point."""
    windows = arm_result.dynamics_result.window_trajectories
    densities = [np.abs(windows[0].states) ** 2]
    for window in windows[1:]:
        densities.append(np.abs(window.states[1:]) ** 2)
    return np.concatenate(densities, axis=0)


def compute_gate_a_observables(
    arm_result: ArmRunResult,
    is_l_driven: bool,
    t_values: NDArray[np.floating],
    q: float,
) -> GateAObservables:
    """`is_l_driven`: True for the Operator-Independence Diagnostic rerun
    and Arm CD (Classical Diffusion Control); False for every other arm
    (Active, Frozen, Parameter-Matched Random, Topology Scrambled, Fixed
    Flat Geometry, Alternative Objective) -- these are quantum-carrier
    arms whose OWN dynamics used L_norm, per the Operator-Matching Rule.
    """
    graph = arm_result.dynamics_result.final_graph
    dynamics_laplacian = (
        combinatorial_laplacian(graph) if is_l_driven else normalized_laplacian(graph)
    )
    resistance_laplacian = combinatorial_laplacian(graph)

    g1 = spectral_dimension(dynamics_laplacian, t_values)
    g2 = laplacian_gap(dynamics_laplacian)
    g3 = resistance_diameter(resistance_laplacian)
    lowest_mode = low_mode_eigenvectors(dynamics_laplacian, n_modes=1)[:, 0]
    g4 = inverse_participation_ratio(lowest_mode)

    hop_distances = hop_distances_from_source(
        arm_result.initial_graph.mask, arm_result.source_nodes[0]
    )
    density = _concatenated_density(arm_result)
    g5 = propagation_front_trajectory(density, hop_distances, q)

    return GateAObservables(
        g1_spectral_dimension=g1,
        g2_laplacian_gap=g2,
        g3_resistance_diameter=g3,
        g4_ipr=g4,
        g5_propagation_front=g5,
    )
