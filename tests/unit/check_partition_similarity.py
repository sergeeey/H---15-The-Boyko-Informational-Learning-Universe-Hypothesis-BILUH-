"""Phase 12 Stage 0 (docs/phase12_spec.md): partition comparison for the
Cσ modularity re-test.

Every numeric expectation below was cross-checked with a standalone
prototype run BEFORE being written as an assertion (this project's
prototype-verify-then-assert discipline), including the -0.5 case which
is hand-derivable from the ARI definition:

    A = [0,0,1,1], B = [0,1,0,1]
    contingency all-ones 2x2 -> sum_ij C(1,2) = 0
    a_i = (2,2) -> sum C(2,2) = 2;  b_j = (2,2) -> sum = 2
    expected = 2*2/C(4,2) = 4/6 = 2/3;  max = (2+2)/2 = 2
    ARI = (0 - 2/3) / (2 - 2/3) = -0.5
"""

import networkx as nx
import numpy as np

from boyko_benchmark.observables.partition_similarity import (
    adjusted_rand_index,
    partition_labels,
)
from boyko_benchmark.types import WeightedGraph


def test_ari_is_one_for_identical_partitions() -> None:
    assert adjusted_rand_index([0, 0, 1, 1], [0, 0, 1, 1]) == 1.0


def test_ari_is_label_invariant() -> None:
    """A partition is a grouping, not a labelling -- renaming clusters
    must not change the score, or every comparison below is meaningless
    (greedy_modularity_communities has no stable cluster-naming
    convention across runs)."""
    assert adjusted_rand_index([0, 0, 1, 1], [7, 7, 3, 3]) == 1.0


def test_ari_matches_hand_derived_crossed_partition() -> None:
    """Hand-derived in this module's docstring: two partitions that agree
    on no pair score -0.5, i.e. WORSE than chance, not 0. Pins the
    chance-correction term, which is the whole point of using an
    *adjusted* index."""
    assert abs(adjusted_rand_index([0, 0, 1, 1], [0, 1, 0, 1]) - (-0.5)) < 1e-12


def test_ari_of_independent_random_partitions_is_near_zero() -> None:
    """The chance floor. Verified over 20 prototype trials at n=200
    (mean=0.0003, max=0.0284) -- the 0.05 bound here is above that
    observed maximum, not a guess."""
    rng = np.random.default_rng(0)

    scores = [
        adjusted_rand_index(rng.integers(0, 4, 200), rng.integers(0, 4, 200)) for _ in range(20)
    ]

    assert max(abs(s) for s in scores) < 0.05


def test_partition_labels_recovers_obvious_two_community_structure() -> None:
    """Barbell fixture reused from check_conductance.py: two triangles
    joined by one edge. Any usable community detector must put each
    triangle in its own group -- if this fails, the detector is not fit
    for Phase 12's comparisons regardless of what ARI reports."""
    n = 6
    mask = np.zeros((n, n), dtype=bool)
    weights = np.zeros((n, n))
    for i, j in [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (2, 3)]:
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = 1.0
    graph = WeightedGraph(mask=mask, weights=weights)

    labels = partition_labels(graph)

    assert labels[0] == labels[1] == labels[2]
    assert labels[3] == labels[4] == labels[5]
    assert labels[0] != labels[3]


def test_partition_labels_is_deterministic_on_repeated_calls() -> None:
    """Phase 12 Stage 0's substrate gate, as a permanent regression test:
    every AMI/ARI comparison in Phase 12 is confounded if the detector
    returns a different partition for the same input. This must hold on a
    graph large enough for greedy modularity to have real choices to
    make, not just the 6-node barbell."""
    rng = np.random.default_rng(42)
    nx_graph = nx.gnm_random_graph(200, 600, seed=7)
    mask = np.zeros((200, 200), dtype=bool)
    weights = np.zeros((200, 200))
    for i, j in nx_graph.edges():
        mask[i, j] = mask[j, i] = True
        w = float(rng.uniform(0.5, 1.5))
        weights[i, j] = weights[j, i] = w
    graph = WeightedGraph(mask=mask, weights=weights)

    first = partition_labels(graph)
    second = partition_labels(graph)

    assert adjusted_rand_index(first, second) == 1.0
