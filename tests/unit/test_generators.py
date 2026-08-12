"""Unit tests for the Erdos-Renyi topology generator (graphs/generators.py)."""

import numpy as np

from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.types import WeightedGraph


def test_generates_graph_with_correct_node_and_edge_count() -> None:
    rng = np.random.default_rng(1)
    graph = generate_erdos_renyi(n_nodes=8, n_edges=10, rng=rng)

    assert isinstance(graph, WeightedGraph)
    assert graph.n_nodes == 8
    assert int(graph.mask.sum()) == 2 * 10


def test_generated_weights_are_uniform_on_edges() -> None:
    rng = np.random.default_rng(1)
    graph = generate_erdos_renyi(n_nodes=8, n_edges=10, rng=rng)

    edge_weights = graph.weights[graph.mask]
    assert np.all(edge_weights == edge_weights[0])
    assert edge_weights[0] > 0


def test_same_rng_state_produces_identical_graph() -> None:
    graph_a = generate_erdos_renyi(n_nodes=8, n_edges=10, rng=np.random.default_rng(42))
    graph_b = generate_erdos_renyi(n_nodes=8, n_edges=10, rng=np.random.default_rng(42))

    np.testing.assert_array_equal(graph_a.mask, graph_b.mask)
    np.testing.assert_array_equal(graph_a.weights, graph_b.weights)


def test_different_rng_state_produces_different_topology() -> None:
    graph_a = generate_erdos_renyi(n_nodes=8, n_edges=10, rng=np.random.default_rng(1))
    graph_b = generate_erdos_renyi(n_nodes=8, n_edges=10, rng=np.random.default_rng(2))

    assert not np.array_equal(graph_a.mask, graph_b.mask)