"""Unit tests for degree-preserving topology scrambling (Arm D, [A8], [A21]).

Explicitly named in TZ.txt Sec13's Milestone-1 test list:
test_scrambling_preserves_degree_sequence.
"""

import numpy as np

from boyko_benchmark.graphs.rewiring import scramble_preserving_degree_sequence
from boyko_benchmark.types import WeightedGraph


def _six_node_ring() -> WeightedGraph:
    """0-1-2-3-4-5-0, unit weights, every node degree 2."""
    n = 6
    mask = np.zeros((n, n), dtype=bool)
    weights = np.zeros((n, n), dtype=float)
    for i in range(n):
        j = (i + 1) % n
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = 1.0
    return WeightedGraph(mask=mask, weights=weights)


def test_scramble_preserves_degree_sequence() -> None:
    """The Milestone-1 test named in TZ.txt Sec13."""
    graph = _six_node_ring()
    original_degree = graph.mask.sum(axis=1)

    scrambled = scramble_preserving_degree_sequence(graph, rng=np.random.default_rng(1), n_swaps=20)

    np.testing.assert_array_equal(scrambled.mask.sum(axis=1), original_degree)


def test_scramble_preserves_node_count() -> None:
    graph = _six_node_ring()

    scrambled = scramble_preserving_degree_sequence(graph, rng=np.random.default_rng(1), n_swaps=20)

    assert scrambled.n_nodes == graph.n_nodes


def test_scramble_changes_topology() -> None:
    """With enough swaps on a graph that has multiple realizations of its
    degree sequence, the specific wiring should differ from the original."""
    graph = _six_node_ring()

    scrambled = scramble_preserving_degree_sequence(graph, rng=np.random.default_rng(1), n_swaps=20)

    assert not np.array_equal(scrambled.mask, graph.mask)


def test_scramble_uses_uniform_initial_weight() -> None:
    """[A21]: rewired edges get the uniform INITIAL_EDGE_WEIGHT convention,
    not any weight value carried over from the original graph."""
    graph = _six_node_ring()

    scrambled = scramble_preserving_degree_sequence(graph, rng=np.random.default_rng(1), n_swaps=20)

    edge_weights = scrambled.weights[scrambled.mask]
    assert np.all(edge_weights == edge_weights[0])
    assert edge_weights[0] > 0


def test_scramble_produces_valid_weighted_graph() -> None:
    graph = _six_node_ring()

    scrambled = scramble_preserving_degree_sequence(graph, rng=np.random.default_rng(1), n_swaps=20)

    assert isinstance(scrambled, WeightedGraph)
    np.testing.assert_array_equal(scrambled.mask, scrambled.mask.T)
    assert not np.any(np.diagonal(scrambled.mask))


def test_scramble_is_reproducible_with_same_seed() -> None:
    graph = _six_node_ring()

    scrambled_a = scramble_preserving_degree_sequence(
        graph, rng=np.random.default_rng(42), n_swaps=20
    )
    scrambled_b = scramble_preserving_degree_sequence(
        graph, rng=np.random.default_rng(42), n_swaps=20
    )

    np.testing.assert_array_equal(scrambled_a.mask, scrambled_b.mask)
