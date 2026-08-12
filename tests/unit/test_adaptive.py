"""Unit tests for adaptation rules (mathematical_contract.md Sec3, [A20]).

Test scenario reuses the same 2-node single-edge graph from Phase 2's
test_fast.py. Two hand-picked initial states give exact, hand-computable
correlations because they are EIGENSTATES of the 2-node Hamiltonian
(stationary -- the trajectory never changes), so no numerical integration
error enters the expected values at all:

  psi_a = (1, 1) / sqrt(2)   -- zero-eigenvalue eigenvector
    Re(psi_1* psi_2) = 0.5 for every snapshot -> K-average = 0.5 exactly.
  psi_b = (1, -1) / sqrt(2)  -- eigenvalue-2 eigenvector
    Re(psi_1* psi_2) = -0.5 for every snapshot -> K-average = -0.5 exactly.

Both have density (0.5, 0.5) at every node -- same density, opposite-sign
correlation. This is what makes psi_a/psi_b a clean test pair for "does
AlternativeObjective really ignore phase and Hebbian really doesn't".

With W(0) = 1.0 on the single edge, psi_a is *exactly* the Oja fixed
point of HebbianAdaptation (correlation 0.5 == W_ij * (0.5+0.5)/2 == 0.5),
so the fixed-point test needs no tolerance beyond floating point.
"""

import numpy as np

from boyko_benchmark.dynamics.adaptive import (
    AlternativeObjective,
    AntiHebbianAdaptation,
    HebbianAdaptation,
    NoAdaptation,
    StateTrajectory,
)
from boyko_benchmark.types import WeightedGraph


