"""Core adaptive-dynamics loop (mathematical_contract.md Sec3, [A9]
K-window convention, [A24] dtau=1.0 per adaptation window): interleave K
fast-dynamics steps with one slow-timescale adaptation update, repeated
dtau_steps times.

Two carrier-specific variants, mirroring dynamics/fast.py and dynamics/
classical.py's own separation, rather than one generic parametrized loop
-- the same "don't prematurely unify" choice those two modules already
made for the underlying propagators.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import AdaptationRule, StateTrajectory
from boyko_benchmark.dynamics.classical import evolve_classical_trajectory
from boyko_benchmark.dynamics.fast import evolve_trajectory
from boyko_benchmark.graphs.weights import combinatorial_laplacian, normalized_laplacian
from boyko_benchmark.types import WeightedGraph

ADAPTATION_DTAU: float = 1.0  # [A24] -- degenerate with eta, fixed per window


@dataclass(frozen=True)
class AdaptiveRunResult:
    final_graph: WeightedGraph
    window_trajectories: tuple[StateTrajectory, ...]


def localized_psi0(n_nodes: int, source_node: int) -> NDArray[np.complexfloating]:
    """[A6]: psi(0) = e_k, a single localized excitation at node k."""
    psi0 = np.zeros(n_nodes, dtype=complex)
    psi0[source_node] = 1.0
    return psi0


def localized_p0(n_nodes: int, source_node: int) -> NDArray[np.floating]:
    p0 = np.zeros(n_nodes)
    p0[source_node] = 1.0
    return p0


def run_adaptive_dynamics(
    initial_graph: WeightedGraph,
    psi0: NDArray[np.complexfloating],
    adaptation_rule: AdaptationRule,
    dt: float,
    k: int,
    dtau_steps: int,
    hamiltonian_fn: Callable[[WeightedGraph], NDArray[np.floating]] = normalized_laplacian,
) -> AdaptiveRunResult:
    """Quantum carrier: H(W) = hamiltonian_fn(W) drives fast dynamics
    between adaptation windows (Sec2; Sec5.6's operator-matching rule).
    Default `hamiltonian_fn` is `normalized_laplacian` (L_norm, every
    quantum-carrier arm). The Operator-Independence Diagnostic (Sec5.6,
    Phase 8 Cycle 18) passes `combinatorial_laplacian` instead -- the
    contract's own framing ("H := L ... in place of L_norm") is exactly an
    operator swap on an otherwise-identical loop, not a different loop
    structure, hence a parameter here rather than a duplicated function.
    `psi` carries over as the final state of one window into the next
    window's initial state -- NOT reset to `psi0` every window."""
    graph = initial_graph
    psi = psi0
    window_trajectories: list[StateTrajectory] = []
    for _ in range(dtau_steps):
        hamiltonian = hamiltonian_fn(graph)
        states = evolve_trajectory(hamiltonian, psi, dt, k)
        trajectory = StateTrajectory(states=states)
        window_trajectories.append(trajectory)
        graph = adaptation_rule.update(graph, trajectory, ADAPTATION_DTAU)
        psi = states[-1]
    return AdaptiveRunResult(final_graph=graph, window_trajectories=tuple(window_trajectories))


def run_adaptive_dynamics_classical(
    initial_graph: WeightedGraph,
    p0: NDArray[np.floating],
    adaptation_rule: AdaptationRule,
    dt: float,
    k: int,
    dtau_steps: int,
) -> AdaptiveRunResult:
    """Classical carrier (Arm CD only, [A18]): L(W) combinatorial drives
    diffusion between adaptation windows. `p` is real but stored in a
    complex-typed `StateTrajectory` by the existing dynamics/adaptive.py
    convention (`[A22]` design debt, not introduced here) -- cast
    explicitly; the imaginary part is always exactly zero."""
    graph = initial_graph
    p = p0
    window_trajectories: list[StateTrajectory] = []
    for _ in range(dtau_steps):
        laplacian = combinatorial_laplacian(graph)
        states = evolve_classical_trajectory(laplacian, p, dt, k)
        trajectory = StateTrajectory(states=states.astype(complex))
        window_trajectories.append(trajectory)
        graph = adaptation_rule.update(graph, trajectory, ADAPTATION_DTAU)
        p = states[-1]
    return AdaptiveRunResult(final_graph=graph, window_trajectories=tuple(window_trajectories))
