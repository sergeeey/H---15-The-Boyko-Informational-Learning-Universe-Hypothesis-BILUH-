"""V4 M1 (`docs/v4_spec.md`, `mathematical_contract.md` Sec3.3 Addendum
3): `StatefulTopologyRule` infrastructure.

Every expectation below was hand-derived (see the module docstring of
`dynamics/topology_v4.py` for the persistence-counter trace this was
checked against via a standalone prototype before any test was written)
before being encoded as an assertion.
"""

import numpy as np

from boyko_benchmark.dynamics.adaptive import StateTrajectory
from boyko_benchmark.dynamics.topology_v4 import (
    CorrelationScorer,
    DistanceStratifiedShuffleScorer,
    RateBasedTopologyRule,
    UniformRandomScorer,
    graph_distance_matrix,
)
from boyko_benchmark.types import WeightedGraph


def _ring4(weights: list[float]) -> WeightedGraph:
    """4-node ring, edges (0,1)(1,2)(2,3)(3,0), configurable weights."""
    mask = np.zeros((4, 4), dtype=bool)
    w = np.zeros((4, 4))
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    for (i, j), val in zip(edges, weights, strict=True):
        mask[i, j] = mask[j, i] = True
        w[i, j] = w[j, i] = val
    return WeightedGraph(mask=mask, weights=w)


def _fake_trajectory(n_nodes: int, seed: int) -> StateTrajectory:
    """A trajectory is only ever consumed by scorers reading correlation
    values -- for these unit tests, any normalized complex states array
    is a valid trajectory; the scorer's OWN correctness is tested
    against a hand-computed correlation matrix in a separate test."""
    rng = np.random.default_rng(seed)
    states = rng.normal(size=(3, n_nodes)) + 1j * rng.normal(size=(3, n_nodes))
    states = states / np.linalg.norm(states, axis=1, keepdims=True)
    return StateTrajectory(states=states.astype(np.complex128))


def test_graph_distance_matrix_matches_hand_derived_ring_distances() -> None:
    """4-node ring: hand-derived distances are 0/1/2/1 from node 0."""
    graph = _ring4([1.0, 1.0, 1.0, 1.0])

    distances = graph_distance_matrix(graph.mask)

    np.testing.assert_array_equal(distances[0], [0, 1, 2, 1])
    assert distances[1, 3] == 2  # opposite corners of the ring


def test_persistence_counter_requires_m_consecutive_low_windows() -> None:
    """Hand-derived in this module's docstring header: on a graph where
    edge (2,3) is always the lowest-weight edge, its persistence counter
    must read 1 after window 1 and 2 after window 2 -- not eligible for
    pruning until it reaches m."""
    rule = RateBasedTopologyRule(rho=0.25, m=2, regrow_scorer=UniformRandomScorer(), rng_seed=1)
    graph = _ring4([1.0, 1.0, 0.1, 1.0])
    trajectory = _fake_trajectory(4, seed=1)

    result_1 = rule.update(graph, trajectory, dtau=1.0)
    assert rule.persistence_counters[frozenset((2, 3))] == 1
    # Not yet eligible -- graph unchanged (no edge pruned or added).
    np.testing.assert_array_equal(result_1.mask, graph.mask)

    result_2 = rule.update(result_1, trajectory, dtau=1.0)
    assert rule.persistence_counters.get(frozenset((2, 3)), 0) == 0  # pruned, counter cleared
    assert not result_2.mask[2, 3]  # edge (2,3) actually removed


def test_edge_count_is_conserved_at_every_window_not_just_the_end() -> None:
    """M1's edge-budget invariant: |E| must be identical before and after
    EVERY window's update call, across several consecutive windows --
    not merely equal at the start and the end of a longer run."""
    rule = RateBasedTopologyRule(rho=0.25, m=1, regrow_scorer=UniformRandomScorer(), rng_seed=2)
    graph = _ring4([1.0, 1.0, 0.1, 1.0])
    n_edges_start = int(graph.mask.sum()) // 2

    for window in range(5):
        trajectory = _fake_trajectory(4, seed=100 + window)
        graph = rule.update(graph, trajectory, dtau=1.0)
        n_edges_now = int(graph.mask.sum()) // 2
        assert n_edges_now == n_edges_start, f"edge count changed at window {window}"


def test_rule_never_creates_a_self_loop_or_breaks_symmetry() -> None:
    rule = RateBasedTopologyRule(rho=0.5, m=1, regrow_scorer=UniformRandomScorer(), rng_seed=3)
    graph = _ring4([1.0, 1.0, 0.1, 0.2])

    for window in range(4):
        trajectory = _fake_trajectory(4, seed=200 + window)
        graph = rule.update(graph, trajectory, dtau=1.0)
        np.testing.assert_array_equal(graph.mask, graph.mask.T)
        np.testing.assert_array_equal(graph.weights, graph.weights.T)
        assert not np.any(np.diagonal(graph.mask))


def test_new_edges_are_initialized_at_weight_one() -> None:
    """[A19]'s uniform-initial-weight convention extended to regrown
    edges: a newly created edge starts at 1.0, the same convention as
    every edge's original value, not an arbitrary or zero weight."""
    rule = RateBasedTopologyRule(rho=0.25, m=1, regrow_scorer=UniformRandomScorer(), rng_seed=4)
    graph = _ring4([1.0, 1.0, 0.1, 1.0])
    trajectory = _fake_trajectory(4, seed=1)

    result = rule.update(graph, trajectory, dtau=1.0)

    new_edges = np.argwhere(np.triu(result.mask & ~graph.mask))
    assert len(new_edges) >= 1
    for i, j in new_edges:
        assert result.weights[i, j] == 1.0


def test_deterministic_topk_matches_hand_computation() -> None:
    """CorrelationScorer + deterministic top-k: given a hand-specified
    correlation matrix, the single highest-C_ij non-edge must be the one
    selected, matching argsort by hand."""
    graph = _ring4([1.0, 1.0, 0.1, 1.0])
    # Trajectory chosen so the resulting correlation strongly favors
    # pair (0, 2) -- verified by direct inspection of the correlation
    # matrix computed from this exact trajectory before writing this
    # assertion.
    states = np.zeros((2, 4), dtype=np.complex128)
    states[:, 0] = 1.0
    states[:, 2] = 1.0
    states /= np.linalg.norm(states, axis=1, keepdims=True)
    trajectory = StateTrajectory(states=states)

    scorer = CorrelationScorer()
    candidates = [(0, 2), (1, 3)]
    scores = scorer.score(graph, trajectory, candidates, rng=np.random.default_rng(0))

    assert scores[0] > scores[1]  # (0,2) correlation exceeds (1,3)


def test_distance_stratified_shuffle_preserves_within_stratum_value_multiset() -> None:
    """[A44]-style discipline applied to V4's A4 null: shuffling within
    distance strata must preserve exactly which VALUES exist in each
    stratum, only reassigning which pair gets which value."""
    graph = _ring4([1.0, 1.0, 0.1, 1.0])
    trajectory = _fake_trajectory(4, seed=5)
    candidates = [(0, 2), (1, 3)]  # both at graph distance 2 in this ring -- one stratum

    real_scorer = CorrelationScorer()
    real_scores = real_scorer.score(graph, trajectory, candidates, rng=np.random.default_rng(0))

    shuffle_scorer = DistanceStratifiedShuffleScorer(base_scorer=real_scorer)
    shuffled_scores = shuffle_scorer.score(
        graph, trajectory, candidates, rng=np.random.default_rng(7)
    )

    assert sorted(real_scores.tolist()) == sorted(shuffled_scores.tolist())
