"""V4-K1c (`docs/v4_spec.md` Sec7d, Revision 2, pre-registered
2026-08-18): `BoundedIncidenceTopologyRule` -- same weight-sorted
persistence-gated pruning as `RateBasedTopologyRule`, but a per-node
cap `b_i = max(0, min(floor(q*d_i), d_i-1))` on how many of a node's
CURRENT edges the prune step may remove in one window, selected via a
deterministic greedy walk (score-descending = weight-ascending) rather
than an unconstrained "prune everything eligible."

Hand-derived fixture (prototype verified before any assertion written,
`.venv/Scripts/python.exe -c "..."`): 5-node "hub" graph, node 0
connected to 1,2,3,4 (degree 4) plus a ring 1-2-3-4-1 (each of 1..4 has
degree 3). Hub edges weighted 0.1/0.2/0.3/0.4 (the 4 lowest of 8 total
edges); ring edges weighted 1.0 (never eligible). With `rho=0.5` (
n_target=4) and `m=1`, ALL FOUR hub edges become eligible on window 1.
`q=1/2` gives `b_0=max(0,min(2,3))=2` (node 0 can lose at most 2 of its
4 edges) and `b_{1..4}=max(0,min(1,2))=1` (each ring node's own cap,
not binding here since each only has ONE eligible edge touching it).
Greedy by ascending weight: (0,1)[0.1] selected (0->1,1->1), (0,2)[0.2]
selected (0->2,2->1), (0,3)[0.3] REJECTED (node 0's cap of 2 already
hit), (0,4)[0.4] REJECTED (same reason) -- S_prune={(0,1),(0,2)}, NOT
all 4 eligible edges.
"""

import numpy as np

from boyko_benchmark.dynamics.adaptive import StateTrajectory
from boyko_benchmark.dynamics.topology_v4 import (
    BoundedIncidenceTopologyRule,
    CorrelationScorer,
    UniformRandomScorer,
)
from boyko_benchmark.types import WeightedGraph


def _hub_graph() -> WeightedGraph:
    mask = np.zeros((5, 5), dtype=bool)
    weights = np.zeros((5, 5))
    hub_edges = {(0, 1): 0.1, (0, 2): 0.2, (0, 3): 0.3, (0, 4): 0.4}
    ring_edges = {(1, 2): 1.0, (2, 3): 1.0, (3, 4): 1.0, (1, 4): 1.0}
    for (i, j), w in {**hub_edges, **ring_edges}.items():
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = w
    return WeightedGraph(mask=mask, weights=weights)


def _dummy_trajectory(n_nodes: int) -> StateTrajectory:
    # Constant, non-degenerate state -- only used by regrow scorers that
    # ignore it entirely (UniformRandomScorer) in these cap-focused tests.
    states = np.ones((2, n_nodes), dtype=complex)
    return StateTrajectory(states=states)


def test_cap_rejects_edges_beyond_the_hub_node_budget() -> None:
    graph = _hub_graph()
    trajectory = _dummy_trajectory(graph.n_nodes)
    rule = BoundedIncidenceTopologyRule(
        rho=0.5,
        m=1,
        q=0.5,
        regrow_scorer=UniformRandomScorer(),
        topology_tiebreak_seed=1,
        control_regrowth_seed=1,
    )

    rule.update(graph, trajectory, dtau=1.0)

    assert rule.last_eligible == frozenset({(0, 1), (0, 2), (0, 3), (0, 4)})
    assert rule.last_pruned == frozenset({(0, 1), (0, 2)})


def test_capped_out_edges_keep_their_persistence_counter_not_reset() -> None:
    """(0,3)/(0,4) were eligible (persistence>=m) but rejected by node
    0's cap -- their persistence must be PRESERVED (not popped, as only
    actually-pruned edges are), so they don't need to re-accumulate `m`
    fresh windows before being reconsidered."""
    graph = _hub_graph()
    trajectory = _dummy_trajectory(graph.n_nodes)
    rule = BoundedIncidenceTopologyRule(
        rho=0.5,
        m=1,
        q=0.5,
        regrow_scorer=UniformRandomScorer(),
        topology_tiebreak_seed=1,
        control_regrowth_seed=1,
    )

    graph_after_1 = rule.update(graph, trajectory, dtau=1.0)

    assert graph_after_1.mask[0, 3]  # not pruned -- capped out, still present
    assert graph_after_1.mask[0, 4]
    assert rule.persistence_counters.get(frozenset({0, 3}), 0) >= 1
    assert rule.persistence_counters.get(frozenset({0, 4}), 0) >= 1
    # the ACTUALLY pruned edges' counters are gone, per the pre-existing
    # (unchanged) persistence-pop-on-prune behavior
    assert frozenset({0, 1}) not in rule.persistence_counters
    assert frozenset({0, 2}) not in rule.persistence_counters


def test_regrow_count_matches_actual_prune_count_not_the_target() -> None:
    graph = _hub_graph()
    trajectory = _dummy_trajectory(graph.n_nodes)
    rule = BoundedIncidenceTopologyRule(
        rho=0.5,
        m=1,
        q=0.5,
        regrow_scorer=UniformRandomScorer(),
        topology_tiebreak_seed=1,
        control_regrowth_seed=1,
    )

    rule.update(graph, trajectory, dtau=1.0)

    assert len(rule.last_pruned) == 2  # capped, not the n_target=4
    assert len(rule.last_regrown) == 2  # matched to actual prune count
    assert rule.last_regrown != rule.last_pruned


def test_edge_count_conserved_despite_capping() -> None:
    graph = _hub_graph()
    trajectory = _dummy_trajectory(graph.n_nodes)
    rule = BoundedIncidenceTopologyRule(
        rho=0.5,
        m=1,
        q=0.5,
        regrow_scorer=UniformRandomScorer(),
        topology_tiebreak_seed=1,
        control_regrowth_seed=1,
    )
    n_before = int(graph.mask.sum())

    result = rule.update(graph, trajectory, dtau=1.0)

    assert int(result.mask.sum()) == n_before


def test_cap_formula_never_allows_pruning_the_last_edge() -> None:
    """A degree-1 node's single edge must never be prunable by the cap
    mechanism, for any q -- the naive max(1, floor(q*d)) form would
    allow exactly this at d=1; the corrected form must not."""
    from boyko_benchmark.dynamics.topology_v4 import bounded_incidence_cap

    assert bounded_incidence_cap(degree=1, q=0.5) == 0
    assert bounded_incidence_cap(degree=0, q=0.5) == 0
    assert bounded_incidence_cap(degree=6, q=0.5) == 3
    assert bounded_incidence_cap(degree=3, q=0.5) == 1
    assert bounded_incidence_cap(degree=2, q=0.5) == 1


def test_correlation_scorer_still_used_for_regrow_ranking() -> None:
    """Wiring check: BoundedIncidenceTopologyRule still delegates regrow
    ranking to whatever RegrowScorer it's given, same as RateBased
    TopologyRule -- CorrelationScorer must not raise on this fixture."""
    graph = _hub_graph()
    trajectory = _dummy_trajectory(graph.n_nodes)
    rule = BoundedIncidenceTopologyRule(
        rho=0.5,
        m=1,
        q=0.5,
        regrow_scorer=CorrelationScorer(),
        topology_tiebreak_seed=1,
        control_regrowth_seed=1,
    )

    result = rule.update(graph, trajectory, dtau=1.0)

    assert int(result.mask.sum()) == int(graph.mask.sum())
