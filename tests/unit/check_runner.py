"""Unit tests for the core K-window adaptive-dynamics loop
(mathematical_contract.md Sec3, [A9], [A24]).

Hand-derived / structurally-derived reference, cross-checked via Bash
prototype before writing these assertions: with `NoAdaptation` (graph
frozen), chaining `dtau_steps` windows of `K` fast-dynamics steps each,
carrying the state forward between windows, must be numerically IDENTICAL
to one single `evolve_trajectory`/`evolve_classical_trajectory` call of
`dtau_steps*K` total steps -- exp(-iHdt)^n = exp(-iH*n*dt) for constant H
(same exactness argument dynamics/fast.py's own docstring already makes,
extended here across a multi-window chain). Verified on the 3-node path
graph (dt=0.1, K=3, dtau_steps=2, psi0/p0 = e_0): window-boundary states
matched the single-shot trajectory's corresponding indices to full
floating-point precision for both carriers.
"""

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation, NoAdaptation
from boyko_benchmark.dynamics.classical import evolve_classical_trajectory
from boyko_benchmark.dynamics.fast import evolve_trajectory
from boyko_benchmark.experiment.runner import (
    AdaptiveRunResult,
    run_adaptive_dynamics,
    run_adaptive_dynamics_classical,
)
from boyko_benchmark.graphs.weights import combinatorial_laplacian, normalized_laplacian
from boyko_benchmark.types import WeightedGraph

_DT = 0.1
_K = 3
_DTAU_STEPS = 2


def _path_graph_3_nodes() -> WeightedGraph:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def test_quantum_loop_with_no_adaptation_matches_single_shot_evolution() -> None:
    graph = _path_graph_3_nodes()
    psi0 = np.array([1.0, 0.0, 0.0], dtype=complex)

    result = run_adaptive_dynamics(graph, psi0, NoAdaptation(), _DT, _K, _DTAU_STEPS)

    hamiltonian = normalized_laplacian(graph)
    single_shot = evolve_trajectory(hamiltonian, psi0, _DT, _DTAU_STEPS * _K)
    np.testing.assert_allclose(
        result.window_trajectories[0].states[_K], single_shot[_K], atol=1e-12
    )
    np.testing.assert_allclose(
        result.window_trajectories[1].states[_K], single_shot[2 * _K], atol=1e-12
    )


def test_quantum_loop_no_adaptation_leaves_graph_unchanged() -> None:
    graph = _path_graph_3_nodes()
    psi0 = np.array([1.0, 0.0, 0.0], dtype=complex)

    result = run_adaptive_dynamics(graph, psi0, NoAdaptation(), _DT, _K, _DTAU_STEPS)

    assert isinstance(result, AdaptiveRunResult)
    np.testing.assert_array_equal(result.final_graph.weights, graph.weights)
    assert len(result.window_trajectories) == _DTAU_STEPS
    for trajectory in result.window_trajectories:
        assert trajectory.states.shape == (_K + 1, 3)


def test_quantum_loop_with_hebbian_adaptation_changes_the_graph() -> None:
    graph = _path_graph_3_nodes()
    psi0 = np.array([1.0, 0.0, 0.0], dtype=complex)

    result = run_adaptive_dynamics(graph, psi0, HebbianAdaptation(eta=0.1), _DT, _K, _DTAU_STEPS)

    assert not np.allclose(result.final_graph.weights, graph.weights)


def test_classical_loop_with_no_adaptation_matches_single_shot_evolution() -> None:
    graph = _path_graph_3_nodes()
    p0 = np.array([1.0, 0.0, 0.0])

    result = run_adaptive_dynamics_classical(graph, p0, NoAdaptation(), _DT, _K, _DTAU_STEPS)

    laplacian = combinatorial_laplacian(graph)
    single_shot = evolve_classical_trajectory(laplacian, p0, _DT, _DTAU_STEPS * _K)
    np.testing.assert_allclose(
        result.window_trajectories[0].states[_K].real, single_shot[_K], atol=1e-12
    )
    np.testing.assert_allclose(
        result.window_trajectories[1].states[_K].real, single_shot[2 * _K], atol=1e-12
    )


def test_classical_loop_conserves_total_probability_across_windows() -> None:
    from boyko_benchmark.dynamics.adaptive import ClassicalHebbianAdaptation

    graph = _path_graph_3_nodes()
    p0 = np.array([1.0, 0.0, 0.0])

    result = run_adaptive_dynamics_classical(
        graph, p0, ClassicalHebbianAdaptation(eta=0.05), _DT, _K, _DTAU_STEPS
    )

    final_p = result.window_trajectories[-1].states[-1].real
    assert abs(np.sum(final_p) - 1.0) < 1e-9
