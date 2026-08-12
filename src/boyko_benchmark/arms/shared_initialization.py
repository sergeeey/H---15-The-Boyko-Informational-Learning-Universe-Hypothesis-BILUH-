"""Shared initialization for Active, Frozen, Alternative Objective, and
Classical Diffusion Control (mathematical_contract.md Sec4's
shared-initialization rule, extended to Arm CD in that same section).

Also provides Arm C (Parameter-Matched Random)'s construction, which
deliberately does NOT share this initialization -- [A7]: independent ER
draw, same node/edge count, no correlation-driven topology.
"""

from dataclasses import dataclass

import numpy as np

from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.types import WeightedGraph


@dataclass(frozen=True)
class SharedInitialization:
    """Bit-identical (M(0), W(0)) shared by Active, Frozen, Alternative
    Objective, and Classical Diffusion Control. source_nodes are the
    [A17] multi-source-averaging set, drawn from the same seed stream so
    every arm sharing this initialization also shares the same source
    nodes for a paired propagation-front comparison."""

    graph: WeightedGraph
    source_nodes: tuple[int, ...]


def build_shared_initialization(
    n_nodes: int,
    n_edges: int,
    rng: np.random.Generator,
    n_source_nodes: int = 5,
) -> SharedInitialization:
    """[A7]: Erdos-Renyi topology, no spatial embedding. [A17]: n_source_
    nodes (default 5) drawn without replacement from the same rng."""
    graph = generate_erdos_renyi(n_nodes, n_edges, rng)
    n_to_draw = min(n_source_nodes, n_nodes)
    source_nodes = tuple(int(i) for i in rng.choice(n_nodes, size=n_to_draw, replace=False))
    return SharedInitialization(graph=graph, source_nodes=source_nodes)


def build_parameter_matched_random_graph(
    n_nodes: int, n_edges: int, rng: np.random.Generator
) -> WeightedGraph:
    """Arm C (Parameter-Matched Random): independent Erdos-Renyi draw,
    same node/edge count as the shared initialization's graph, but a
    fresh seed -- deliberately NOT sharing (M(0), W(0)) with A/B/F/CD,
    since Arm C isolates "does this specific graph realization matter",
    not "does adaptation matter" ([A7], mathematical_contract.md Sec4)."""
    return generate_erdos_renyi(n_nodes, n_edges, rng)
