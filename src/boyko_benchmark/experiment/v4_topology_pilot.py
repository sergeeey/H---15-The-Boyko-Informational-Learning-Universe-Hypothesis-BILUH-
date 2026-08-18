"""V4 (`docs/v4_spec.md`): the adaptive-dynamics loop generalized once
more, this time to pass `trajectory` into the topology rule as well as
the adaptation rule -- `StatefulTopologyRule`'s regrow scorers need the
same `C_ij` the adaptation step computes, so `TopologyUpdateRule`'s
`(graph, dtau)` signature (V3's protocol, `dynamics/topology.py`) cannot
carry it. A new entry point, not a change to `open_pilot.py` or
`v3_topology_pilot.py` -- same established pattern in this project of
adding new loop variants rather than modifying an already-validated one.

Also implements `docs/v4_spec.md` Sec3's `while-active` ICE strategy for
disconnection ("Pruning disconnects the graph -> truncate the run at
that window, flag it, report the rate. Never silently reconnect."):
a topology update is checked for connectivity immediately after it
runs, and the loop stops there if it disconnected the graph -- one more
window's fast dynamics would otherwise run on a graph `normalized_
laplacian` isn't well-posed for.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import AdaptationRule, StateTrajectory
from boyko_benchmark.dynamics.backend import DynamicsBackend
from boyko_benchmark.dynamics.topology_v4 import StatefulTopologyRule
from boyko_benchmark.experiment.runner import ADAPTATION_DTAU
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.observables.propagation_front import hop_distances_from_source
from boyko_benchmark.types import WeightedGraph


@dataclass(frozen=True)
class V4AdaptiveRunResult:
    final_graph: WeightedGraph
    window_trajectories: tuple[StateTrajectory, ...]
    truncated_at_window: int | None
    """`docs/v4_spec.md` Sec3's while-active ICE: the 0-indexed window at
    which the topology rule disconnected the graph, or `None` if the run
    completed all `dtau_steps` windows without disconnecting."""


def _is_connected(mask: NDArray[np.bool_]) -> bool:
    return bool(np.all(hop_distances_from_source(mask, 0) != -1))


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
) -> V4AdaptiveRunResult:
    """Identical to `run_adaptive_dynamics_open`/`run_adaptive_dynamics_
    with_topology` except `topology_rule.update` also receives this
    window's `trajectory` -- verified by `check_v4_topology_pilot.py`'s
    wiring test to match `run_adaptive_dynamics_open` exactly when the
    topology rule is a no-op. Truncates early per the while-active ICE
    strategy if a topology update disconnects the graph."""
    graph = initial_graph
    psi = psi0
    window_trajectories: list[StateTrajectory] = []
    truncated_at_window: int | None = None
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
        if not _is_connected(graph.mask):
            truncated_at_window = window_index
            break

    return V4AdaptiveRunResult(
        final_graph=graph,
        window_trajectories=tuple(window_trajectories),
        truncated_at_window=truncated_at_window,
    )
