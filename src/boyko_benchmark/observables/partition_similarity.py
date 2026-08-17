"""Phase 12 (docs/phase12_spec.md): compare community PARTITIONS, not
just the scalar modularity value.

Why this module exists: Phase 11's Milestone 5 (`[A37]`) concluded that
the Cσ modularity effect is not correlation-specific, because real and
shuffled correlations produced statistically indistinguishable
modularity VALUES. Modularity Q is a scalar -- two entirely different
partitions (no shared community membership at all) can score the same Q.
That comparison therefore established "equally modular", not "the same
communities". This module supplies the missing partition-level measure.

Measure choice (deviation from phase12_spec.md's "AMI", documented not
silent): the spec named Adjusted Mutual Information, which would require
adding scikit-learn as a dependency for a single function. Adjusted Rand
Index (Hubert & Arabie 1985) is used instead -- same essential property
(correction for chance agreement, so independent partitions score ~0
rather than a size-dependent positive value), standard for network
community comparison, and implementable in ~20 lines with hand-derivable
test cases. Recorded in `[A40]`.
"""

from math import comb

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.observables.conductance import _greedy_communities
from boyko_benchmark.types import WeightedGraph


def partition_labels(graph: WeightedGraph) -> NDArray[np.integer]:
    """Community membership as a per-node integer label array, using the
    SAME detector `observables/conductance.py::modularity` already uses --
    so a partition compared here is exactly the partition whose Q was
    reported in `[A37]`/`[A39]`, not a second independent detection that
    might disagree for unrelated reasons.

    Cluster label VALUES carry no meaning (greedy modularity has no
    stable naming convention across runs); only the grouping does, which
    is why every comparison goes through `adjusted_rand_index`.
    """
    n = graph.n_nodes
    labels = np.zeros(n, dtype=np.int64)
    for community_index, community in enumerate(_greedy_communities(graph)):
        for node in community:
            labels[node] = community_index
    return labels


def adjusted_rand_index(
    labels_a: NDArray[np.integer] | list[int],
    labels_b: NDArray[np.integer] | list[int],
) -> float:
    """Adjusted Rand Index between two partitions of the same node set.

    1.0 = identical grouping (up to relabelling), ~0 = no more agreement
    than chance, negative = systematically LESS agreement than chance.

    The chance-correction term is the entire point: an unadjusted Rand
    index rises with cluster count and node count even for independent
    partitions, which would make "Cσ and H0 agree" unfalsifiable by
    construction.
    """
    a = np.asarray(labels_a)
    b = np.asarray(labels_b)
    if a.shape != b.shape:
        raise ValueError(f"partitions cover different node sets: {a.shape} vs {b.shape}")
    n_nodes = len(a)
    if n_nodes < 2:
        raise ValueError("adjusted_rand_index needs at least 2 nodes")

    unique_a = np.unique(a)
    unique_b = np.unique(b)
    contingency = np.zeros((len(unique_a), len(unique_b)), dtype=np.int64)
    for i, cluster_a in enumerate(unique_a):
        in_a = a == cluster_a
        for j, cluster_b in enumerate(unique_b):
            contingency[i, j] = int(np.sum(in_a & (b == cluster_b)))

    sum_pairs_joint = sum(comb(int(v), 2) for v in contingency.flatten())
    sum_pairs_a = sum(comb(int(v), 2) for v in contingency.sum(axis=1))
    sum_pairs_b = sum(comb(int(v), 2) for v in contingency.sum(axis=0))

    total_pairs = comb(n_nodes, 2)
    expected = sum_pairs_a * sum_pairs_b / total_pairs
    maximum = 0.5 * (sum_pairs_a + sum_pairs_b)
    if maximum == expected:
        # WHY: both partitions are trivial (all nodes in one cluster, or
        # all singletons). Agreement is then total but carries zero
        # information; 1.0 is the mathematically consistent limit and
        # avoids a 0/0 NaN propagating silently into a comparison table.
        return 1.0
    return float((sum_pairs_joint - expected) / (maximum - expected))
