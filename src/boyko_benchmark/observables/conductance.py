"""Phase 11 mechanistic diagnostics (ТЗ §12.6-12.7): modularity and a
direct connectivity/bottleneck metric (conductance), neither reducible
to a single binary Gate-A pass/fail.
"""

import networkx as nx
import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.graphs.weights import combinatorial_laplacian
from boyko_benchmark.types import WeightedGraph


def spectral_conductance(graph: WeightedGraph) -> float:
    """Cheeger-like bottleneck statistic (ТЗ §12.7): bipartitions the
    graph by the SIGN of the Fiedler vector (second-smallest eigenvector
    of the combinatorial Laplacian -- the standard spectral bisection,
    Cheeger's inequality connects this partition's conductance to
    lambda_2) and reports

        conductance = cut(S, S-bar) / min(vol(S), vol(S-bar))

    Low conductance -> a genuine bottleneck/community boundary exists
    (e.g. a barbell graph). High conductance (up to 1.0 for e.g. a
    complete graph) -> no good separator, well-mixed/expander-like.

    Degenerate cases (disconnected graph, N<2) return 0.0 -- a
    disconnected graph trivially has a zero-cut bipartition, which is
    the mathematically correct (not a fallback/error) conductance value.
    """
    n = graph.n_nodes
    if n < 2:
        return 0.0
    laplacian = combinatorial_laplacian(graph)
    eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
    fiedler = eigenvectors[:, 1]
    partition = fiedler > 0
    if not partition.any() or partition.all():
        # Fiedler vector didn't split the graph (e.g. a fully symmetric
        # or disconnected structure) -- fall back to the trivial
        # half-split by index, still well-defined, not an error.
        partition = np.arange(n) < n // 2

    degree: NDArray[np.floating] = graph.weights.sum(axis=1)
    vol_s = float(degree[partition].sum())
    vol_s_complement = float(degree[~partition].sum())
    if vol_s == 0.0 or vol_s_complement == 0.0:
        return 0.0
    cut = float(graph.weights[np.ix_(partition, ~partition)].sum())
    return cut / min(vol_s, vol_s_complement)


def modularity(graph: WeightedGraph) -> float:
    """Newman modularity Q (ТЗ §12.6), using networkx's greedy-modularity
    community detection (reused, not reimplemented) on the weighted
    graph. Q close to 0 (or negative) -> no meaningful community
    structure; Q closer to its practical ceiling (~0.3-0.7 for typical
    modular networks) -> genuine modular organization.
    """
    n = graph.n_nodes
    if n < 2:
        return 0.0
    nx_graph = nx.from_numpy_array(graph.weights)
    if nx_graph.number_of_edges() == 0:
        return 0.0
    communities = [
        set(community)
        for community in nx.algorithms.community.greedy_modularity_communities(
            nx_graph, weight="weight"
        )
    ]
    return float(nx.algorithms.community.quality.modularity(nx_graph, communities, weight="weight"))
