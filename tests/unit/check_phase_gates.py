"""Unit tests for the Gate-A verdict machine (falsification_gates.md).

Includes the MANDATORY Oracle Adequacy checks the doc itself requires
before any real-arm verdict can be trusted: single-arm positive/negative
synthetic controls for G1-G5, and three paired-arm synthetic G6-tiering
cases with known-correct tiers. A gate implementation that misclassifies
any of these is documented as ORACLE_INADEQUATE by falsification_gates.md
-- these tests exist to catch exactly that, not just "the code runs."

All synthetic values verified via Bash prototype before writing
assertions (same discipline as every other observable/statistics module
this session):
- G2/G4 positive control: gap/IPR ~ 3*N^-0.5 on N=[64,125,216,343,512] ->
  exponent=-0.5 exactly, R^2=1.0, gamma/eta=0.5>0 -> PASS.
- G2/G4 negative control: near-flat values (tiny noise) -> R^2=0.057,
  well below the 0.9 floor -> FAIL (the R^2 condition catches it even
  though the fitted exponent happens to be nominally positive).
- G3 positive control: resistance ~ N^0.5 (growth) -- reuses Phase 7's
  own exact power-law fixture. G3 negative control: exact logarithmic
  data `1.5*ln(N)+0.5` -- reuses Phase 7's own exact logarithmic fixture,
  where power_law_beats_logarithmic already verified False.
- G5 positive control: exact linear r_q(t)=2t+1 -> v_eff=2.0, R^2=1.0.
  G5 negative control: flat r_q(t)=2 (frozen front) -> v_eff=0.0 exactly
  (R^2 comes back NaN for zero-variance data -- `>= 0.9` on NaN is
  correctly False in Python, no crash, no special-casing needed).
"""

import numpy as np

from boyko_benchmark.observables.propagation_front import fit_effective_velocity
from boyko_benchmark.phase_gates import (
    G6Tier,
    GateStatus,
    StageOneVerdict,
    compute_verdict,
    evaluate_g1,
    evaluate_g2,
    evaluate_g3,
    evaluate_g4,
    evaluate_g5,
    evaluate_g6,
)
from boyko_benchmark.statistics.finite_size_scaling import SizeEstimate

_SIZES = np.array([64.0, 125.0, 216.0, 343.0, 512.0])


def _make_samples(mean: float, std: float, n: int) -> np.ndarray:
    """Deterministic n-sample array with an exact mean and (ddof=1) std --
    no RNG, fully reproducible."""
    offsets = np.linspace(-1.0, 1.0, n)
    offsets = offsets - offsets.mean()
    offsets = offsets / np.std(offsets, ddof=1) * std
    return mean + offsets


# ---------------------------------------------------------------------
# Oracle Adequacy: single-arm G1-G5 positive/negative synthetic controls
# ---------------------------------------------------------------------


def test_g1_oracle_positive_control_converges() -> None:
    estimates = [
        SizeEstimate(size=216, mean=2.0, ci_95=(1.8, 2.2)),
        SizeEstimate(size=512, mean=2.05, ci_95=(1.9, 2.2)),
    ]

    result = evaluate_g1(estimates)

    assert result.status == GateStatus.PASS


def test_g1_oracle_negative_control_diverges() -> None:
    estimates = [
        SizeEstimate(size=216, mean=2.0, ci_95=(1.8, 2.2)),
        SizeEstimate(size=512, mean=5.0, ci_95=(4.8, 5.2)),
    ]

    result = evaluate_g1(estimates)

    assert result.status == GateStatus.FAIL


def test_g2_oracle_positive_control_passes() -> None:
    gap_values = 3.0 * _SIZES**-0.5

    result = evaluate_g2(_SIZES, gap_values)

    assert result.status == GateStatus.PASS
    assert abs(result.exponent_used - 0.5) < 1e-6


