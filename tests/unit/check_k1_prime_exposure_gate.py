"""`V5-K1'-Exposure` (`docs/v5_spec.md` Sec13): checkpoint dose-response
gate -- ONE continuous run per arm/seed, recording `R_edge` and cumulative
committed/skipped swap counts at several frozen window counts, not three
separately-restarted runs (Sec13.1's own stated reason: avoids assuming
"first N windows of a longer run" == "a standalone N-window run" without
verifying it). Structural/invariant tests only -- exact `R_edge` values
depend on real correlation-driven swap selection on a real lattice, not
hand-derivable by inspection, same discipline as `check_k1_prime_damage_
gate.py`."""

from boyko_benchmark.experiment.k1_prime_exposure_gate import run_k1_prime_exposure_gate_one_seed


def test_checkpoints_are_recorded_at_the_requested_window_counts_in_order() -> None:
    result = run_k1_prime_exposure_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        n_swaps=2,
        checkpoint_windows=(2, 3),
        eta=0.1,
        dt=0.05,
        k=5,
        seed_index=0,
    )

    assert [cp.window_count for cp in result.arm_a3.checkpoints] == [2, 3]
    assert [cp.window_count for cp in result.arm_a4.checkpoints] == [2, 3]


def test_r_edge_values_are_valid_fractions_at_every_checkpoint() -> None:
    result = run_k1_prime_exposure_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        n_swaps=2,
        checkpoint_windows=(1, 2, 3),
        eta=0.1,
        dt=0.05,
        k=5,
        seed_index=1,
    )

    for arm in (result.arm_a3, result.arm_a4):
        for checkpoint in arm.checkpoints:
            assert 0.0 <= checkpoint.r_edge <= 1.0
            assert 0.0 <= checkpoint.wrong_removal_rate <= 1.0


def test_cumulative_committed_plus_skipped_matches_budget_at_final_checkpoint() -> None:
    result = run_k1_prime_exposure_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        n_swaps=2,
        checkpoint_windows=(2, 3),
        eta=0.1,
        dt=0.05,
        k=5,
        seed_index=2,
    )

    total_budget = 2 * 3  # n_swaps * final checkpoint's window count
    for arm in (result.arm_a3, result.arm_a4):
        final = arm.checkpoints[-1]
        assert final.cumulative_committed + final.cumulative_skipped == total_budget
        assert final.cumulative_committed > 0


def test_cumulative_counts_are_non_decreasing_across_checkpoints() -> None:
    result = run_k1_prime_exposure_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        n_swaps=2,
        checkpoint_windows=(1, 2, 3),
        eta=0.1,
        dt=0.05,
        k=5,
        seed_index=3,
    )

    for arm in (result.arm_a3, result.arm_a4):
        committed = [cp.cumulative_committed for cp in arm.checkpoints]
        skipped = [cp.cumulative_skipped for cp in arm.checkpoints]
        assert committed == sorted(committed)
        assert skipped == sorted(skipped)


def test_both_arms_share_the_identical_damaged_graph() -> None:
    result = run_k1_prime_exposure_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        n_swaps=2,
        checkpoint_windows=(2,),
        eta=0.1,
        dt=0.05,
        k=5,
        seed_index=4,
    )

    assert len(result.damaged_out) > 0
