"""`V5-K1'-Exposure` (`docs/v5_spec.md` Sec13.4): aggregation logic,
hand-derived fixtures constructed directly (no simulation) -- pure
arithmetic over given `R_edge` arrays, same discipline as `check_k1_
prime_gate_verdict.py`."""

import pytest

from boyko_benchmark.experiment.k1_prime_exposure_gate import (
    K1PrimeExposureArmResult,
    K1PrimeExposureCheckpoint,
    K1PrimeExposureSeedResult,
)
from boyko_benchmark.experiment.k1_prime_exposure_verdict import aggregate_k1_prime_exposure_results

_WINDOWS = (10, 25, 49)


def _checkpoint(window_count: int, r_edge: float) -> K1PrimeExposureCheckpoint:
    return K1PrimeExposureCheckpoint(
        window_count=window_count,
        r_edge=r_edge,
        wrong_removal_rate=0.0,
        cumulative_committed=window_count * 3,
        cumulative_skipped=0,
    )


def _seed(
    seed_index: int, a3_r_edges: list[float], a4_r_edges: list[float]
) -> K1PrimeExposureSeedResult:
    assert len(a3_r_edges) == len(_WINDOWS) == len(a4_r_edges)
    return K1PrimeExposureSeedResult(
        seed_index=seed_index,
        damaged_out=frozenset({(0, 1)}),
        arm_a3=K1PrimeExposureArmResult(
            checkpoints=tuple(_checkpoint(w, r) for w, r in zip(_WINDOWS, a3_r_edges, strict=True))
        ),
        arm_a4=K1PrimeExposureArmResult(
            checkpoints=tuple(_checkpoint(w, r) for w, r in zip(_WINDOWS, a4_r_edges, strict=True))
        ),
    )


def test_primary_checkpoint_is_the_last_and_largest_window_count() -> None:
    results = [_seed(i, [0.1, 0.2, 0.3], [0.1, 0.2, 0.3]) for i in range(3)]

    verdict = aggregate_k1_prime_exposure_results(results)

    assert [cp.window_count for cp in verdict.checkpoints] == list(_WINDOWS)
    assert verdict.checkpoints[-1].window_count == max(_WINDOWS)


def test_pass_when_a3_clearly_beats_a4_with_majority_and_mcid() -> None:
    """Hand-derived (prototype-verified via direct arithmetic before
    writing this assertion): at the primary checkpoint (window=49),
    A3=[0.85,0.90,0.95,0.90] vs A4=[0.05,0.10,0.15,0.10] -- mean_diff=0.80,
    pooled_std=0.0408, d=19.6 (well above 0.8), CIs (0.835,0.965) vs
    (0.035,0.165) -- non-overlapping. 4/4 seeds show A3>A4."""
    results = [
        _seed(0, [0.0, 0.0, 0.85], [0.0, 0.0, 0.05]),
        _seed(1, [0.0, 0.0, 0.90], [0.0, 0.0, 0.10]),
        _seed(2, [0.0, 0.0, 0.95], [0.0, 0.0, 0.15]),
        _seed(3, [0.0, 0.0, 0.90], [0.0, 0.0, 0.10]),
    ]

    verdict = aggregate_k1_prime_exposure_results(results)

    primary = verdict.checkpoints[-1]
    assert primary.delta_r_mean == pytest.approx(0.80)
    assert primary.cohens_d > 0.8
    assert primary.mcid_pass is True
    assert primary.seeds_a3_beats_a4 == 4
    assert primary.majority_a3_beats_a4 is True
    assert verdict.status == "PASS"


def test_fail_when_effect_is_weak_and_concentrated_in_one_seed() -> None:
    """Hand-derived to reproduce `[A66]`'s own shape: A3=[0.02,0,0,0,0]
    vs A4=[0,0,0,0,0] at the primary checkpoint -- mean_diff=0.004,
    pooled_std=0.006325, d=0.6325 (< 0.8 MCID), and only 1/5 seeds show
    A3>A4 (not a majority) -- both conditions independently fail."""
    results = [
        _seed(0, [0.0, 0.0, 0.02], [0.0, 0.0, 0.0]),
        _seed(1, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        _seed(2, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        _seed(3, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        _seed(4, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
    ]

    verdict = aggregate_k1_prime_exposure_results(results)

    primary = verdict.checkpoints[-1]
    assert primary.delta_r_mean == pytest.approx(0.004)
    assert primary.cohens_d == pytest.approx(0.6325, abs=1e-3)
    assert primary.mcid_pass is False
    assert primary.seeds_a3_beats_a4 == 1
    assert primary.majority_a3_beats_a4 is False
    assert verdict.status == "FAIL"


def test_seeds_a3_beats_a4_count_is_computed_correctly() -> None:
    """Direct count check, independent of MCID passing: 3 of 4 seeds
    show A3>A4 at the primary checkpoint -> majority True (3 > 4/2)."""
    results = [
        _seed(0, [0.0, 0.0, 0.5], [0.0, 0.0, 0.1]),
        _seed(1, [0.0, 0.0, 0.5], [0.0, 0.0, 0.1]),
        _seed(2, [0.0, 0.0, 0.5], [0.0, 0.0, 0.1]),
        _seed(3, [0.0, 0.0, 0.1], [0.0, 0.0, 0.5]),
    ]

    verdict = aggregate_k1_prime_exposure_results(results)

    primary = verdict.checkpoints[-1]
    assert primary.seeds_a3_beats_a4 == 3
    assert primary.n_seeds == 4
    assert primary.majority_a3_beats_a4 is True


def test_all_checkpoints_are_reported_not_just_the_primary_one() -> None:
    results = [_seed(i, [0.1, 0.4, 0.9], [0.05, 0.1, 0.05]) for i in range(3)]

    verdict = aggregate_k1_prime_exposure_results(results)

    assert len(verdict.checkpoints) == 3
    deltas = [cp.delta_r_mean for cp in verdict.checkpoints]
    assert deltas == [pytest.approx(0.05), pytest.approx(0.3), pytest.approx(0.85)]


def test_raises_a_clear_error_on_empty_results() -> None:
    """Reviewer-flagged gap (2026-08-18): `results[0]` on an empty list
    previously raised a bare IndexError; now a clear ValueError, matching
    the mismatched-checkpoint-schedule error below."""
    with pytest.raises(ValueError, match="non-empty"):
        aggregate_k1_prime_exposure_results([])


def test_raises_on_mismatched_checkpoint_schedules_across_seeds() -> None:
    mismatched = K1PrimeExposureSeedResult(
        seed_index=1,
        damaged_out=frozenset({(0, 1)}),
        arm_a3=K1PrimeExposureArmResult(checkpoints=(_checkpoint(10, 0.1), _checkpoint(25, 0.2))),
        arm_a4=K1PrimeExposureArmResult(checkpoints=(_checkpoint(10, 0.1), _checkpoint(25, 0.2))),
    )
    results = [_seed(0, [0.1, 0.2, 0.3], [0.1, 0.2, 0.3]), mismatched]

    with pytest.raises(ValueError, match="checkpoint"):
        aggregate_k1_prime_exposure_results(results)
