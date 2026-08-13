"""Per-(arm, N)-cell statistics and effect sizes (mathematical_contract.md
Sec7 / TZ.txt Sec11).

For every metric, every (arm, N) cell: mean, standard deviation, median,
95% CI, effect size (Cohen's d vs each negative-control arm), seed count,
raw per-seed samples (persisted, not just aggregates).

Independence rule (hard constraint, Sec7): `samples` here must be one
value per independent seed -- never multiple time points from a single
run. Enforcing that discipline is the caller's (experiment runner's)
responsibility; this module only aggregates whatever array it is given.
"""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats


@dataclass(frozen=True)
class CellStatistics:
    mean: float
    std: float
    median: float
    ci_95: tuple[float, float]
    seed_count: int
    raw_samples: tuple[float, ...]


def compute_cell_statistics(samples: NDArray[np.floating]) -> CellStatistics:
    """Everything mathematical_contract.md Sec7 requires recorded for one
    (arm, N, metric) cell. `std`/`ci_95` use the sample (ddof=1) standard
    deviation -- the standard unbiased estimator when the population
    variance is unknown, which it always is here (finite seed count)."""
    n_seeds = len(samples)
    mean = float(np.mean(samples))
    std = float(np.std(samples, ddof=1))
    median = float(np.median(samples))
    standard_error = std / np.sqrt(n_seeds)
    t_critical = float(stats.t.ppf(0.975, df=n_seeds - 1))
    margin = t_critical * standard_error
    ci_95 = (mean - margin, mean + margin)
    return CellStatistics(
        mean=mean,
        std=std,
        median=median,
        ci_95=ci_95,
        seed_count=n_seeds,
        raw_samples=tuple(float(x) for x in samples),
    )


def cohens_d(sample_a: NDArray[np.floating], sample_b: NDArray[np.floating]) -> float:
    """Standard pooled-standard-deviation Cohen's d:
    d = (mean_a - mean_b) / pooled_std,
    pooled_std = sqrt(((n_a-1)*var_a + (n_b-1)*var_b) / (n_a+n_b-2)).

    `pooled_std == 0` is a legal degenerate input (both samples internally
    constant, e.g. found 2026-08-13 once G5's v_eff started using an
    auto-detected unsaturated fit window narrow enough to make some
    replicate's fitted slope identical across seeds) -- not an error.
    Identical constants -> zero effect (d=0). Differing constants -> a
    perfectly separated pair, the limiting case of an arbitrarily large
    effect (d=+-inf, signed by the direction of the mean difference).
    """
    n_a, n_b = len(sample_a), len(sample_b)
    mean_a, mean_b = float(np.mean(sample_a)), float(np.mean(sample_b))
    var_a, var_b = float(np.var(sample_a, ddof=1)), float(np.var(sample_b, ddof=1))
    pooled_variance = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
    pooled_std = float(np.sqrt(pooled_variance))
    mean_diff = mean_a - mean_b
    if pooled_std == 0.0:
        return 0.0 if mean_diff == 0.0 else math.copysign(math.inf, mean_diff)
    return mean_diff / pooled_std


def mcid_gate(sample_active: NDArray[np.floating], sample_control: NDArray[np.floating]) -> bool:
    """The fixed MCID (`[A10]`, estimand.md): `|Cohen's d| >= 0.8` AND
    non-overlapping 95% CIs, both required."""
    effect_size = cohens_d(sample_active, sample_control)
    stats_active = compute_cell_statistics(sample_active)
    stats_control = compute_cell_statistics(sample_control)
    non_overlapping = (
        stats_active.ci_95[0] > stats_control.ci_95[1]
        or stats_control.ci_95[0] > stats_active.ci_95[1]
    )
    return bool(abs(effect_size) >= 0.8 and non_overlapping)
