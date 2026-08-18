"""M2 (`docs/v4_spec.md` Sec7, K1 gate): controlled lattice damage for
the K1 positive control -- corrupt a known-geometric graph, then ask
whether V4's regrowth rule can restore the SPECIFIC edges that were
actually removed.

Reuses `scramble_preserving_degree_sequence` (Arm D's degree-preserving
double_edge_swap, `graphs/rewiring.py`) rather than reimplementing edge
rewiring -- this module's only new responsibility is exposing exactly
which edges were removed, which K1's `R_edge` needs and the existing
scramble utility does not return.
"""

import numpy as np

from boyko_benchmark.graphs.rewiring import scramble_preserving_degree_sequence
from boyko_benchmark.types import WeightedGraph

Edge = tuple[int, int]


def corrupt_lattice_edges(
    graph: WeightedGraph, rng: np.random.Generator, fraction: float
) -> tuple[WeightedGraph, frozenset[Edge]]:
    """Rewire approximately `fraction` of `graph`'s edges (`docs/v4_
    spec.md` Sec7: "randomly rewiring 10% of its edges"). Each double-
    edge-swap removes exactly 2 existing edges and adds 2 new ones, so
    `n_swaps = round(target_removed / 2)` targets the requested count;
    the realized count can fall short (networkx internally rejects
    duplicate/self-loop swap attempts) -- `E_damaged_out` reports what
    ACTUALLY happened via direct set difference, never the target count.

    Returns `(G_damaged, E_damaged_out)` where `E_damaged_out` is the
    set of `graph`'s original edges no longer present in `G_damaged` --
    exactly the edges K1's `R_edge` checks for restoration.
    """
    n_edges = int(graph.mask.sum()) // 2
    target_removed = round(fraction * n_edges)
    n_swaps = max(1, round(target_removed / 2))

    original_edges = frozenset((int(i), int(j)) for i, j in np.argwhere(np.triu(graph.mask)))
    damaged = scramble_preserving_degree_sequence(graph, rng, n_swaps)
    damaged_edges = frozenset((int(i), int(j)) for i, j in np.argwhere(np.triu(damaged.mask)))

    damaged_out = original_edges - damaged_edges
    return damaged, damaged_out
