"""Normalized Laplacian gap (mathematical_contract.md Sec5.2, G2).

lambda_1 = first non-zero eigenvalue of L_norm.

Scaling ansatz lambda_1(N) ~ N^-gamma is estimated from FSS-grid
regression (Phase 7), never hard-coded here -- gamma = 2/3 is explicitly
not assumed (ТЗ.txt Sec6).
"""

import numpy as np
from numpy.typing import NDArray


def laplacian_gap(laplacian: NDArray[np.floating], zero_tolerance: float = 1e-9) -> float:
    """First non-zero eigenvalue of a (normalized) Laplacian.

    zero_tolerance separates the zero eigenvalue(s) (multiplicity =
    number of connected components) from the first genuinely positive
    one -- documented, not a silently-chosen magic number: L_norm's
    spectrum is bounded in [0, 2), so 1e-9 is many orders of magnitude
    below any physically meaningful gap while comfortably above floating-
    point round-off on a well-conditioned eigendecomposition.
    """
    eigenvalues = np.sort(np.linalg.eigvalsh(laplacian))
    for eigenvalue in eigenvalues:
        if eigenvalue > zero_tolerance:
            return float(eigenvalue)
    raise ValueError("no non-zero eigenvalue found -- graph may be fully disconnected")
