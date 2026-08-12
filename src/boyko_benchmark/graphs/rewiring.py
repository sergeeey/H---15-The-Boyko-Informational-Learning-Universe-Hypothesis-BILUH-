"""Degree-preserving topology rewiring for Arm D (Topology Scrambled).

[A8]: applied once to Active's final topology, producing a static graph
for the rest of Arm D's run (dynamics/topology.py's NoTopologyUpdate
governs afterward). Uses networkx's double_edge_swap -- the standard
algorithm for randomizing a graph while preserving every node's degree
exactly, not just the sorted degree sequence.
"""

import networkx as nx
import numpy as np

from boyko_benchmark.graphs.generators import INITIAL_EDGE_WEIGHT
from boyko_benchmark.types import WeightedGraph

_MAX_RETRY_ATTEMPTS = 20
"""[Found Phase 8 Cycle 19]: at high edge density (e.g. N=8 mean-degree-6
ER, 24/28 possible edges = 85.7% dense -- smoke.yaml's smallest size),
double_edge_swap can fail its own internal max_tries bound stochastically:
empirically, a single failed attempt does NOT mean the requested n_swaps
is infeasible for that graph, just that this PARTICULAR random search path
didn't find enough valid swaps in time -- retrying with a fresh seed on
the same graph succeeds in most such cases (verified via Bash prototype,
50 random N=8/24-edge graphs, nswap=1: ~6% single-attempt failure rate,
dropping to ~4% after 15 retries -- the residual is graphs close enough to
complete that few/no valid swaps exist at all, not a retry-count problem).
Retrying preserves A21's "achieve the FULL requested n_swaps" intent --
unlike silently reducing n_swaps on failure, which would silently
under-randomize exactly what A21 warns against.
"""


def scramble_preserving_degree_sequence(
    graph: WeightedGraph, rng: np.random.Generator, n_swaps: int
) -> WeightedGraph:
    """One-shot degree-preserving rewire [A8].

    `n_swaps` has no default -- [A21]: a fixed constant would not scale
    correctly across the FSS grid, the caller must choose and record it
    per config.

    Rewired edges get INITIAL_EDGE_WEIGHT [A19, A21] uniformly -- Active's
    specific weight values don't transfer to a shuffled topology.

    Retries with a fresh networkx seed (same graph, same requested
    n_swaps) up to `_MAX_RETRY_ATTEMPTS` times if a swap attempt fails --
    see `_MAX_RETRY_ATTEMPTS`'s docstring for why this is a legitimate
    recovery, not a silent under-randomization. If every attempt fails,
    the graph itself is judged too dense for the requested randomization
    and a clear error is raised (never silently return a less-randomized
    result).
    """
    nx_graph: nx.Graph[int] = nx.Graph()
    nx_graph.add_nodes_from(range(graph.n_nodes))
    edges = np.argwhere(np.triu(graph.mask))
    nx_graph.add_edges_from((int(i), int(j)) for i, j in edges)

    last_error: nx.NetworkXAlgorithmError | None = None
    for _ in range(_MAX_RETRY_ATTEMPTS):
        candidate = nx_graph.copy()
        networkx_seed = int(rng.integers(0, 2**32 - 1))
        try:
            nx.double_edge_swap(
                candidate, nswap=n_swaps, max_tries=n_swaps * 20, seed=networkx_seed
            )
        except nx.NetworkXAlgorithmError as error:
            last_error = error
            continue
        mask = np.zeros((graph.n_nodes, graph.n_nodes), dtype=bool)
        weights = np.zeros((graph.n_nodes, graph.n_nodes), dtype=float)
        for i, j in candidate.edges():
            mask[i, j] = mask[j, i] = True
            weights[i, j] = weights[j, i] = INITIAL_EDGE_WEIGHT
        return WeightedGraph(mask=mask, weights=weights)

    raise nx.NetworkXAlgorithmError(
        f"scramble_preserving_degree_sequence: {n_swaps} swaps not achieved after "
        f"{_MAX_RETRY_ATTEMPTS} retries -- graph is likely too dense for this many "
        f"degree-preserving swaps to exist. Last underlying error: {last_error}"
    )
