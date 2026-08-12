"""Unit tests for effective resistance (G3, mathematical_contract.md Sec5.4).

Hand-derived reference: the 3-node path graph (0-1-2, unit weights) is a
simple circuit-theory case -- there is exactly ONE path between any pair of
nodes, so resistances combine in SERIES (R = R_01 + R_12, no parallel
paths to reduce it). With unit edge weight = unit conductance = unit
resistance per edge:
  R_eff(0,1) = 1  (single resistor)
  R_eff(1,2) = 1  (single resistor)
  R_eff(0,2) = 2  (two resistors in series: 1 + 1)
Cross-checked numerically via np.linalg.pinv before writing this test
(Bash prototype): R matrix = [[0,1,2],[1,0,1],[2,1,0]], exact match to
1e-12. This is independent of the pseudoinverse machinery itself --
circuit theory gives the expected values from first principles.
"""

import numpy as np

from boyko_benchmark.graphs.weights import combinatorial_laplacian
from boyko_benchmark.observables.graph_geometry import (
    effective_resistance_matrix,
    mean_effective_resistance,
    resistance_diameter,
)
from boyko_benchmark.types import WeightedGraph


def _path_graph_3_nodes() -> WeightedGraph:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def test_effective_resistance_matches_hand_derived_series_circuit() -> None:
    laplacian = combinatorial_laplacian(_path_graph_3_nodes())

    resistance = effective_resistance_matrix(laplacian)

    expected = np.array([[0.0, 1.0, 2.0], [1.0, 0.0, 1.0], [2.0, 1.0, 0.0]])
    np.testing.assert_allclose(resistance, expected, atol=1e-9)


def test_effective_resistance_matrix_is_symmetric_with_zero_diagonal() -> None:
    laplacian = combinatorial_laplacian(_path_graph_3_nodes())

    resistance = effective_resistance_matrix(laplacian)

    np.testing.assert_allclose(resistance, resistance.T, atol=1e-9)
    np.testing.assert_allclose(np.diagonal(resistance), np.zeros(3), atol=1e-9)


def test_resistance_diameter_is_the_longest_shortest_path_pair_here() -> None:
    """For this path graph the resistance diameter (2.0, the 0-2 pair)
    happens to equal the hop-count diameter -- a coincidence of the
    series-only topology, not a general equivalence (a graph with a
    parallel/shortcut path would make R_eff strictly SMALLER than hop
    count for that pair, which is exactly why G3 was revised away from
    hop count -- resistance is weight-sensitive, hop count is not)."""
    laplacian = combinatorial_laplacian(_path_graph_3_nodes())

    diameter = resistance_diameter(laplacian)

    assert abs(diameter - 2.0) < 1e-9


def test_mean_effective_resistance_matches_hand_derived_average() -> None:
    """Off-diagonal entries are {1, 2, 1, 1, 2, 1} (6 ordered pairs for
    N=3) -- mean = (1+2+1+1+2+1)/6 = 8/6 = 4/3 exactly."""
    laplacian = combinatorial_laplacian(_path_graph_3_nodes())

    mean_resistance = mean_effective_resistance(laplacian)

    assert abs(mean_resistance - 4.0 / 3.0) < 1e-9


def test_effective_resistance_is_strictly_smaller_with_a_shortcut_edge() -> None:
    """Adding a direct 0-2 edge (unit weight) to the path graph creates a
    parallel path between 0 and 2: two routes in parallel always reduce
    effective resistance below either route alone (parallel resistor
    law: 1/R = 1/R_a + 1/R_b). Original R_eff(0,2) was 2.0 (series); the
    direct edge alone would give R=1.0; parallel combination must be
    STRICTLY below the smaller of the two (< 1.0) -- this is the
    weight-sensitivity property hop-count diameter structurally cannot
    have under a fixed topology mask."""
    mask = np.array([[False, True, True], [True, False, True], [True, True, False]])
    weights = np.array([[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]])
    triangle = WeightedGraph(mask=mask, weights=weights)
    laplacian = combinatorial_laplacian(triangle)

    resistance = effective_resistance_matrix(laplacian)

    assert resistance[0, 2] < 1.0
