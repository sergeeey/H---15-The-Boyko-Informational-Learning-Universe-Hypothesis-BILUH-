"""Effective resistance (G3, mathematical_contract.md Sec5.4).

R_eff(i,j) = L+_ii + L+_jj - 2*L+_ij, L+ is the Moore-Penrose pseudoinverse
of the COMBINATORIAL Laplacian (not L_norm -- see the Operator-Matching
Rule in Sec5 of the contract).

Replaces an original hop-count-diameter design that was dead by
construction under fixed topology (Cohen's d=0 vs Frozen guaranteed) --
found by the 1st DDD skeptic pass, see .claude/memory/decisions.md.
Effective resistance is genuinely weight-sensitive even when the topology
mask never changes, which is what makes it usable as a G3 gate observable.
"""

import numpy as np
from numpy.typing import NDArray


def effective_resistance_matrix(laplacian: NDArray[np.floating]) -> NDArray[np.floating]:
    """R_eff(i,j) = L+_ii + L+_jj - 2*L+_ij for every pair (i, j)."""
    pseudo_inverse = np.linalg.pinv(laplacian)
    diagonal = np.diagonal(pseudo_inverse)
    result: NDArray[np.floating] = diagonal[:, None] + diagonal[None, :] - 2 * pseudo_inverse
    return result


def resistance_diameter(laplacian: NDArray[np.floating]) -> float:
    """max_{i,j} R_eff(i,j) -- the G3 gate observable."""
    return float(np.max(effective_resistance_matrix(laplacian)))


def mean_effective_resistance(laplacian: NDArray[np.floating]) -> float:
    """Average R_eff over all distinct pairs (i != j)."""
    resistance = effective_resistance_matrix(laplacian)
    n_nodes = laplacian.shape[0]
    off_diagonal_sum = float(np.sum(resistance)) - float(np.trace(resistance))
    n_pairs = n_nodes * (n_nodes - 1)
    return float(off_diagonal_sum / n_pairs)
