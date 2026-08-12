"""Unit tests for shared initialization (Arms A/B/F/CD) and Arm C's
independent construction (mathematical_contract.md Sec4, [A7], [A17])."""

import numpy as np

from boyko_benchmark.arms.shared_initialization import (
    SharedInitialization,
    build_parameter_matched_random_graph,
    build_shared_initialization,
)


def test_shared_initialization_is_reproducible_with_same_seed() -> None:
    init_a = build_shared_initialization(
        n_nodes=10, n_edges=15, rng=np.random.default_rng(1), n_source_nodes=5
    )
    init_b = build_shared_initialization(
        n_nodes=10, n_edges=15, rng=np.random.default_rng(1), n_source_nodes=5
    )

    np.testing.assert_array_equal(init_a.graph.mask, init_b.graph.mask)
    np.testing.assert_array_equal(init_a.graph.weights, init_b.graph.weights)
    assert init_a.source_nodes == init_b.source_nodes


def test_shared_initialization_differs_with_different_seed() -> None:
    init_a = build_shared_initialization(
        n_nodes=10, n_edges=15, rng=np.random.default_rng(1), n_source_nodes=5
    )
    init_b = build_shared_initialization(
        n_nodes=10, n_edges=15, rng=np.random.default_rng(2), n_source_nodes=5
    )

    assert not np.array_equal(init_a.graph.mask, init_b.graph.mask) or (
        init_a.source_nodes != init_b.source_nodes
    )


def test_shared_initialization_source_nodes_are_valid_and_unique() -> None:
    init = build_shared_initialization(
        n_nodes=10, n_edges=15, rng=np.random.default_rng(1), n_source_nodes=5
    )

    assert len(init.source_nodes) == 5
    assert len(set(init.source_nodes)) == 5
    assert all(0 <= idx < 10 for idx in init.source_nodes)


def test_shared_initialization_returns_correct_type() -> None:
    init = build_shared_initialization(
        n_nodes=8, n_edges=10, rng=np.random.default_rng(1), n_source_nodes=5
    )

    assert isinstance(init, SharedInitialization)
    assert init.graph.n_nodes == 8
    assert int(init.graph.mask.sum()) == 2 * 10


def test_arm_c_matches_node_and_edge_count() -> None:
    graph = build_parameter_matched_random_graph(
        n_nodes=10, n_edges=15, rng=np.random.default_rng(3)
    )

    assert graph.n_nodes == 10
    assert int(graph.mask.sum()) == 2 * 15


def test_arm_c_is_independent_of_shared_initialization() -> None:
    """Different seeds -> Arm C's topology should not coincide with the
    shared initialization's topology (overwhelming probability, not a
    formal guarantee, but this is what 'independent draw' means)."""
    shared = build_shared_initialization(
        n_nodes=12, n_edges=20, rng=np.random.default_rng(10), n_source_nodes=5
    )
    arm_c_graph = build_parameter_matched_random_graph(
        n_nodes=12, n_edges=20, rng=np.random.default_rng(99)
    )

    assert not np.array_equal(shared.graph.mask, arm_c_graph.mask)
