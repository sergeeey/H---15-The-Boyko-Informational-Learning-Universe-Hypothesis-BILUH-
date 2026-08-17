"""Phase 12 Stage 3: Forman-Ricci curvature. Every expectation below is
hand-derivable from the unweighted collapse F(e) = 4 - deg(u) - deg(v),
and all three were confirmed by a standalone prototype run before being
written as assertions."""

import numpy as np

from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice
from boyko_benchmark.observables.curvature import forman_ricci_curvature
from boyko_benchmark.types import WeightedGraph


def _unweighted(edges: list[tuple[int, int]], n_nodes: int) -> WeightedGraph:
    mask = np.zeros((n_nodes, n_nodes), dtype=bool)
    weights = np.zeros((n_nodes, n_nodes))
    for i, j in edges:
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = 1.0
    return WeightedGraph(mask=mask, weights=weights)


def test_triangle_has_zero_curvature_on_every_edge() -> None:
    """Every node has degree 2 -> F = 4 - 2 - 2 = 0."""
    curvatures = forman_ricci_curvature(_unweighted([(0, 1), (1, 2), (0, 2)], 3))

    assert len(curvatures) == 3
    np.testing.assert_allclose(curvatures, 0.0, atol=1e-12)


def test_path_graph_curvature_matches_degree_formula() -> None:
    """Path 0-1-2, degrees (1,2,1) -> both edges F = 4 - 1 - 2 = 1."""
    curvatures = forman_ricci_curvature(_unweighted([(0, 1), (1, 2)], 3))

    np.testing.assert_allclose(curvatures, [1.0, 1.0], atol=1e-12)


def test_periodic_cubic_lattice_has_uniform_negative_curvature() -> None:
    """The positive geometric control: a periodic cubic lattice is
    degree-regular (6), so every edge must carry exactly
    F = 4 - 6 - 6 = -8. A detector that returns anything else on a
    perfectly homogeneous geometric object is not measuring what it
    claims to."""
    lattice = generate_periodic_cubic_lattice(8)

    curvatures = forman_ricci_curvature(lattice)

    assert len(curvatures) == 1536
    np.testing.assert_allclose(curvatures, -8.0, atol=1e-12)


def test_empty_graph_returns_empty_array() -> None:
    graph = WeightedGraph(mask=np.zeros((4, 4), dtype=bool), weights=np.zeros((4, 4)))

    assert len(forman_ricci_curvature(graph)) == 0


def test_zero_weight_edges_are_excluded_not_infinite() -> None:
    """`[A42]` regression: the Hebbian rule's non-negativity clamp can
    drive an edge's weight to EXACTLY zero under noise (observed: 1 edge
    of 1536, on 1 of 5 seeds, in the Cσ cell). Forman-Ricci divides by
    sqrt(w_e * w_neighbor), so a zero weight produced inf/nan and
    silently poisoned every downstream mean -- which is exactly what
    happened on the first Stage 3 run.

    A zero-weight edge carries no coupling: it is dynamically absent even
    though `mask` still records it. The correct treatment is to exclude
    it from the weighted graph entirely, both as a focal edge and as an
    incident neighbour -- NOT to add an epsilon, which would invent a
    coupling that the dynamics removed."""
    mask = np.zeros((4, 4), dtype=bool)
    weights = np.zeros((4, 4))
    for i, j, w in [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 0.0)]:
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = w
    graph = WeightedGraph(mask=mask, weights=weights)

    curvatures = forman_ricci_curvature(graph)

    assert np.all(np.isfinite(curvatures)), "zero-weight edge produced inf/nan"
    # Only the two positive-weight edges remain; with (2,3) dynamically
    # absent the graph is the path 0-1-2, so both survivors score 1.0
    # exactly -- same hand-derived value as the plain path test above.
    np.testing.assert_allclose(curvatures, [1.0, 1.0], atol=1e-12)


def test_heavier_edge_weight_changes_curvature() -> None:
    """Sanity: the observable must actually respond to weights, or it
    could not possibly distinguish this project's fixed-topology cells
    (where weights are the ONLY thing that differs)."""
    base = _unweighted([(0, 1), (1, 2)], 3)
    heavier = WeightedGraph(mask=base.mask, weights=base.weights * np.array([1.0]))
    heavier.weights[0, 1] = heavier.weights[1, 0] = 5.0

    assert not np.allclose(forman_ricci_curvature(base), forman_ricci_curvature(heavier), atol=1e-9)
