"""Phase 11 (open-system pilot ТЗ §21): adaptive-dynamics loop wired to a
swappable `DynamicsBackend`, mirroring `experiment/runner.py::run_
adaptive_dynamics`'s loop structure exactly but NOT modifying that
function (ТЗ §21: "the existing closed backend must not be changed
directly") -- this module is the new, separate open-system entry point.
"""

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import AdaptationRule, StateTrajectory
from boyko_benchmark.dynamics.backend import DynamicsBackend
from boyko_benchmark.experiment.runner import ADAPTATION_DTAU, AdaptiveRunResult
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.types import WeightedGraph


def run_adaptive_dynamics_open(
    initial_graph: WeightedGraph,
    psi0: NDArray[np.complexfloating],
    adaptation_rule: AdaptationRule,
    dt: float,
    k: int,
    dtau_steps: int,
    backend: DynamicsBackend,
    gamma: float,
    sigma: float,
    noise_seed: int | None,
) -> AdaptiveRunResult:
    """Same loop as `run_adaptive_dynamics` (fast dynamics for `k` steps,
    one adaptation update, repeat `dtau_steps` times, `psi` carries over
    between windows) -- generalized only in WHICH backend drives the fast
    dynamics. `hamiltonian_fn` is fixed to `normalized_laplacian` here
    (the Operator-Independence Diagnostic's `combinatorial_laplacian`
    swap is a closed-system-only concern, not yet extended to Phase 11).

    `noise_seed`: per ТЗ §8's independent-seed-spaces requirement, each
    adaptation window gets its own DERIVED sub-seed (via `SeedSequence`
    spawning from the one `noise_seed` passed in) rather than reusing the
    same seed for every window -- pseudo-replication across windows would
    otherwise silently correlate every window's noise draw.
    """
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
        psi = states[-1]
    return AdaptiveRunResult(final_graph=graph, window_trajectories=tuple(window_trajectories))
