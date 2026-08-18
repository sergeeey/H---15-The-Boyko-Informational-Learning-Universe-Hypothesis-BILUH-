"""V4 (`docs/v4_spec.md`): the adaptive-dynamics loop generalized once
more, this time to pass `trajectory` into the topology rule as well as
the adaptation rule -- `StatefulTopologyRule`'s regrow scorers need the
same `C_ij` the adaptation step computes, so `TopologyUpdateRule`'s
`(graph, dtau)` signature (V3's protocol, `dynamics/topology.py`) cannot
carry it. A new entry point, not a change to `open_pilot.py` or
`v3_topology_pilot.py` -- same established pattern in this project of
adding new loop variants rather than modifying an already-validated one.
"""

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import AdaptationRule, StateTrajectory
from boyko_benchmark.dynamics.backend import DynamicsBackend
from boyko_benchmark.dynamics.topology_v4 import StatefulTopologyRule
from boyko_benchmark.experiment.runner import ADAPTATION_DTAU, AdaptiveRunResult
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.types import WeightedGraph


def run_adaptive_dynamics_v4(
    initial_graph: WeightedGraph,
    psi0: NDArray[np.complexfloating],
    adaptation_rule: AdaptationRule,
    topology_rule: StatefulTopologyRule,
    dt: float,
    k: int,
    dtau_steps: int,
    backend: DynamicsBackend,
    gamma: float,
    sigma: float,
    noise_seed: int | None,
) -> AdaptiveRunResult:
    """Identical to `run_adaptive_dynamics_open`/`run_adaptive_dynamics_
    with_topology` except `topology_rule.update` also receives this
    window's `trajectory` -- verified by `check_v4_topology_pilot.py`'s
    wiring test to match `run_adaptive_dynamics_open` exactly when the
    topology rule is a no-op."""
    graph = initial_graph
    psi = psi0
    window_trajectories: list[StateTrajectory] = []
    window_seeds: list[int | None]
    if noise_seed is None:
        window_seeds = [None] * dtau_steps
    else:
        seed_sequence = np.random.SeedSequence(noise_seed)
        window_seeds = [
            int(child.generate_state(1)[0]) for child in seed_sequence.spawn(dtau_steps)
        ]

    for window_index in range(dtau_steps):
        hamiltonian = normalized_laplacian(graph)
        states = backend.evolve(hamiltonian, psi, dt, k, gamma, sigma, window_seeds[window_index])
        trajectory = StateTrajectory(states=states)
        window_trajectories.append(trajectory)
        graph = adaptation_rule.update(graph, trajectory, ADAPTATION_DTAU)
        graph = topology_rule.update(graph, trajectory, ADAPTATION_DTAU)
        psi = states[-1]
    return AdaptiveRunResult(final_graph=graph, window_trajectories=tuple(window_trajectories))
