"""V5 (`docs/v5_spec.md`, `mathematical_contract.md` Addendum 5):
degree-preserving connected edge swap -- the elementary structural
operation replacing V4's independent edge deletion.

Hand-derived fixture (prototype verified before any assertion written,
`.venv/Scripts/python.exe -c "..."`): a 4-node square, edges
`{(0,1),(1,2),(2,3),(0,3)}`. Exactly 2 disjoint edge pairs exist
(`{(0,1),(2,3)}` and `{(0,3),(1,2)}`); each has 2 possible
reconnections, but one reconnection per pair would recreate an
already-existing edge (multi-edge), leaving exactly 2 structurally
legal candidates, both adding `{(0,2),(1,3)}` but removing different
original edges. Both happen to keep the graph connected (each is
itself another 4-cycle) -- verified by direct computation, not assumed.

`generate_swap_candidates` returns NumPy arrays `(remove, add)`, shape
`(K, 2, 2)` each, not a list of dataclasses -- found necessary during
implementation: at N=512 (~1536 edges) there are ~2.3 million legal
candidates, and constructing that many Python objects per call (needed
up to ~7500 times for the real K1'-equivalent campaign) would take
hours. See `dynamics/topology_v5.py`'s module docstring for the
measured timings.
"""

import numpy as np

from boyko_benchmark.dynamics.adaptive import StateTrajectory
from boyko_benchmark.dynamics.topology_v5 import (
    BalancedSwapTopologyRule,
    CorrelationSwapScorer,
    DistanceStratifiedSwapScorer,
    SwapCandidate,
    apply_swap,
    generate_swap_candidates,
)
from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.types import WeightedGraph


def _square_graph() -> WeightedGraph:
    mask = np.zeros((4, 4), dtype=bool)
    weights = np.zeros((4, 4))
    for i, j in [(0, 1), (1, 2), (2, 3), (0, 3)]:
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = 1.0
    return WeightedGraph(mask=mask, weights=weights)


def test_generate_swap_candidates_matches_hand_derived_square_example() -> None:
    graph = _square_graph()

    remove, add = generate_swap_candidates(graph.mask)

    assert remove.shape == (2, 2, 2)
    assert add.shape == (2, 2, 2)
    removes = {tuple(map(tuple, r)) for r in remove}
    adds = {tuple(map(tuple, a)) for a in add}
    assert removes == {((0, 1), (2, 3)), ((0, 3), (1, 2))}
    assert adds == {((0, 2), (1, 3))}


def test_generate_swap_candidates_excludes_multi_edge_reconnections() -> None:
    """Both disjoint-edge-pairs in the square fixture have a reconnection
    that would recreate an existing edge -- confirmed excluded (only 2
    of the 4 raw reconnection possibilities survive)."""
    graph = _square_graph()

    remove, add = generate_swap_candidates(graph.mask)

    for k in range(len(remove)):
        assert not graph.mask[add[k, 0, 0], add[k, 0, 1]]
        assert not graph.mask[add[k, 1, 0], add[k, 1, 1]]


def test_generate_swap_candidates_on_a_graph_with_no_disjoint_pairs_is_empty() -> None:
    """A 3-node path (0-1-2) has only 2 edges, sharing node 1 -- no
    disjoint pair exists, so the candidate arrays must be empty, not
    error."""
    mask = np.zeros((3, 3), dtype=bool)
    for i, j in [(0, 1), (1, 2)]:
        mask[i, j] = mask[j, i] = True

    remove, add = generate_swap_candidates(mask)

    assert remove.shape == (0, 2, 2)
    assert add.shape == (0, 2, 2)


def test_apply_swap_preserves_every_nodes_degree() -> None:
    graph = _square_graph()
    degree_before = graph.mask.sum(axis=1).copy()
    swap = SwapCandidate(remove=((0, 1), (2, 3)), add=((0, 2), (1, 3)))

    result = apply_swap(graph, swap, new_edge_weight=1.0)

    degree_after = result.mask.sum(axis=1)
    np.testing.assert_array_equal(degree_before, degree_after)


def test_apply_swap_produces_the_expected_edge_set() -> None:
    graph = _square_graph()
    swap = SwapCandidate(remove=((0, 1), (2, 3)), add=((0, 2), (1, 3)))

    result = apply_swap(graph, swap, new_edge_weight=1.0)

    new_edges = frozenset(map(tuple, np.argwhere(np.triu(result.mask))))
    assert new_edges == frozenset({(0, 3), (1, 2), (0, 2), (1, 3)})


def test_apply_swap_gives_new_edges_the_specified_weight() -> None:
    graph = _square_graph()
    swap = SwapCandidate(remove=((0, 1), (2, 3)), add=((0, 2), (1, 3)))

    result = apply_swap(graph, swap, new_edge_weight=0.5)

    assert result.weights[0, 2] == 0.5
    assert result.weights[1, 3] == 0.5
    assert result.weights[0, 1] == 0.0
    assert result.weights[2, 3] == 0.0


