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
    """L_norm = I - D^-1/2 W D^-1/2."""
    degree = graph.weights.sum(axis=1)
    d_inv_sqrt = 1.0 / np.sqrt(degree)
    scaled_weights = d_inv_sqrt[:, None] * graph.weights * d_inv_sqrt[None, :]
    return np.eye(graph.n_nodes) - scaled_weights
