"""H0 secondary control (Correlation Shuffle), proposed in the 2026-08-13
external red-team review: `H1` (structured correlations cause geometric
organization) vs `H0` (any reinforcement with the same correlation-
magnitude distribution suffices, regardless of which pair correlated).

`CorrelationShuffleAdaptation` runs the identical Oja-normalized update as
`HebbianAdaptation`, except the off-diagonal correlation values are
permuted across the graph's existing edges before being applied -- same
multiset of numbers, different (i,j) assignment. The diagonal (density,
used only by the decay term) is deliberately NOT shuffled: density is a
per-node quantity answering a different question than "which pair
correlated," shuffling it would conflate the two.

This is a usable `AdaptationRule`, not yet wired into `config.py`'s `Arm`
enum / `arms_runner.py` as an 8th experimental arm (docs/assumptions.md
records this as a documented next step, following [A26]'s own pattern of
recording partial-scope additions explicitly).

Hand-derived reference: 4-node path graph (edges 0-1, 1-2, 2-3), a single
real-valued snapshot `psi=[1,2,3,4]` makes `correlation[i,j] = psi_i*psi_j`
exactly (no numerical integration involved) -- edge correlations are
`(0,1)=2, (1,2)=6, (2,3)=12`, each a distinct value so shuffling is
detectable. `numpy.random.default_rng(0).permutation([2,6,12])` was cross-
checked via a Bash prototype before writing the assertions: `[12, 2, 6]`.
"""

import numpy as np

from boyko_benchmark.dynamics.adaptive import (
    CorrelationShuffleAdaptation,
    HebbianAdaptation,
    StateTrajectory,
    _shuffle_edge_correlations,
)
from boyko_benchmark.types import WeightedGraph


def _four_node_path_graph() -> WeightedGraph:
    mask = np.array(
        [
            [False, True, False, False],
            [True, False, True, False],
            [False, True, False, True],
            [False, False, True, False],
        ]
    )
    weights = np.zeros((4, 4))
    weights[mask] = 1.0
    return WeightedGraph(mask=mask, weights=weights)


def _correlation_from_real_psi(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, psi)


def test_shuffle_edge_correlations_preserves_multiset_of_edge_values() -> None:
    mask = _four_node_path_graph().mask
    correlation = _correlation_from_real_psi(np.array([1.0, 2.0, 3.0, 4.0]))
    rng = np.random.default_rng(0)

    shuffled = _shuffle_edge_correlations(correlation, mask, rng)

    edge_values = shuffled[mask]
    # each edge appears twice (symmetric matrix), so the multiset of
    # UNIQUE edge values must match {2, 6, 12} exactly.
    unique_values = sorted(set(edge_values.tolist()))
    assert unique_values == [2.0, 6.0, 12.0]


def test_shuffle_edge_correlations_matches_hand_derived_permutation() -> None:
    mask = _four_node_path_graph().mask
    correlation = _correlation_from_real_psi(np.array([1.0, 2.0, 3.0, 4.0]))
    rng = np.random.default_rng(0)

    shuffled = _shuffle_edge_correlations(correlation, mask, rng)

    # rng.permutation([2,6,12]) with seed 0 -> [12, 2, 6] (verified via
    # prototype), assigned in triu-scan order: (0,1)->12, (1,2)->2, (2,3)->6.
    assert shuffled[0, 1] == 12.0
    assert shuffled[1, 0] == 12.0
    assert shuffled[1, 2] == 2.0
    assert shuffled[2, 3] == 6.0


def test_shuffle_edge_correlations_leaves_non_edges_and_diagonal_zero() -> None:
    mask = _four_node_path_graph().mask
    correlation = _correlation_from_real_psi(np.array([1.0, 2.0, 3.0, 4.0]))
    rng = np.random.default_rng(0)

    shuffled = _shuffle_edge_correlations(correlation, mask, rng)

    assert shuffled[0, 2] == 0.0  # non-edge
    assert shuffled[0, 3] == 0.0  # non-edge
    for i in range(4):
        assert shuffled[i, i] == 0.0  # diagonal untouched by this function


def test_correlation_shuffle_adaptation_differs_from_hebbian_on_same_input() -> None:
    """With a fixed seed producing a non-identity permutation, the two
    rules must diverge -- confirms the shuffle rule actually feeds the
    permuted correlation into the update, not silently falling back to
    the unshuffled one."""
    graph = _four_node_path_graph()
    psi = np.array([1.0, 2.0, 3.0, 4.0], dtype=complex)
    trajectory = StateTrajectory(states=psi[None, :])

    hebbian_result = HebbianAdaptation(eta=0.1).update(graph, trajectory, dtau=1.0)
    shuffle_result = CorrelationShuffleAdaptation(eta=0.1, rng=np.random.default_rng(0)).update(
        graph, trajectory, dtau=1.0
    )

    assert not np.allclose(hebbian_result.weights, shuffle_result.weights)


def test_correlation_shuffle_adaptation_preserves_graph_invariants() -> None:
    graph = _four_node_path_graph()
    psi = np.array([1.0, 2.0, 3.0, 4.0], dtype=complex)
    trajectory = StateTrajectory(states=psi[None, :])

    result = CorrelationShuffleAdaptation(eta=0.1, rng=np.random.default_rng(0)).update(
        graph, trajectory, dtau=1.0
    )

    assert np.array_equal(result.mask, graph.mask)
    assert np.all(result.weights >= 0.0)
    assert np.all((result.weights > 0) <= result.mask)
