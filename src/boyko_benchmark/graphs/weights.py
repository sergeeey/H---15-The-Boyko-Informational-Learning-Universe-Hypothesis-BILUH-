"""Laplacians derived from a WeightedGraph (mathematical_contract.md Sec1.2).

Two Laplacians are kept deliberately distinct, not interchangeable:

- combinatorial L = D - W: zero eigenvector is 1 (the all-ones vector).
  This is the Laplacian Milestone-1's `L.1=0` test targets.
- normalized L_norm = I - D^-1/2 W D^-1/2: zero eigenvector is D^1/2 . 1,
  NOT 1. Spectrum bounded in [0, 2). This is the operator used for the
  fast-dynamics Hamiltonian (dynamics/fast.py) and for the eigenstructure
  observables (G1/G2/G4) on L_norm-driven trajectories -- see the
  Operator-Matching Rule in mathematical_contract.md Sec5.
"""

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.types import WeightedGraph


def combinatorial_laplacian(graph: WeightedGraph) -> NDArray[np.floating]:
    """L = D - W."""
    degree: NDArray[np.floating] = graph.weights.sum(axis=1)
    result: NDArray[np.floating] = np.diag(degree) - graph.weights
    return result


def normalized_laplacian(graph: WeightedGraph) -> NDArray[np.floating]:
    """L_norm = I - D^-1/2 W D^-1/2.

    A node whose weights have all decayed to zero (a legal state under
    HebbianAdaptation's non-negativity floor, [A5]) has degree=0. The
    standard convention for the normalized Laplacian on such a node is
    d_inv_sqrt=0, not inf/nan -- row/column i is then all-zero in
    scaled_weights, so L_norm's diagonal entry for that node stays 1 and
    it does not couple to any neighbor. Found 2026-08-13: the development
    config's longer adaptation budget (dtau_steps=200) reached this state
    where smoke's short budget (dtau_steps=5) never did; the un-guarded
    1/sqrt(0) produced NaN that corrupted downstream dynamics.
    """
    degree = graph.weights.sum(axis=1)
    with np.errstate(divide="ignore"):
        d_inv_sqrt = np.where(degree > 0, 1.0 / np.sqrt(degree), 0.0)
    scaled_weights = d_inv_sqrt[:, None] * graph.weights * d_inv_sqrt[None, :]
    result: NDArray[np.floating] = np.eye(graph.n_nodes) - scaled_weights
    return result
