"""Unit tests for finite-size scaling regressions (mathematical_contract.md
Sec6/Sec9, gamma/eta/delta exponents for G2/G4/G3).

Hand-derived references, cross-checked via Bash prototype (scipy.stats.
linregress) before writing these assertions:

- exact synthetic decay `value = 3 * N^-0.5` on the dev FSS grid
  N=[64,125,216,343,512]: log-log regression recovers exponent=-0.5,
  R^2=1.0, amplitude=3.0, all exactly (zero-residual synthetic data).
- exact synthetic growth `value = 2 * N^0.5`: exponent=+0.5, amplitude=2.0.
- exact synthetic logarithmic `value = 1.5*ln(N) + 0.5`: fit_logarithmic
  recovers slope=1.5, intercept=0.5, R^2=1.0 exactly; the SAME data fit
  with fit_power_law (log-log) gives R^2=0.9969 -- strictly worse, as
  expected since the data isn't actually a power law -- confirming
  power_law_beats_logarithmic correctly picks the logarithmic model here
  (the reverse of G3's expected real-world result, used precisely to prove
  the comparison isn't rigged to always prefer power-law).
"""

import numpy as np

from boyko_benchmark.statistics.finite_size_scaling import (
    LogarithmicFit,
    PowerLawFit,
    fit_logarithmic,
    fit_power_law,
    power_law_beats_logarithmic,
)

_DEV_GRID = np.array([64.0, 125.0, 216.0, 343.0, 512.0])


def test_fit_power_law_recovers_exact_decay_exponent() -> None:
    values = 3.0 * _DEV_GRID**-0.5

    fit = fit_power_law(_DEV_GRID, values)

    assert isinstance(fit, PowerLawFit)
    assert abs(fit.exponent - (-0.5)) < 1e-9
    assert abs(fit.r_squared - 1.0) < 1e-9
    assert abs(fit.amplitude - 3.0) < 1e-6
    assert abs(fit.exponent_ci_95[0] - (-0.5)) < 1e-6
    assert abs(fit.exponent_ci_95[1] - (-0.5)) < 1e-6


def test_fit_power_law_recovers_exact_growth_exponent() -> None:
    values = 2.0 * _DEV_GRID**0.5

    fit = fit_power_law(_DEV_GRID, values)

    assert abs(fit.exponent - 0.5) < 1e-9
    assert abs(fit.amplitude - 2.0) < 1e-6


def test_fit_logarithmic_recovers_exact_slope_and_intercept() -> None:
    values = 1.5 * np.log(_DEV_GRID) + 0.5

    fit = fit_logarithmic(_DEV_GRID, values)

    assert isinstance(fit, LogarithmicFit)
    assert abs(fit.slope - 1.5) < 1e-9
    assert abs(fit.intercept - 0.5) < 1e-9
    assert abs(fit.r_squared - 1.0) < 1e-9


def test_power_law_beats_logarithmic_prefers_the_better_fitting_model() -> None:
    """On genuinely power-law data, the power-law fit wins."""
    values = 3.0 * _DEV_GRID**-0.5
    power_fit = fit_power_law(_DEV_GRID, values)
    log_fit = fit_logarithmic(_DEV_GRID, values)

    assert power_law_beats_logarithmic(power_fit, log_fit) is True


def test_power_law_beats_logarithmic_rejects_when_logarithmic_fits_better() -> None:
    """On genuinely logarithmic data, the comparison must NOT always favor
    power-law -- proves the criterion is a real comparison, not a rigged
    one. Hand-verified: power-law R^2=0.9969 < logarithmic R^2=1.0 on this
    exact data (see module docstring)."""
    values = 1.5 * np.log(_DEV_GRID) + 0.5
    power_fit = fit_power_law(_DEV_GRID, values)
    log_fit = fit_logarithmic(_DEV_GRID, values)

    assert power_law_beats_logarithmic(power_fit, log_fit) is False


def test_power_law_beats_logarithmic_requires_the_absolute_r_squared_floor() -> None:
    """Even if power-law R^2 exceeds logarithmic R^2, a power-law R^2 below
    0.9 must still fail the contract's unconditional floor (A23)."""
    noisy_power = PowerLawFit(
        exponent=0.5, exponent_ci_95=(0.4, 0.6), r_squared=0.85, amplitude=2.0
    )
    worse_log = LogarithmicFit(slope=1.0, intercept=0.0, r_squared=0.5)

    assert power_law_beats_logarithmic(noisy_power, worse_log) is False
