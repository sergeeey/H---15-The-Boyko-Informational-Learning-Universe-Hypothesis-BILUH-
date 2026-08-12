"""Finite-size scaling regressions (mathematical_contract.md Sec6, Sec9 of
TZ.txt). gamma (G2 gap), eta (G4 IPR), delta (G3 resistance diameter) are
ALWAYS estimated from a log-log regression across the FSS grid, never
hard-coded (ТЗ.txt Sec6).

Sign convention: `fit_power_law` returns the RAW regression slope as
`exponent` -- positive for growth (value ~ N^exponent), negative for decay
(value ~ N^exponent with exponent<0, equivalently N^-|exponent|). Callers
map this to the contract's own gamma/eta/delta symbols, which are already
each defined with their own sign in the observable modules' docstrings
(laplacian_gap.py: "lambda_1(N) ~ N^-gamma" -> gamma = -exponent;
ipr.py: "IPR(N) ~ N^-eta" -> eta = -exponent; delta (G3, growth) =
+exponent directly). Keeping the regression itself sign-agnostic avoids
baking a growth/decay assumption into the one function shared by all
three gates.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats


@dataclass(frozen=True)
class PowerLawFit:
    """value ~ amplitude * N^exponent, from a log-log linear regression."""

    exponent: float
    exponent_ci_95: tuple[float, float]
    r_squared: float
    amplitude: float


@dataclass(frozen=True)
class LogarithmicFit:
    """value ~ slope * ln(N) + intercept -- the small-world alternative
    model G3's gate must be shown to lose against (mathematical_contract.md
    Sec falsification_gates G3 row: 'model comparison, not just a slope
    was fit')."""

    slope: float
    intercept: float
    r_squared: float


def fit_power_law(sizes: NDArray[np.floating], values: NDArray[np.floating]) -> PowerLawFit:
    """Log-log linear regression: ln(value) = exponent*ln(N) + ln(amplitude)."""
    log_sizes = np.log(sizes)
    log_values = np.log(values)
    regression = stats.linregress(log_sizes, log_values)
    exponent = float(regression.slope)
    r_squared = float(regression.rvalue) ** 2
    n_points = len(sizes)
    t_critical = float(stats.t.ppf(0.975, df=n_points - 2))
    margin = t_critical * float(regression.stderr)
    ci_95 = (exponent - margin, exponent + margin)
    amplitude = float(np.exp(regression.intercept))
    return PowerLawFit(
        exponent=exponent, exponent_ci_95=ci_95, r_squared=r_squared, amplitude=amplitude
    )


def fit_logarithmic(sizes: NDArray[np.floating], values: NDArray[np.floating]) -> LogarithmicFit:
    """Linear regression of value against ln(N) directly (not log-log) --
    the small-world-diameter alternative model, y = a*ln(N) + b."""
    log_sizes = np.log(sizes)
    regression = stats.linregress(log_sizes, values)
    r_squared = float(regression.rvalue) ** 2
    return LogarithmicFit(
        slope=float(regression.slope), intercept=float(regression.intercept), r_squared=r_squared
    )


def power_law_beats_logarithmic(power_fit: PowerLawFit, log_fit: LogarithmicFit) -> bool:
    """G3's model-comparison criterion (`[A23]`, assumptions.md): the
    power-law model is preferred over the logarithmic (small-world)
    alternative iff it clears the contract's own R^2>=0.9 bar AND its R^2
    strictly exceeds the logarithmic fit's R^2 on the same data."""
    return power_fit.r_squared >= 0.9 and power_fit.r_squared > log_fit.r_squared


@dataclass(frozen=True)
class SizeEstimate:
    """One (arm, N) cell's aggregate estimate of a metric -- mean and 95%
    CI across independent seeds (statistics.py), tagged with the graph
    size it was measured at."""

    size: int
    mean: float
    ci_95: tuple[float, float]


def check_finite_size_convergence(estimates: list[SizeEstimate]) -> bool:
    """G1's plateau-convergence criterion (falsification_gates.md): the
    largest-N estimate must fall within the second-largest-N's 95% CI --
    convergence, not monotonic drift. Order of `estimates` does not
    matter; the two largest sizes are found by sorting on `.size`."""
    if len(estimates) < 2:
        raise ValueError("need at least two distinct sizes to check convergence")
    sorted_estimates = sorted(estimates, key=lambda estimate: estimate.size)
    largest = sorted_estimates[-1]
    second_largest = sorted_estimates[-2]
    lower, upper = second_largest.ci_95
    return lower <= largest.mean <= upper
