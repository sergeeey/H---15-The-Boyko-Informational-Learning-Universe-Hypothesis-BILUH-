"""Unit tests for inverse participation ratio (G4, mathematical_contract.md
Sec5.3).

Hand-derived reference: the 3-node path graph's L_norm has eigenvalues
{0, 1, 2} with eigenvectors (normalized to unit L2 norm) v0=(0.5,
sqrt(2)/2, 0.5) for lambda=0, v1=(sqrt(2)/2, 0, -sqrt(2)/2) for lambda=1,
v2=(0.5, -sqrt(2)/2, 0.5) for lambda=2 -- derived by hand solving
(L_norm - lambda*I)v = 0 for each root (test_laplacian_gap.py's
characteristic polynomial). IPR(v0) = 0.5^4 + (sqrt(2)/2)^4 + 0.5^4
= 0.0625 + 0.25 + 0.0625 = 0.375 exactly.
"""

import numpy as np

from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.observables.ipr import inverse_participation_ratio, low_mode_eigenvectors
from boyko_benchmark.types import WeightedGraph


def _path_graph_3_nodes() -> WeightedGraph:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def test_ipr_matches_hand_derived_value_for_lowest_mode() -> None:
    l_norm = normalized_laplacian(_path_graph_3_nodes())
    lowest_mode = low_mode_eigenvectors(l_norm, n_modes=1)[:, 0]

    ipr = inverse_participation_ratio(lowest_mode)

    assert abs(ipr - 0.375) < 1e-9


def test_ipr_is_between_one_over_n_and_one() -> None:
    """For a normalized vector (Sum|phi_i|^2=1) on N components, IPR is
    bounded: 1/N (maximally delocalized, all |phi_i|^2 equal) <= IPR <= 1
    (maximally localized, all mass on one node) -- a structural bound, not
    specific to this graph."""
    l_norm = normalized_laplacian(_path_graph_3_nodes())
    lowest_mode = low_mode_eigenvectors(l_norm, n_modes=1)[:, 0]

    ipr = inverse_participation_ratio(lowest_mode)

    assert 1.0 / 3.0 - 1e-9 <= ipr <= 1.0 + 1e-9


def test_ipr_of_fully_localized_state_is_one() -> None:
    """A single-node point mass (e_k) has IPR = 1 exactly -- maximal
    localization, the opposite extreme from the uniform case below."""
    localized = np.array([1.0, 0.0, 0.0])

    ipr = inverse_participation_ratio(localized)

    assert abs(ipr - 1.0) < 1e-12


def test_ipr_of_uniform_state_is_one_over_n() -> None:
    """A perfectly uniform normalized state has IPR = 1/N exactly --
    maximal delocalization."""
    n = 5
    uniform = np.full(n, 1.0 / np.sqrt(n))

    ipr = inverse_participation_ratio(uniform)

    assert abs(ipr - 1.0 / n) < 1e-12


def test_low_mode_eigenvectors_returns_normalized_vectors() -> None:
    l_norm = normalized_laplacian(_path_graph_3_nodes())
    modes = low_mode_eigenvectors(l_norm, n_modes=3)

    for k in range(3):
        norm_sq = np.sum(np.abs(modes[:, k]) ** 2)
        assert abs(norm_sq - 1.0) < 1e-10


def test_low_mode_eigenvectors_returns_smallest_eigenvalues_first() -> None:
    """First returned mode should correspond to eigenvalue 0 (the
    hand-derived smallest root) -- verified by checking L_norm @ v ~ 0."""
    l_norm = normalized_laplacian(_path_graph_3_nodes())
    lowest_mode = low_mode_eigenvectors(l_norm, n_modes=1)[:, 0]

    residual = l_norm @ lowest_mode

    np.testing.assert_allclose(residual, np.zeros(3), atol=1e-9)
