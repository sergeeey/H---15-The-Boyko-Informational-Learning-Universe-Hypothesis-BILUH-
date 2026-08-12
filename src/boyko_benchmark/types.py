"""Core graph data type (mathematical_contract.md §1.1).

Topology and weights are two separate objects, deliberately not merged
into one array: `WeightedGraph.mask` (topology, boolean) may only change
through an explicit TopologyUpdateRule (Phase 4+); `WeightedGraph.weights`
may only change through an AdaptationRule (Phase 3+). Weights adaptation
must never silently create an edge absent from the mask -- enforced here
by rejecting any weight where the mask is False at construction time,
which is the invariant every later mutation must also preserve.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class WeightedGraph:
    """A weighted undirected graph with topology and weights kept separate.

    Args:
        mask: (N, N) boolean array. Symmetric, zero diagonal (no self-loops).
            True where an edge exists.
        weights: (N, N) float array. Symmetric, non-negative, zero diagonal.
            weights[i, j] > 0 requires mask[i, j] to be True.
    """

    mask: NDArray[np.bool_]
    weights: NDArray[np.floating]

    def __post_init__(self) -> None:
        if not np.array_equal(self.mask, self.mask.T):
            raise ValueError("mask must be symmetric")
        if not np.allclose(self.weights, self.weights.T):
            raise ValueError("weights must be symmetric")
        if np.any(self.weights < 0):
            raise ValueError("weights must be non-negative")
        if np.any(np.diagonal(self.mask)):
            raise ValueError("mask must have no self-loop (zero diagonal)")
        if np.any((self.weights > 0) & ~self.mask):
            raise ValueError("weight present without a topology edge (mask is False)")

    @property
    def n_nodes(self) -> int:
        return int(self.weights.shape[0])
