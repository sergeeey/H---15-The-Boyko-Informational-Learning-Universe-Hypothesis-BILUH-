"""Topology update rules (mathematical_contract.md Sec3.3).

Edges may appear or disappear only through an explicit TopologyUpdateRule
-- never as a side effect of weight adaptation or noise. NoTopologyUpdate
is the Stage-1 default for every arm except Arm D's one-shot rewire
([A8], [A14]); the rewire itself lives in graphs/rewiring.py as a
standalone construction function, not a repeated per-step rule, since it
runs exactly once (Active's final graph -> Arm D's initial graph), not on
every dtau step.
"""

from typing import Protocol

import numpy as np

from boyko_benchmark.types import WeightedGraph


class TopologyUpdateRule(Protocol):
    def update(self, graph: WeightedGraph, dtau: float) -> WeightedGraph: ...


class NoTopologyUpdate:
    """Identity rule -- topology never changes."""

    def update(self, graph: WeightedGraph, dtau: float) -> WeightedGraph:
        return graph


class PruneZeroWeightTopologyUpdate:
    """V3 pilot rule (`mathematical_contract.md` Sec3.3 addendum
    2026-08-14, `[A42]`, `null_results/20260814-open-system-
    geometrogenesis.md`): removes any edge whose weight has been driven
    to exactly 0.0 -- a zero-weight edge carries no coupling, so this
    makes explicit an effective topology change `[A42]` found the
    adaptation rule's non-negativity clamp already produces implicitly.

    Only ever REMOVES edges (`M_ij: 1 -> 0`), never adds one -- obeys
    Sec3.3's "no rule may add an edge" invariant. Idempotent: a graph
    with no zero-weight edges among its current mask is a fixed point.
    """

    def update(self, graph: WeightedGraph, dtau: float) -> WeightedGraph:
        new_mask = graph.mask & (graph.weights > 0.0)
        new_weights = np.where(new_mask, graph.weights, 0.0)
        return WeightedGraph(mask=new_mask, weights=new_weights)