def _two_node_graph(initial_weight: float) -> WeightedGraph:
    mask = np.array([[False, True], [True, False]])
    weights = np.array([[0.0, initial_weight], [initial_weight, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def _stationary_trajectory(psi: np.ndarray, n_snapshots: int = 5) -> StateTrajectory:
    """psi repeated n_snapshots times -- valid because psi is an eigenstate
    of the 2-node Hamiltonian in these tests, hence truly stationary."""
    return StateTrajectory(states=np.tile(psi, (n_snapshots, 1)))


PSI_SYMMETRIC = np.array([1.0 + 0j, 1.0 + 0j]) / np.sqrt(2)  # correlation = +0.5
PSI_ANTISYMMETRIC = np.array([1.0 + 0j, -1.0 + 0j]) / np.sqrt(2)  # correlation = -0.5


def test_no_adaptation_never_changes_weights() -> None:
    graph = _two_node_graph(initial_weight=1.0)
    trajectory = _stationary_trajectory(PSI_SYMMETRIC)

    updated = NoAdaptation().update(graph, trajectory, dtau=1.0)

    np.testing.assert_array_equal(updated.weights, graph.weights)


def test_hebbian_at_oja_fixed_point_leaves_weight_unchanged() -> None:
    """W=1.0 is exactly the Oja fixed point for correlation=0.5, density=0.5
    each (see module docstring) -- update must be zero, not approximately."""
    graph = _two_node_graph(initial_weight=1.0)
    trajectory = _stationary_trajectory(PSI_SYMMETRIC)

    updated = HebbianAdaptation(eta=0.1).update(graph, trajectory, dtau=1.0)

    np.testing.assert_allclose(updated.weights, graph.weights, atol=1e-12)


def test_hebbian_below_fixed_point_grows_toward_it() -> None:
    graph = _two_node_graph(initial_weight=0.5)
    trajectory = _stationary_trajectory(PSI_SYMMETRIC)

    updated = HebbianAdaptation(eta=0.1).update(graph, trajectory, dtau=1.0)

    # decay_term = 0.5*(0.5+0.5)/2 = 0.25; delta = 0.1*(0.5-0.25) = 0.025
    assert updated.weights[0, 1] > graph.weights[0, 1]
    np.testing.assert_allclose(updated.weights[0, 1], 0.525, atol=1e-10)


def test_hebbian_above_fixed_point_shrinks_toward_it() -> None:
    graph = _two_node_graph(initial_weight=2.0)
    trajectory = _stationary_trajectory(PSI_SYMMETRIC)

    updated = HebbianAdaptation(eta=0.1).update(graph, trajectory, dtau=1.0)

    # decay_term = 2.0*0.5 = 1.0; delta = 0.1*(0.5-1.0) = -0.05
    assert updated.weights[0, 1] < graph.weights[0, 1]
    np.testing.assert_allclose(updated.weights[0, 1], 1.95, atol=1e-10)


def test_hebbian_never_creates_weight_outside_topology_mask() -> None:
    """3-node path (no 0-2 edge); a state with amplitude at both 0 and 2
    creates nonzero correlation there, but weights[0,2] must stay exactly
    zero -- the topology mask, not the correlation value, decides."""
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    graph = WeightedGraph(mask=mask, weights=weights)

    psi = np.array([1.0 + 0j, 0.0 + 0j, 1.0 + 0j]) / np.sqrt(2)
    trajectory = _stationary_trajectory(psi)

    updated = HebbianAdaptation(eta=0.5).update(graph, trajectory, dtau=1.0)

    assert updated.weights[0, 2] == 0.0
    assert updated.weights[2, 0] == 0.0


def test_hebbian_never_produces_negative_weight() -> None:
    """Small initial weight + large eta*dtau against negative correlation
    would drive the raw update below zero without clamping."""
    graph = _two_node_graph(initial_weight=0.01)
    trajectory = _stationary_trajectory(PSI_ANTISYMMETRIC)  # correlation = -0.5

    updated = HebbianAdaptation(eta=1.0).update(graph, trajectory, dtau=1.0)

    assert updated.weights[0, 1] >= 0.0


def test_antihebbian_decreases_weight_when_correlation_positive() -> None:
    graph = _two_node_graph(initial_weight=1.0)
    trajectory = _stationary_trajectory(PSI_SYMMETRIC)  # correlation = +0.5

    updated = AntiHebbianAdaptation(eta=0.1).update(graph, trajectory, dtau=1.0)

    # delta = -0.1 * 0.5 = -0.05, no Oja term
    np.testing.assert_allclose(updated.weights[0, 1], 0.95, atol=1e-10)


def test_alternative_objective_ignores_phase_uses_only_density() -> None:
    """psi_a and psi_b have identical density (0.5, 0.5) but opposite-sign
    correlation -- AlternativeObjective must give the SAME update for both,
    unlike Hebbian which would differ."""
    graph_a = _two_node_graph(initial_weight=1.0)
    graph_b = _two_node_graph(initial_weight=1.0)

    updated_a = AlternativeObjective(eta=0.1).update(
        graph_a, _stationary_trajectory(PSI_SYMMETRIC), dtau=1.0
    )
    updated_b = AlternativeObjective(eta=0.1).update(
        graph_b, _stationary_trajectory(PSI_ANTISYMMETRIC), dtau=1.0
    )

    np.testing.assert_allclose(updated_a.weights, updated_b.weights, atol=1e-12)


def test_alternative_objective_differs_from_hebbian_when_correlation_negative() -> None:
    """Cross-check: on psi_b (correlation=-0.5), Hebbian shrinks the weight
    (moving toward its fixed point from above) while AlternativeObjective
    (density-only, always positive contribution) grows it -- confirming
    the two rules are genuinely mechanistically different, not just
    differently-parameterized versions of the same update."""
    graph_hebbian = _two_node_graph(initial_weight=1.0)
    graph_alt = _two_node_graph(initial_weight=1.0)
    trajectory = _stationary_trajectory(PSI_ANTISYMMETRIC)

    updated_hebbian = HebbianAdaptation(eta=0.1).update(graph_hebbian, trajectory, dtau=1.0)
    updated_alt = AlternativeObjective(eta=0.1).update(graph_alt, trajectory, dtau=1.0)

    assert updated_hebbian.weights[0, 1] < 1.0
    assert updated_alt.weights[0, 1] > 1.0
