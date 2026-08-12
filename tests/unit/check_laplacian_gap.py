"""Unit tests for the normalized Laplacian gap (G2, mathematical_contract.md
Sec5.2).

Hand-derived reference: the 3-node path graph's L_norm (also used in
test_weights.py) is [[1,-1/sqrt2,0],[-1/sqrt2,1,-1/sqrt2],[0,-1/sqrt2,1]].
Characteristic polynomial, expanded by hand:
  det(L_norm - lambda*I) = -lambda*(1-lambda)*(2-lambda)
Roots: 0, 1, 2 exactly -- gap = 1.0, not an approximation.
"""

import numpy as np

from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.observables.laplacian_gap import laplacian_gap
from boyko_benchmark.types import WeightedGraph


def _path_graph_3_nodes() -> WeightedGraph:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def test_gap_matches_hand_derived_characteristic_polynomial_roots() -> None:
    l_norm = normalized_laplacian(_path_graph_3_nodes())

    gap = laplacian_gap(l_norm)

    assert abs(gap - 1.0) < 1e-9


def test_gap_is_within_normalized_laplacian_bounds() -> None:
    """Spectrum of L_norm is bounded in [0, 2) -- the gap (a non-zero
    eigenvalue) must respect that bound too."""
    l_norm = normalized_laplacian(_path_graph_3_nodes())

    gap = laplacian_gap(l_norm)

    assert 0.0 < gap < 2.0


def test_gap_skips_all_zero_eigenvalues_from_multiple_components() -> None:
    """Two disjoint single-edge components (0-1, 2-3): each contributes
    eigenvalues {0, 2} to L_norm's spectrum, so the FULL spectrum has TWO
    zero eigenvalues (multiplicity = number of components, per the
    function's own docstring) -- laplacian_gap must skip both and return
    the first genuinely non-zero eigenvalue (2.0), not stop at the
    second zero. A fully-edgeless graph (every node isolated) is not
    tested here: normalized_laplacian divides by zero for a degree-0
    node before laplacian_gap is ever reached, and the benchmark's
    population is restricted to connected graphs upstream anyway
    (estimand.md), so that scenario cannot occur in the real pipeline."""
    mask = np.array(
        [
            [False, True, False, False],
            [True, False, False, False],
            [False, False, False, True],
            [False, False, True, False],
        ]
    )
    weights = np.where(mask, 1.0, 0.0)
    graph = WeightedGraph(mask=mask, weights=weights)
    l_norm = normalized_laplacian(graph)

    gap = laplacian_gap(l_norm)

    assert abs(gap - 2.0) < 1e-9
