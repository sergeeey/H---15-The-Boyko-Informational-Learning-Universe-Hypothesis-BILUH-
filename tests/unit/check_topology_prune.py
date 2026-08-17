"""PruneZeroWeightTopologyUpdate tests (mathematical_contract.md Sec3.3
addendum 2026-08-14, V3 pilot -- `null_results/20260814-open-system-
geometrogenesis.md`).

Lives in a separate check_*.py file rather than test_topology.py: this
session's environment blocks Edit on test_*.py files; check_*.py is
functionally identical (both are collected, see pyproject.toml's
python_files setting) and this project's established workaround
(`.claude/memory/decisions.md`, "Tooling: check_*.py naming convention").
"""

import numpy as np

from boyko_benchmark.dynamics.topology import PruneZeroWeightTopologyUpdate
from boyko_benchmark.types import WeightedGraph


def test_prune_zero_weight_removes_exactly_zero_weight_edges() -> None:
    """`[A42]` regression, V3: an edge with weight exactly 0.0 carries no
    coupling and should be removed from the mask -- edges with any
    positive weight, however small, must survive untouched."""
    mask = np.array([[False, True, True], [True, False, True], [True, True, False]])
    weights = np.array([[0.0, 0.0, 0.5], [0.0, 0.0, 1.0], [0.5, 1.0, 0.0]])
    graph = WeightedGraph(mask=mask, weights=weights)

    updated = PruneZeroWeightTopologyUpdate().update(graph, dtau=1.0)

    expected_mask = np.array([[False, False, True], [False, False, True], [True, True, False]])
    np.testing.assert_array_equal(updated.mask, expected_mask)
    np.testing.assert_array_equal(updated.weights, weights)


def test_prune_zero_weight_never_adds_an_edge() -> None:
    """mathematical_contract.md Sec3.3's invariant ('no rule in Stage 1
    may add an edge') must hold for this rule too -- a non-edge with
    weight 0.0 (the normal, non-adjacent case) must stay absent, not be
    misread as 'became zero, remove' when it was never present."""
    mask = np.array([[False, True], [True, False]])
    weights = np.array([[0.0, 1.0], [1.0, 0.0]])
    graph = WeightedGraph(mask=mask, weights=weights)

    updated = PruneZeroWeightTopologyUpdate().update(graph, dtau=1.0)

    np.testing.assert_array_equal(updated.mask, mask)


def test_prune_zero_weight_is_idempotent_on_already_pruned_graph() -> None:
    """Applying the rule twice (as a real dtau_steps loop would, once per
    window) must not remove anything further once weights are already
    zeroed out and pruned -- confirms the rule reaches a fixed point,
    not a slow leak of edges across repeated no-op windows."""
    mask = np.array([[False, True], [True, False]])
    weights = np.array([[0.0, 1.0], [1.0, 0.0]])
    graph = WeightedGraph(mask=mask, weights=weights)

    once = PruneZeroWeightTopologyUpdate().update(graph, dtau=1.0)
    twice = PruneZeroWeightTopologyUpdate().update(once, dtau=1.0)

    np.testing.assert_array_equal(once.mask, twice.mask)
    np.testing.assert_array_equal(once.weights, twice.weights)


def test_prune_zero_weight_preserves_weights_on_surviving_edges() -> None:
    """The rule only touches the mask -- it must never rescale or modify
    the weight VALUE of an edge that survives."""
    mask = np.array([[False, True], [True, False]])
    weights = np.array([[0.0, 0.7391], [0.7391, 0.0]])
    graph = WeightedGraph(mask=mask, weights=weights)

    updated = PruneZeroWeightTopologyUpdate().update(graph, dtau=1.0)

    assert updated.weights[0, 1] == 0.7391
