"""V3 pilot (`null_results/20260814-open-system-geometrogenesis.md`,
`mathematical_contract.md` Sec3.3 addendum 2026-08-14): the same
adaptive-dynamics loop as `experiment/open_pilot.py::run_adaptive_
dynamics_open`, generalized to also apply a `TopologyUpdateRule` after
each window -- NOT added to `open_pilot.py` itself, following this
project's established pattern of adding new entry points rather than
modifying an existing, already-validated loop (see `open_pilot.py`'s own
docstring for the same rationale relative to `runner.py`).
"""

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import AdaptationRule, StateTrajectory
from boyko_benchmark.dynamics.backend import DynamicsBackend
from boyko_benchmark.dynamics.topology import TopologyUpdateRule
from boyko_benchmark.experiment.runner import ADAPTATION_DTAU, AdaptiveRunResult
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.types import WeightedGraph


def run_adaptive_dynamics_with_topology(
    initial_graph: WeightedGraph,
    psi0: NDArray[np.complexfloating],
    adaptation_rule: AdaptationRule,
    topology_rule: TopologyUpdateRule,
    dt: float,
    k: int,
    dtau_steps: int,
    backend: DynamicsBackend,
    gamma: float,
    sigma: float,
    noise_seed: int | None,
) -> AdaptiveRunResult:
    """Identical to `run_adaptive_dynamics_open` except `topology_rule`
    runs immediately after `adaptation_rule` in every window -- at
    `NoTopologyUpdate` this must reproduce `run_adaptive_dynamics_open`
    exactly (verified by `check_v3_topology_pilot.py`'s wiring test)."""
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
        graph = topology_rule.update(graph, ADAPTATION_DTAU)
        psi = states[-1]
    return AdaptiveRunResult(final_graph=graph, window_trajectories=tuple(window_trajectories))