def test_g2_oracle_negative_control_fails() -> None:
    gap_values = np.full(5, 1.0) + np.array([0.001, -0.001, 0.0005, -0.0003, 0.0002])

    result = evaluate_g2(_SIZES, gap_values)

    assert result.status == GateStatus.FAIL
    assert result.fit.r_squared < 0.9


def test_g3_oracle_positive_control_passes() -> None:
    resistance_values = 2.0 * _SIZES**0.5

    result = evaluate_g3(_SIZES, resistance_values)

    assert result.status == GateStatus.PASS
    assert abs(result.delta - 0.5) < 1e-6


def test_g3_oracle_negative_control_fails() -> None:
    """Exact logarithmic (small-world) data -- power law cannot beat it."""
    resistance_values = 1.5 * np.log(_SIZES) + 0.5

    result = evaluate_g3(_SIZES, resistance_values)

    assert result.status == GateStatus.FAIL


def test_g4_oracle_positive_control_passes() -> None:
    ipr_values = 3.0 * _SIZES**-0.5

    result = evaluate_g4(_SIZES, ipr_values)

    assert result.status == GateStatus.PASS
    assert abs(result.exponent_used - 0.5) < 1e-6


def test_g4_oracle_negative_control_fails() -> None:
    ipr_values = np.full(5, 0.5) + np.array([0.001, -0.001, 0.0005, -0.0003, 0.0002])

    result = evaluate_g4(_SIZES, ipr_values)

    assert result.status == GateStatus.FAIL


def test_g5_oracle_positive_control_passes() -> None:
    times = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    radii = 2.0 * times + 1.0
    fit = fit_effective_velocity(times, radii, fit_window=(0, 5))

    result = evaluate_g5(fit)

    assert result.status == GateStatus.PASS


def test_g5_oracle_negative_control_fails() -> None:
    """Frozen front (v_eff=0) -- zero-variance data, R^2 comes back NaN;
    the v_eff>0 condition alone must correctly reject this, no crash."""
    times = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    radii = np.array([2.0, 2.0, 2.0, 2.0, 2.0])
    fit = fit_effective_velocity(times, radii, fit_window=(0, 5))

    result = evaluate_g5(fit)

    assert result.status == GateStatus.FAIL


# ---------------------------------------------------------------------
# Oracle Adequacy: paired-arm G6 tiering synthetic cases (known tiers)
# ---------------------------------------------------------------------

_OBSERVABLES = ["g1", "g2", "g3", "g4", "g5"]
_COMPARATORS = ["frozen", "random", "scrambled"]


def test_g6_oracle_all_cells_clear_gives_strong() -> None:
    cells = {
        (obs, comp): (_make_samples(0.0, 1.0, 10), _make_samples(-2.0, 1.0, 10))
        for obs in _OBSERVABLES
        for comp in _COMPARATORS
    }

    result = evaluate_g6(cells)

    assert result.n_cleared == 15
    assert result.tier == G6Tier.STRONG


def test_g6_oracle_twelve_of_fifteen_gives_partial() -> None:
    """4 of 5 observables clear on all 3 comparators (12 cells); the 5th
    observable fails on all 3 comparators (3 cells) -> 12/15 -> PARTIAL."""
    cells = {}
    for obs in _OBSERVABLES:
        for comp in _COMPARATORS:
            if obs == "g5":
                cells[(obs, comp)] = (_make_samples(0.0, 1.0, 10), _make_samples(-0.1, 1.0, 10))
            else:
                cells[(obs, comp)] = (_make_samples(0.0, 1.0, 10), _make_samples(-2.0, 1.0, 10))

    result = evaluate_g6(cells)

    assert result.n_cleared == 12
    assert result.tier == G6Tier.PARTIAL


