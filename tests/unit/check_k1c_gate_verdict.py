"""V4-K1c (`docs/v4_spec.md` Sec7d): aggregation logic for the three
ICE gates + PASS/FAIL/INVALID verdict. Hand-derived fixtures constructed
directly (no simulation) to isolate the aggregation math from the
dynamics."""

from boyko_benchmark.experiment.k1c_damage_gate import K1cArmResult, K1cSeedResult, WindowDiagnostic
from boyko_benchmark.experiment.k1c_gate_verdict import aggregate_k1c_results


def _diag(window_index: int, n_target: int, n_eligible: int, n_pruned: int) -> WindowDiagnostic:
    return WindowDiagnostic(
        window_index=window_index,
        n_target=n_target,
        n_eligible=n_eligible,
        n_pruned=n_pruned,
        max_node_prune=0,
        max_node_regrow=0,
        max_degree_pre_window=6,
    )


def _arm(
    diagnostics: list[WindowDiagnostic], r_edge: float, truncated: int | None = None
) -> K1cArmResult:
    return K1cArmResult(
        r_edge=r_edge,
        wrong_removal_rate=0.0,
        truncated_at_window=truncated,
        diagnostics=tuple(diagnostics),
    )


def test_invalid_when_exposure_ratio_is_below_threshold() -> None:
    # m=2 -> exclude window_index < 1 (i.e. exclude window 0). Window 1:
    # pruned=3/target=10 per arm, aggregated over 1 seed x 2 arms = 6/20 = 0.3
    diags = [_diag(0, 10, 0, 0), _diag(1, 10, 5, 3)]
    result = K1cSeedResult(
        seed_index=0,
        damaged_out=frozenset({(0, 1)}),
        arm_a3=_arm(diags, r_edge=0.8),
        arm_a4=_arm(diags, r_edge=0.3),
    )

    verdict = aggregate_k1c_results([result], m=2)

    assert verdict.status == "INVALID"
    assert verdict.exposure_ratio == 0.3
    assert "ICE-1" in verdict.reason


def test_invalid_when_disconnection_rate_exceeds_threshold() -> None:
    # 2 seeds x 2 arms = 4 arm-runs; 2 truncated = 50% > 20% threshold.
    # Exposure kept high so ICE-1 doesn't trigger first.
    diags = [_diag(0, 10, 0, 0), _diag(1, 10, 10, 10)]
    results = [
        K1cSeedResult(
            seed_index=0,
            damaged_out=frozenset({(0, 1)}),
            arm_a3=_arm(diags, r_edge=0.8, truncated=1),
            arm_a4=_arm(diags, r_edge=0.3, truncated=1),
        ),
        K1cSeedResult(
            seed_index=1,
            damaged_out=frozenset({(0, 1)}),
            arm_a3=_arm(diags, r_edge=0.8),
            arm_a4=_arm(diags, r_edge=0.3),
        ),
    ]

    verdict = aggregate_k1c_results(results, m=2)

    assert verdict.status == "INVALID"
    assert verdict.disconnection_rate == 0.5
    assert "ICE-2" in verdict.reason


def test_pass_when_substrate_valid_and_a3_beats_a4() -> None:
    diags = [_diag(0, 10, 0, 0), _diag(1, 10, 10, 10)]
    results = [
        K1cSeedResult(
            seed_index=i,
            damaged_out=frozenset({(0, 1)}),
            arm_a3=_arm(diags, r_edge=0.8),
            arm_a4=_arm(diags, r_edge=0.3),
        )
        for i in range(2)
    ]

    verdict = aggregate_k1c_results(results, m=2)

    assert verdict.status == "PASS"
    assert verdict.exposure_ratio == 1.0
    assert verdict.disconnection_rate == 0.0
    assert verdict.stats_a3 is not None and verdict.stats_a3.mean == 0.8
    assert verdict.stats_a4 is not None and verdict.stats_a4.mean == 0.3
    assert verdict.cohens_d is not None and verdict.cohens_d > 0


def test_fail_when_substrate_valid_but_a3_does_not_beat_a4() -> None:
    diags = [_diag(0, 10, 0, 0), _diag(1, 10, 10, 10)]
    results = [
        K1cSeedResult(
            seed_index=i,
            damaged_out=frozenset({(0, 1)}),
            arm_a3=_arm(diags, r_edge=0.2),
            arm_a4=_arm(diags, r_edge=0.6),
        )
        for i in range(2)
    ]

    verdict = aggregate_k1c_results(results, m=2)

    assert verdict.status == "FAIL"
    assert verdict.cohens_d is not None and verdict.cohens_d < 0


def test_cap_activity_computed_from_eligible_minus_pruned() -> None:
    # window 1: eligible=10, pruned=6 -> 4 rejected, per arm; 2 arms -> 8/20 = 0.4
    diags = [_diag(0, 10, 0, 0), _diag(1, 10, 10, 6)]
    result = K1cSeedResult(
        seed_index=0,
        damaged_out=frozenset({(0, 1)}),
        arm_a3=_arm(diags, r_edge=0.8),
        arm_a4=_arm(diags, r_edge=0.3),
    )

    verdict = aggregate_k1c_results([result], m=1)

    assert verdict.f_cap == 0.4
