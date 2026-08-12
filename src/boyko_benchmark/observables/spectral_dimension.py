"""Heat-kernel spectral dimension (mathematical_contract.md Sec5.1, G1).

P_return(t) = Tr(exp(-t L_norm)) / N
d_s(t) = -2 d ln(P_return(t)) / d ln(t)

Correction 4: never treat `I - L_norm` as a standard random-walk
transition matrix -- this module only ever uses the heat-kernel form
above.

[A13]: for large N, the contract calls for a stochastic (Hutchinson)
trace estimator instead of the exact eigendecomposition used here. Not
implemented yet -- exact computation is correct, just O(N^3), acceptable
for calibration/development sizes (N <= 512 in this project's configs).
Swap in a stochastic estimator before production-scale runs if N grows
past what exact eigendecomposition can handle in reasonable time.
"""

import numpy as np
from numpy.typing import NDArray


def heat_kernel_trace(laplacian: NDArray[np.floating], t: float) -> float:
    """Tr(exp(-t L)) via exact eigendecomposition."""
    eigenvalues = np.linalg.eigvalsh(laplacian)
    return float(np.sum(np.exp(-t * eigenvalues)))


def return_probability(laplacian: NDArray[np.floating], t: float) -> float:
    """P_return(t) = Tr(exp(-t L)) / N."""
    n_nodes = laplacian.shape[0]
    return float(heat_kernel_trace(laplacian, t) / n_nodes)


def spectral_dimension(
    laplacian: NDArray[np.floating], t_values: NDArray[np.floating]
) -> NDArray[np.floating]:
    """d_s(t) = -2 d ln(P_return(t)) / d ln(t), estimated via a central
    finite difference on a log-log grid (np.gradient)."""
    log_t = np.log(t_values)
    p_return = np.array([return_probability(laplacian, t) for t in t_values])
    log_p = np.log(p_return)
    result: NDArray[np.floating] = -2.0 * np.gradient(log_p, log_t)
    return result
