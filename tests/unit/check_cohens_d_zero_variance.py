"""Regression for a ZeroDivisionError found 2026-08-13: `cohens_d`
(statistics/cell_statistics.py) divides by `pooled_std` unconditionally.
`pooled_std=0` is a legal degenerate input -- both samples are internally
constant (zero within-group variance) -- and surfaced for real once G5's
`v_eff` started using an auto-detected unsaturated window
(detect_unsaturated_window): the narrower window can make a linear fit
deterministic enough that multiple seeds land on the exact same slope.

Standard convention (not invented here -- e.g. `effectsize` packages in R
and `pingouin` in Python special-case this): when pooled_std is exactly
zero, the effect size is well-defined only in the limiting sense --
identical constant samples have NO effect (d=0), differing constant
samples have a COMPLETE/perfect effect (d=+-inf, they are perfectly
separated by any threshold). Returning inf (not raising) also keeps
`mcid_gate`'s `abs(effect_size) >= 0.8` mathematically consistent: a
perfectly-separated pair should trivially clear any finite MCID threshold.
"""

import math

import numpy as np

from boyko_benchmark.statistics.cell_statistics import cohens_d, mcid_gate


def test_cohens_d_is_zero_for_identical_constant_samples() -> None:
    """Both samples equal to the same constant: no variance, no mean
    difference -- zero effect, not a division-by-zero crash."""
    sample_a = np.array([2.0, 2.0, 2.0])
    sample_b = np.array([2.0, 2.0, 2.0])

    assert cohens_d(sample_a, sample_b) == 0.0


def test_cohens_d_is_signed_infinity_for_differing_constant_samples() -> None:
    """Both samples individually constant but at different values: zero
    pooled variance with a nonzero mean difference is a perfectly
    separated (complete-effect) pair, not an error."""
    sample_a = np.array([2.0, 2.0, 2.0])
    sample_b = np.array([5.0, 5.0, 5.0])

    d = cohens_d(sample_a, sample_b)

    assert math.isinf(d)
    assert d < 0  # mean_a - mean_b = 2 - 5 = -3, negative direction


def test_mcid_gate_does_not_crash_on_zero_variance_constant_samples() -> None:
    sample_active = np.array([2.0, 2.0, 2.0])
    sample_control = np.array([5.0, 5.0, 5.0])

    # Degenerate zero-CI-width samples never truly overlap when means
    # differ, so the non-overlap half of the AND gate is trivially True;
    # combined with the infinite effect size, the gate must pass.
    assert mcid_gate(sample_active, sample_control) is True
