"""Unit tests for per-(arm,N)-cell statistics and effect sizes
(mathematical_contract.md Sec7, [A10] MCID).

Hand-derived references, cross-checked via Bash prototype before writing
these assertions:

- a=[1,2,3,4,5]: mean=3, sample std (ddof=1)=sqrt(2.5)=1.58113883,
  median=3, 95% CI via t-distribution (df=4, t=2.7764451): margin=
  2.7764451*(1.58113883/sqrt(5))=1.96324316, CI=(1.03675684, 4.96324316).
- Cohen's d(a, b=[3,4,5,6,7]) = -1.26491106 (equal std groups, pooled_std
  = 1.58113883, mean diff = -2).
- Cohen's d(a, c=[10,11,12,13,14]) = -5.69209979 (large mean diff).
- MCID mixed case (n=100 per group, tiled base pattern, mean diff=0.5,
  std~1.09): |d|=0.457 (<0.8) but 95% CIs do NOT overlap
  (ci_a=(9.683,10.117), ci_b=(10.183,10.617)) -- proves the gate is a
  genuine AND, not satisfied by non-overlap alone.
"""

import numpy as np

from boyko_benchmark.statistics.cell_statistics import (
    CellStatistics,
    cohens_d,
    compute_cell_statistics,
    mcid_gate,
)

_SAMPLE_A = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
_SAMPLE_B = np.array([3.0, 4.0, 5.0, 6.0, 7.0])
_SAMPLE_C = np.array([10.0, 11.0, 12.0, 13.0, 14.0])


def test_compute_cell_statistics_matches_hand_derived_values() -> None:
    result = compute_cell_statistics(_SAMPLE_A)

    assert isinstance(result, CellStatistics)
    assert abs(result.mean - 3.0) < 1e-9
    assert abs(result.std - 1.58113883) < 1e-6
    assert abs(result.median - 3.0) < 1e-9
    assert result.seed_count == 5
    assert result.raw_samples == (1.0, 2.0, 3.0, 4.0, 5.0)
    assert abs(result.ci_95[0] - 1.03675684) < 1e-6
    assert abs(result.ci_95[1] - 4.96324316) < 1e-6


def test_cohens_d_matches_hand_derived_value_for_equal_variance_groups() -> None:
    d = cohens_d(_SAMPLE_A, _SAMPLE_B)

    assert abs(d - (-1.26491106)) < 1e-6


def test_cohens_d_matches_hand_derived_value_for_large_separation() -> None:
    d = cohens_d(_SAMPLE_A, _SAMPLE_C)

    assert abs(d - (-5.69209979)) < 1e-6


def test_cohens_d_is_zero_for_identical_samples() -> None:
    assert abs(cohens_d(_SAMPLE_A, _SAMPLE_A)) < 1e-12


def test_mcid_gate_passes_with_large_effect_and_nonoverlapping_ci() -> None:
    assert mcid_gate(_SAMPLE_A, _SAMPLE_C) is True


def test_mcid_gate_fails_when_effect_is_large_but_cis_overlap() -> None:
    """d(a,b)=-1.26 clears the 0.8 threshold, but a's CI (1.04,4.96) and
    b's CI (3.04,6.96) (same std, mean shifted by 2) overlap -- MCID
    requires BOTH conditions, not effect size alone."""
    assert abs(cohens_d(_SAMPLE_A, _SAMPLE_B)) >= 0.8
    assert mcid_gate(_SAMPLE_A, _SAMPLE_B) is False


def test_mcid_gate_fails_when_cis_separate_but_effect_is_small() -> None:
    """Large-n case: mean difference of 0.5 against std~1.09 gives
    |d|~0.457 (below 0.8) even though the large sample size (n=100/group)
    narrows the CIs enough to be non-overlapping -- statistically
    significant but not practically meaningful, exactly the case MCID
    exists to reject."""
    base = np.array([-1.5, -1.1, -0.7, -0.3, 0.1, 0.5, 0.9, 1.3, -1.7, 1.5])
    sample_active = np.tile(10.0 + base, 10)
    sample_control = np.tile(10.5 + base, 10)

    assert abs(cohens_d(sample_active, sample_control)) < 0.8
    assert mcid_gate(sample_active, sample_control) is False
