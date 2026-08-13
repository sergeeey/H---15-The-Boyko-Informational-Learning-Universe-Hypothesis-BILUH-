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

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats


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


@dataclass(frozen=True)
class PlateauResult:
    """Real plateau detection for G1 (`[A30]`, docs/assumptions.md),
    replacing the provisional `d_s(t_last)` surrogate. `converged=False`
    means no contiguous window met `slope_tolerance` -- callers must not
    treat `d_s_hat` as meaningful in that case (it is a documented
    fallback, not a plateau estimate)."""

    d_s_hat: float
    t_window: tuple[float, float]
    log_width: float
    slope: float
    r_squared: float
    n_points: int
    converged: bool


def detect_plateau(
    t_values: NDArray[np.floating],
    d_s_values: NDArray[np.floating],
    min_points: int = 3,
    slope_tolerance: float = 0.1,
    range_tolerance: float = 0.3,
) -> PlateauResult:
    """Scans every contiguous window of at least `min_points` points and
    picks the one that qualifies (see below) with the most points
    (log-t span as tiebreak) -- see this module's own docstring and
    `[A30]` for why `|slope|` is one gate, not an R^2-of-the-flat-fit
    threshold.

    A window qualifies only if BOTH:
    - `|slope of d_s vs log(t)| <= slope_tolerance`
    - `max(d_s in window) - min(d_s in window) <= range_tolerance`

    The range check was added 2026-08-13 after running the `[A9]` sweep:
    a rise-then-fall "hump" in `d_s(t)` (a real shape this project's own
    curves show -- rises toward a peak, then declines at large t, not a
    genuine plateau) can have a near-zero AGGREGATE linear-regression
    slope purely because the rise and fall cancel out, while individual
    points scatter across a wide range (witness: a real Active-arm curve
    at N=64 was reported `converged=True` by the slope-only version with
    `d_s_hat` averaged over points `[1.97, 2.60, 3.14, 3.27, 2.61, 2.03]`
    -- range 1.3, `R^2=0.002` near zero, i.e. NOT actually a flat line,
    a false positive). Slope alone cannot distinguish "flat" from
    "symmetric hump" gone through the middle; range can.

    `slope_tolerance`, `range_tolerance`, and `min_points` are provisional
    defaults (`[A30]`) -- not calibrated against a larger corpus of real
    Active-arm `d_s(t)` curves, since no production run exists yet to
    calibrate against.
    """
    n = len(t_values)
    log_t = np.log(t_values)
    best: tuple[int, float, int, int, float, float] | None = (
        None  # (n_pts, width, start, end, slope, r2)
    )

    for start in range(n):
        for end in range(start + min_points, n + 1):
            t_window = log_t[start:end]
            d_window = d_s_values[start:end]
            n_pts = end - start
            width = float(t_window[-1] - t_window[0])

            if np.allclose(d_window, d_window[0]):
                slope, r_squared = 0.0, 1.0
            else:
                regression = stats.linregress(t_window, d_window)
                slope = float(regression.slope)
                r_squared = float(regression.rvalue) ** 2

            window_range = float(np.max(d_window) - np.min(d_window))
            if abs(slope) > slope_tolerance or window_range > range_tolerance:
                continue

            key = (n_pts, width)
            if best is None or key > (best[0], best[1]):
                best = (n_pts, width, start, end, slope, r_squared)

    if best is None:
        return PlateauResult(
            d_s_hat=float(d_s_values[-1]),
            t_window=(float(t_values[0]), float(t_values[-1])),
            log_width=float(log_t[-1] - log_t[0]) if n > 1 else 0.0,
            slope=float("nan"),
            r_squared=float("nan"),
            n_points=0,
            converged=False,
        )

    n_pts, width, start, end, slope, r_squared = best
    return PlateauResult(
        d_s_hat=float(np.mean(d_s_values[start:end])),
        t_window=(float(t_values[start]), float(t_values[end - 1])),
        log_width=width,
        slope=slope,
        r_squared=r_squared,
        n_points=n_pts,
        converged=True,
    )
