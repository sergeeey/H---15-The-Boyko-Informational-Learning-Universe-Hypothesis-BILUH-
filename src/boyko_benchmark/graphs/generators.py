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

_MAX_CONNECTIVITY_RETRY_ATTEMPTS = 20
"""[Found 2026-08-13, development.yaml's first full-grid run]:
`nx.gnm_random_graph`'s exact edge-count draw has no connectivity
guarantee -- at N=64, mean-degree-6 ([A7], n_edges=192), a disconnected
draw is empirically reachable (witness: numpy_seed=18, see
tests/unit/check_erdos_renyi_connectivity.py), and every downstream
observable in mathematical_contract.md assumes a connected graph
(docs/estimand.md's "population restricted to connected graphs upstream").
Retrying with a fresh seed on a connectivity failure follows the same
legitimate-recovery pattern as graphs/rewiring.py's
`_MAX_RETRY_ATTEMPTS` (a failed draw is not evidence the request is
infeasible for this (n_nodes, n_edges), just that this particular random
draw was unlucky) -- silently returning a disconnected graph would violate
the estimand's population assumption without any error surfacing until an
arbitrary downstream consumer trips on it, as happened here."""


def generate_erdos_renyi(n_nodes: int, n_edges: int, rng: np.random.Generator) -> WeightedGraph:
    """Generate a WeightedGraph with Erdos-Renyi topology.

    Uses exact edge-count matching ([A12] default: gnm, not gnp) so the
    same call can also produce Arm C's (Parameter-Matched Random) graph
    by reusing n_edges from Active's realized topology.

    Retries with a fresh networkx seed (same n_nodes/n_edges) up to
    `_MAX_CONNECTIVITY_RETRY_ATTEMPTS` times if a draw is disconnected --
    docs/estimand.md's connected-population assumption is enforced here,
    not just declared.
    """
    last_nx_graph: nx.Graph[int] | None = None
    for _ in range(_MAX_CONNECTIVITY_RETRY_ATTEMPTS):
        networkx_seed = int(rng.integers(0, 2**32 - 1))
        nx_graph = nx.gnm_random_graph(n_nodes, n_edges, seed=networkx_seed)
        if nx.is_connected(nx_graph):
            last_nx_graph = nx_graph
            break
        last_nx_graph = nx_graph
    else:
        raise nx.NetworkXAlgorithmError(
            f"generate_erdos_renyi: no connected draw found for n_nodes={n_nodes}, "
            f"n_edges={n_edges} after {_MAX_CONNECTIVITY_RETRY_ATTEMPTS} retries -- "
            "this (n_nodes, n_edges) combination may be too sparse to reliably "
            "produce a connected graph."
        )

    mask = np.zeros((n_nodes, n_nodes), dtype=bool)
    weights = np.zeros((n_nodes, n_nodes), dtype=float)
    for i, j in last_nx_graph.edges():
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = INITIAL_EDGE_WEIGHT

    return WeightedGraph(mask=mask, weights=weights)
