"""V5-K1' (`docs/v5_spec.md` Sec7): aggregation logic, hand-derived
fixtures constructed directly (no simulation)."""

import pytest

from boyko_benchmark.experiment.k1_prime_damage_gate import K1PrimeArmResult, K1PrimeSeedResult
from boyko_benchmark.experiment.k1_prime_gate_verdict import aggregate_k1_prime_results


def _arm(r_edge: float, committed: int, skipped: int) -> K1PrimeArmResult:
    return K1PrimeArmResult(
        r_edge=r_edge, wrong_removal_rate=0.0, total_committed=committed, total_skipped=skipped
    )


def test_pass_when_a3_beats_a4() -> None:
    results = [
        K1PrimeSeedResult(
            seed_index=i,
            damaged_out=frozenset({(0, 1)}),
            arm_a3=_arm(0.8, 30, 0),
            arm_a4=_arm(0.3, 30, 0),
        )
        for i in range(3)
    ]

    verdict = aggregate_k1_prime_results(results)

    assert verdict.status == "PASS"
    assert verdict.stats_a3.mean == pytest.approx(0.8)
    assert verdict.stats_a4.mean == pytest.approx(0.3)
    assert verdict.cohens_d > 0
    assert verdict.k_skip_rate == 0.0
    assert verdict.weak_flag is False


def test_fail_when_a3_does_not_beat_a4() -> None:
    results = [
        K1PrimeSeedResult(
            seed_index=i,
            damaged_out=frozenset({(0, 1)}),
            arm_a3=_arm(0.2, 30, 0),
            arm_a4=_arm(0.6, 30, 0),
        )
        for i in range(3)
    ]

    verdict = aggregate_k1_prime_results(results)

    assert verdict.status == "FAIL"
    assert verdict.cohens_d < 0


def test_k_skip_rate_hand_derived() -> None:
    # 2 seeds, identical arms each: A3 committed 24/skipped 6 (25% skip),
    # A4 committed 27/skipped 3 (10% skip). Pooled across both seeds:
    # skipped=(6+3)*2=18, total=(30+30)*2=120 -> rate=0.15
    results = [
        K1PrimeSeedResult(
            seed_index=i,
            damaged_out=frozenset({(0, 1)}),
            arm_a3=_arm(0.5, 24, 6),
            arm_a4=_arm(0.4, 27, 3),
        )
        for i in range(2)
    ]

    verdict = aggregate_k1_prime_results(results)

    assert verdict.k_skip_rate == 0.15
    assert verdict.weak_flag is False


def test_weak_flag_set_above_threshold() -> None:
    results = [
        K1PrimeSeedResult(
            seed_index=i,
            damaged_out=frozenset({(0, 1)}),
            arm_a3=_arm(0.5, 5, 5),  # 50% skip
            arm_a4=_arm(0.4, 5, 5),  # 50% skip
        )
        for i in range(2)
    ]

    verdict = aggregate_k1_prime_results(results)

    assert verdict.k_skip_rate == 0.5
    assert verdict.weak_flag is True