def test_correlation_swap_scorer_matches_hand_computation() -> None:
    """States chosen so time_averaged_correlation is exactly computable
    by hand: single snapshot (K=0), psi = [1, 1j, -1, -1j] (unit
    magnitude, orthogonal phases). C_ij = Re(conj(psi_i)*psi_j)."""
    graph = _square_graph()
    states = np.array([[1 + 0j, 0 + 1j, -1 + 0j, 0 - 1j]])
    trajectory = StateTrajectory(states=states)
    scorer = CorrelationSwapScorer()
    remove = np.array([[[0, 1], [2, 3]]])
    add = np.array([[[0, 2], [1, 3]]])

    scores = scorer.score(graph, trajectory, remove, add, np.random.default_rng(0))

    psi = states[0]
    correlation = np.real(np.conj(psi)[:, None] * psi[None, :])
    expected_delta_s = (correlation[0, 2] + correlation[1, 3]) - (
        correlation[0, 1] + correlation[2, 3]
    )
    assert scores[0] == expected_delta_s


def _dummy_trajectory(n_nodes: int, seed: int) -> StateTrajectory:
    rng = np.random.default_rng(seed)
    phases = rng.uniform(0, 2 * np.pi, size=(2, n_nodes))
    states = np.exp(1j * phases)
    return StateTrajectory(states=states)


def test_balanced_swap_rule_preserves_every_nodes_degree_over_multiple_windows() -> None:
    """Real-scale wiring check (N=20 ER graph, prototype-verified before
    this assertion was written): degree invariance must hold not just
    for a single apply_swap call but across several successive windows
    of the full rule, where topology genuinely changes each time."""
    rng = np.random.default_rng(11)
    graph = generate_erdos_renyi(n_nodes=20, n_edges=40, rng=rng)
    degree_before = graph.mask.sum(axis=1).copy()
    rule = BalancedSwapTopologyRule(
        n_swaps=3, score_scorer=CorrelationSwapScorer(), tiebreak_seed=1, control_seed=1
    )

    current = graph
    for window in range(3):
        trajectory = _dummy_trajectory(graph.n_nodes, seed=window)
        current = rule.update(current, trajectory, dtau=1.0)

    degree_after = current.mask.sum(axis=1)
    np.testing.assert_array_equal(degree_before, degree_after)
    assert int(current.mask.sum()) // 2 == 40  # edge count conserved


def test_balanced_swap_rule_commits_the_requested_number_of_swaps_when_feasible() -> None:
    rng = np.random.default_rng(11)
    graph = generate_erdos_renyi(n_nodes=20, n_edges=40, rng=rng)
    rule = BalancedSwapTopologyRule(
        n_swaps=3, score_scorer=CorrelationSwapScorer(), tiebreak_seed=1, control_seed=1
    )
    trajectory = _dummy_trajectory(graph.n_nodes, seed=0)

    rule.update(graph, trajectory, dtau=1.0)

    assert len(rule.last_committed) == 3
    assert rule.last_skipped_count == 0


def test_balanced_swap_rule_is_deterministic_given_the_same_seeds() -> None:
    rng = np.random.default_rng(11)
    graph = generate_erdos_renyi(n_nodes=20, n_edges=40, rng=rng)
    trajectory = _dummy_trajectory(graph.n_nodes, seed=0)

    rule_a = BalancedSwapTopologyRule(
        n_swaps=3, score_scorer=CorrelationSwapScorer(), tiebreak_seed=7, control_seed=7
    )
    rule_b = BalancedSwapTopologyRule(
        n_swaps=3, score_scorer=CorrelationSwapScorer(), tiebreak_seed=7, control_seed=7
    )

    result_a = rule_a.update(graph, trajectory, dtau=1.0)
    result_b = rule_b.update(graph, trajectory, dtau=1.0)

    np.testing.assert_array_equal(result_a.mask, result_b.mask)


def test_distance_stratified_swap_scorer_preserves_the_value_multiset_within_a_stratum() -> None:
    """Wiring check for A4: the shuffled scores must be a PERMUTATION of
    the real scores within each stratum -- same invariant V4's own
    DistanceStratifiedShuffleScorer test checks."""
    rng = np.random.default_rng(11)
    graph = generate_erdos_renyi(n_nodes=20, n_edges=40, rng=rng)
    trajectory = _dummy_trajectory(graph.n_nodes, seed=0)
    remove, add = generate_swap_candidates(graph.mask)
    base_scorer = CorrelationSwapScorer()
    real_scores = base_scorer.score(graph, trajectory, remove, add, np.random.default_rng(0))

    scorer = DistanceStratifiedSwapScorer(base_scorer)
    shuffled_scores = scorer.score(graph, trajectory, remove, add, np.random.default_rng(0))

    np.testing.assert_allclose(sorted(real_scores), sorted(shuffled_scores))
