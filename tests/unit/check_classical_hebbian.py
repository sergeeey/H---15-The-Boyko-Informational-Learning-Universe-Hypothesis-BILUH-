"""Unit tests for ClassicalHebbianAdaptation (Arm CD, [A18]).

A subclass of HebbianAdaptation with no new logic -- these tests confirm
the classical-carrier substitution behaves as the contract's own
sign-asymmetry note describes: p_i*p_j is always non-negative (unlike
quantum Re(psi_i* psi_j), which can be negative).
"""

import numpy as np

from boyko_benchmark.dynamics.adaptive import ClassicalHebbianAdaptation, StateTrajectory
from boyko_benchmark.types import WeightedGraph


def _two_node_graph(initial_weight: float) -> WeightedGraph:
    mask = np.array([[False, True], [True, False]])
    weights = np.array([[0.0, initial_weight], [initial_weight, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def _constant_classical_trajectory(p: np.ndarray, n_snapshots: int = 5) -> StateTrajectory:
    """Real p repeated n_snapshots times, cast to complex with zero
    imaginary part -- StateTrajectory is carrier-agnostic by construction
    (mathematical_contract.md's rho notation), reused unchanged."""
    return StateTrajectory(states=np.tile(p.astype(complex), (n_snapshots, 1)))


def test_classical_hebbian_at_oja_fixed_point_leaves_weight_unchanged() -> None:
    """p=(0.5,0.5): p_1*p_2=0.25, density=0.5 each. Fixed point:
    0.25 == W_ij*(0.5+0.5)/2 == W_ij*0.5 -> W_ij=0.5."""
    graph = _two_node_graph(initial_weight=0.5)
    p = np.array([0.5, 0.5])
    trajectory = _constant_classical_trajectory(p)

    updated = ClassicalHebbianAdaptation(eta=0.1).update(graph, trajectory, dtau=1.0)

    np.testing.assert_allclose(updated.weights, graph.weights, atol=1e-12)


def test_classical_hebbian_below_fixed_point_grows_toward_it() -> None:
    graph = _two_node_graph(initial_weight=0.2)
    p = np.array([0.5, 0.5])
    trajectory = _constant_classical_trajectory(p)

    updated = ClassicalHebbianAdaptation(eta=0.1).update(graph, trajectory, dtau=1.0)

    # decay = 0.2*0.5=0.1; delta = 0.1*(0.25-0.1) = 0.015
    assert updated.weights[0, 1] > graph.weights[0, 1]
    np.testing.assert_allclose(updated.weights[0, 1], 0.215, atol=1e-10)


def test_classical_hebbian_never_creates_weight_outside_topology_mask() -> None:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    graph = WeightedGraph(mask=mask, weights=weights)

    p = np.array([0.4, 0.2, 0.4])  # nonzero occupation at both non-adjacent nodes 0,2
    trajectory = _constant_classical_trajectory(p)

    updated = ClassicalHebbianAdaptation(eta=0.5).update(graph, trajectory, dtau=1.0)

    assert updated.weights[0, 2] == 0.0
    assert updated.weights[2, 0] == 0.0


def test_classical_hebbian_never_produces_negative_weight() -> None:
    """Weight well above the Oja fixed point (2.0 vs fixed point 0.5),
    combined with a large eta*dtau step, drives the raw update below zero
    without clamping -- confirms the floor applies to this rule too."""
    graph = _two_node_graph(initial_weight=2.0)
    p = np.array([0.5, 0.5])
    trajectory = _constant_classical_trajectory(p)

    updated = ClassicalHebbianAdaptation(eta=10.0).update(graph, trajectory, dtau=1.0)

    assert updated.weights[0, 1] == 0.0