def test_g6_oracle_five_of_fifteen_gives_fail() -> None:
    """d~2.0 on 1 comparator for all 5 observables (5 cells clear); d~0.3
    on the other 2 comparators for all 5 observables each (10 cells fail)
    -> 5/15 -> FAIL (falsification_gates.md's own third oracle row)."""
    cells = {}
    for obs in _OBSERVABLES:
        for i, comp in enumerate(_COMPARATORS):
            mean_diff = -2.0 if i == 0 else -0.3
            cells[(obs, comp)] = (_make_samples(0.0, 1.0, 10), _make_samples(mean_diff, 1.0, 10))

    result = evaluate_g6(cells)

    assert result.n_cleared == 5
    assert result.tier == G6Tier.FAIL


# ---------------------------------------------------------------------
# Verdict machine wiring
# ---------------------------------------------------------------------


def _all_pass_g1_to_g5():
    g1 = evaluate_g1(
        [
            SizeEstimate(size=216, mean=2.0, ci_95=(1.8, 2.2)),
            SizeEstimate(size=512, mean=2.05, ci_95=(1.9, 2.2)),
        ]
    )
    g2 = evaluate_g2(_SIZES, 3.0 * _SIZES**-0.5)
    g3 = evaluate_g3(_SIZES, 2.0 * _SIZES**0.5)
    g4 = evaluate_g4(_SIZES, 3.0 * _SIZES**-0.5)
    times = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    g5 = evaluate_g5(fit_effective_velocity(times, 2.0 * times + 1.0, fit_window=(0, 5)))
    return g1, g2, g3, g4, g5


def test_verdict_is_survives_when_all_pass_and_g6_strong() -> None:
    g1, g2, g3, g4, g5 = _all_pass_g1_to_g5()
    g6 = evaluate_g6(
        {
            (obs, comp): (_make_samples(0.0, 1.0, 10), _make_samples(-2.0, 1.0, 10))
            for obs in _OBSERVABLES
            for comp in _COMPARATORS
        }
    )

    verdict = compute_verdict(g1, g2, g3, g4, g5, g6)

    assert verdict == StageOneVerdict.SURVIVES


def test_verdict_is_survives_partial_when_all_pass_and_g6_partial() -> None:
    g1, g2, g3, g4, g5 = _all_pass_g1_to_g5()
    cells = {}
    for obs in _OBSERVABLES:
        for comp in _COMPARATORS:
            mean_diff = -0.1 if obs == "g5" else -2.0
            cells[(obs, comp)] = (_make_samples(0.0, 1.0, 10), _make_samples(mean_diff, 1.0, 10))
    g6 = evaluate_g6(cells)

    verdict = compute_verdict(g1, g2, g3, g4, g5, g6)

    assert verdict == StageOneVerdict.SURVIVES_PARTIAL


def test_verdict_is_fails_when_g6_strong_but_g2_fails() -> None:
    g1, _, g3, g4, g5 = _all_pass_g1_to_g5()
    g2_failing = evaluate_g2(_SIZES, np.full(5, 1.0))  # flat -> fails
    g6 = evaluate_g6(
        {
            (obs, comp): (_make_samples(0.0, 1.0, 10), _make_samples(-2.0, 1.0, 10))
            for obs in _OBSERVABLES
            for comp in _COMPARATORS
        }
    )

    verdict = compute_verdict(g1, g2_failing, g3, g4, g5, g6)

    assert verdict == StageOneVerdict.FAILS


def test_verdict_is_fails_when_all_g1_to_g5_pass_but_g6_fail_tier() -> None:
    g1, g2, g3, g4, g5 = _all_pass_g1_to_g5()
    cells = {}
    for obs in _OBSERVABLES:
        for i, comp in enumerate(_COMPARATORS):
            mean_diff = -2.0 if i == 0 else -0.3
            cells[(obs, comp)] = (_make_samples(0.0, 1.0, 10), _make_samples(mean_diff, 1.0, 10))
    g6 = evaluate_g6(cells)

    verdict = compute_verdict(g1, g2, g3, g4, g5, g6)

    assert verdict == StageOneVerdict.FAILS
