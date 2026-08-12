"""Unit tests for topology update rules (mathematical_contract.md Sec3.3).

NoTopologyUpdate is the Stage-1 default for every arm except Arm D's
one-shot rewire ([A8], [A14]) -- edges may appear or disappear only
through an explicit TopologyUpdateRule, never as a side effect of weight
adaptation.
"""

import numpy as np

from boyko_benchmark.dynamics.topology import NoTopologyUpdate
from boyko_benchmark.types import WeightedGraph


def test_no_topology_update_never_changes_mask() -> None:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    graph = WeightedGraph(mask=mask, weights=weights)

    updated = NoTopologyUpdate().update(graph, dtau=1.0)

    np.testing.assert_array_equal(updated.mask, graph.mask)
    np.testing.assert_array_equal(updated.weights, graph.weights)
