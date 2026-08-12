"""Unit tests for Laplacians derived from a WeightedGraph (mathematical_contract.md Sec1.2).

Two Laplacians, kept deliberately distinct:
- combinatorial L = D - W: its zero eigenvector is the all-ones vector 1.
- normalized L_norm = I - D^-1/2 W D^-1/2: its zero eigenvector is D^1/2 . 1,
  NOT 1 -- these coincide only for regular (constant-degree) graphs. The
  3-node path graph used below has non-constant degree specifically to
  make this distinction testable, not just documented.
"""

import numpy as np

from boyko_benchmark.graphs.weights import combinatorial_laplacian, normalized_laplacian
from boyko_benchmark.types import WeightedGraph


def _path_graph_3_nodes() -> WeightedGraph:
    """0 - 1 - 2, unit weights. Degrees (1, 2, 1) -- deliberately irregular."""
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def test_combinatorial_laplacian_rows_sum_to_zero() -> None:
    graph = _path_graph_3_nodes()
    laplacian = combinatorial_laplacian(graph)

    np.testing.assert_allclose(laplacian @ np.ones(3), np.zeros(3), atol=1e-12)


def test_combinatorial_laplacian_is_symmetric() -> None:
    graph = _path_graph_3_nodes()
    laplacian = combinatorial_laplacian(graph)

    np.testing.assert_allclose(laplacian, laplacian.T, atol=1e-12)


def test_combinatorial_laplacian_matches_hand_derivation() -> None:
    graph = _path_graph_3_nodes()
    laplacian = combinatorial_laplacian(graph)

    expected = np.array([[1.0, -1.0, 0.0], [-1.0, 2.0, -1.0], [0.0, -1.0, 1.0]])
    np.testing.assert_allclose(laplacian, expected, atol=1e-12)


def test_normalized_laplacian_zero_eigenvector_is_sqrt_degree_not_ones() -> None:
    """The specific distinction mathematical_contract.md Sec1.2 documents:
    L_norm @ (sqrt(D) . 1) = 0, but L_norm @ 1 != 0 for an irregular graph."""
    graph = _path_graph_3_nodes()
    l_norm = normalized_laplacian(graph)

    sqrt_degree = np.array([1.0, np.sqrt(2.0), 1.0])
    np.testing.assert_allclose(l_norm @ sqrt_degree, np.zeros(3), atol=1e-10)

    ones_result = l_norm @ np.ones(3)
    assert not np.allclose(ones_result, np.zeros(3), atol=1e-6)


def test_normalized_laplacian_matches_hand_derivation() -> None:
    graph = _path_graph_3_nodes()
    l_norm = normalized_laplacian(graph)

    inv_sqrt2 = 1.0 / np.sqrt(2.0)
    expected = np.array(
        [[1.0, -inv_sqrt2, 0.0], [-inv_sqrt2, 1.0, -inv_sqrt2], [0.0, -inv_sqrt2, 1.0]]
    )
    np.testing.assert_allclose(l_norm, expected, atol=1e-12)


def test_normalized_laplacian_spectrum_bounded_in_zero_two() -> None:
    graph = _path_graph_3_nodes()
    l_norm = normalized_laplacian(graph)

    eigenvalues = np.linalg.eigvalsh(l_norm)
    assert np.all(eigenvalues >= -1e-10)
    assert np.all(eigenvalues < 2.0 + 1e-10)


def test_normalized_laplacian_is_symmetric() -> None:
    graph = _path_graph_3_nodes()
    l_norm = normalized_laplacian(graph)

    np.testing.assert_allclose(l_norm, l_norm.T, atol=1e-12)
