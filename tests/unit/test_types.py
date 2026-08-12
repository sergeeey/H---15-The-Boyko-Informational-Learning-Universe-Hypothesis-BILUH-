"""Unit tests for WeightedGraph invariants (mathematical_contract.md §1.1).

Topology (mask M) and weights (W) are kept as two separate arrays:
M is symmetric with a zero diagonal; W is symmetric, non-negative, zero
diagonal, and W_ij > 0 implies M_ij = True (weight can't exist without a
topology edge). These invariants are enforced at construction time, not
just documented -- a graph that violates them must never be constructible.
"""

import numpy as np
import pytest

from boyko_benchmark.types import WeightedGraph


def test_accepts_valid_symmetric_nonnegative_weights() -> None:
    mask = np.array([[False, True, True], [True, False, False], [True, False, False]])
    weights = np.array([[0.0, 1.5, 2.0], [1.5, 0.0, 0.0], [2.0, 0.0, 0.0]])

    graph = WeightedGraph(mask=mask, weights=weights)

    assert graph.n_nodes == 3
    np.testing.assert_array_equal(graph.mask, mask)
    np.testing.assert_array_equal(graph.weights, weights)


def test_rejects_asymmetric_mask() -> None:
    mask = np.array([[False, True], [False, False]])
    weights = np.array([[0.0, 1.0], [1.0, 0.0]])

    with pytest.raises(ValueError, match="symmetric"):
        WeightedGraph(mask=mask, weights=weights)


def test_rejects_asymmetric_weights() -> None:
    mask = np.array([[False, True], [True, False]])
    weights = np.array([[0.0, 1.0], [2.0, 0.0]])

    with pytest.raises(ValueError, match="symmetric"):
        WeightedGraph(mask=mask, weights=weights)


def test_rejects_negative_weights() -> None:
    mask = np.array([[False, True], [True, False]])
    weights = np.array([[0.0, -1.0], [-1.0, 0.0]])

    with pytest.raises(ValueError, match="non-negative"):
        WeightedGraph(mask=mask, weights=weights)


def test_rejects_self_loop_in_mask() -> None:
    mask = np.array([[True, True], [True, False]])
    weights = np.array([[0.0, 1.0], [1.0, 0.0]])

    with pytest.raises(ValueError, match="self-loop"):
        WeightedGraph(mask=mask, weights=weights)


def test_rejects_weight_without_topology_edge() -> None:
    """W_ij > 0 with M_ij = False must be rejected -- weight can't exist
    without a topology edge (mathematical_contract.md §1.1, [A5])."""
    mask = np.array([[False, False], [False, False]])
    weights = np.array([[0.0, 1.0], [1.0, 0.0]])

    with pytest.raises(ValueError, match="topology"):
        WeightedGraph(mask=mask, weights=weights)