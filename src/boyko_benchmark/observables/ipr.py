"""Low-mode inverse participation ratio (mathematical_contract.md Sec5.3, G4).

IPR(phi) = Sum_i |phi_i|^4, phi normalized: Sum_i |phi_i|^2 = 1.

Scaling ansatz IPR(N) ~ N^-eta is estimated from FSS-grid regression
(Phase 7); extended-mode calibration target eta ~ 1 is used only as a
calibration EXPECTATION, not baked into the estimator.
"""

import numpy as np
from numpy.typing import NDArray


def inverse_participation_ratio(eigenvector: NDArray[np.floating]) -> float:
    """IPR(phi) = Sum_i |phi_i|^4."""
    return float(np.sum(np.abs(eigenvector) ** 4))


def low_mode_eigenvectors(laplacian: NDArray[np.floating], n_modes: int) -> NDArray[np.floating]:
    """The n_modes eigenvectors with smallest eigenvalues (the
    'geometric'/smooth low-energy modes) of a Laplacian, each already
    normalized (Sum_i |phi_i|^2 = 1) by np.linalg.eigh's own convention.

    Returns shape (N, n_modes) -- column k is the k-th lowest mode.
    """
    eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
    order = np.argsort(eigenvalues)
    result: NDArray[np.floating] = eigenvectors[:, order[:n_modes]]
    return result
