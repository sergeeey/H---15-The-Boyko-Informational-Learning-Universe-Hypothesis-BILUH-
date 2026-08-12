"""Graph topology generators (mathematical_contract.md §4).

[A7]: Erdos-Renyi is used for Active's (and Frozen's, and Alternative
Objective's) shared initial topology specifically because it has no
spatial embedding to leak into the adaptive objective as an implicit
target geometry -- unlike a random geometric graph, which would.
"""

import networkx as nx
import numpy as np

from boyko_benchmark.types import WeightedGraph

INITIAL_EDGE_WEIGHT = 1.0
"""[A19]: uniform initial weight on every generated edge -- deliberately
structureless, so any geometric structure Active later develops comes
from the adaptation rule, not from a biased initial condition."""


def generate_erdos_renyi(n_nodes: int, n_edges: int, rng: np.random.Generator) -> WeightedGraph:
    """Generate a WeightedGraph with Erdos-Renyi topology.

    Uses exact edge-count matching ([A12] default: gnm, not gnp) so the
    same call can also produce Arm C's (Parameter-Matched Random) graph
    by reusing n_edges from Active's realized topology.
    """
    networkx_seed = int(rng.integers(0, 2**32 - 1))
    nx_graph = nx.gnm_random_graph(n_nodes, n_edges, seed=networkx_seed)

    mask = np.zeros((n_nodes, n_nodes), dtype=bool)
    weights = np.zeros((n_nodes, n_nodes), dtype=float)
    for i, j in nx_graph.edges():
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = INITIAL_EDGE_WEIGHT

    return WeightedGraph(mask=mask, weights=weights)
