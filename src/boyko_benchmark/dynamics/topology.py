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

from boyko_benchmark.types import WeightedGraph


class TopologyUpdateRule(Protocol):
    def update(self, graph: WeightedGraph, dtau: float) -> WeightedGraph: ...


class NoTopologyUpdate:
    """Identity rule -- topology never changes."""

    def update(self, graph: WeightedGraph, dtau: float) -> WeightedGraph:
        return graph
