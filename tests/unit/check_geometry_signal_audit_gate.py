"""`docs/v5_spec.md` Sec15: wiring check for `run_geometry_signal_audit_
one_trial` -- small-scale (N=8 lattice), not the real N=512 campaign.
Confirms checkpoints land at the requested window counts and different
trial indices genuinely pick different source nodes (deterministically).
"""

from boyko_benchmark.experiment.geometry_signal_audit_gate import (
    run_geometry_signal_audit_one_trial,
)


def test_checkpoints_land_at_requested_windows() -> None:
    result = run_geometry_signal_audit_one_trial(
        side_length=2,  # N=8
        checkpoint_windows=(1, 3),
        eta=0.1,
        dt=0.05,
        k=5,
        trial_index=0,
        master_seed=11,
    )

    assert [cp.window_count for cp in result.checkpoints] == [1, 3]
    for cp in result.checkpoints:
        assert 0.0 <= cp.audit.auroc_nn <= 1.0
        assert -1.0 <= cp.audit.spearman_rho <= 1.0
        assert 0.0 <= cp.audit_magnitude.auroc_nn <= 1.0
        assert -1.0 <= cp.audit_magnitude.spearman_rho <= 1.0


def test_different_trials_use_different_deterministic_source_nodes() -> None:
    result_a = run_geometry_signal_audit_one_trial(
        side_length=2,
        checkpoint_windows=(1,),
        eta=0.1,
        dt=0.05,
        k=5,
        trial_index=0,
        master_seed=11,
    )
    result_b = run_geometry_signal_audit_one_trial(
        side_length=2,
        checkpoint_windows=(1,),
        eta=0.1,
        dt=0.05,
        k=5,
        trial_index=1,
        master_seed=11,
    )
    result_a_again = run_geometry_signal_audit_one_trial(
        side_length=2,
        checkpoint_windows=(1,),
        eta=0.1,
        dt=0.05,
        k=5,
        trial_index=0,
        master_seed=11,
    )

    assert result_a.source_node != result_b.source_node
    assert (
        result_a.source_node == result_a_again.source_node
    )  # deterministic given same trial_index
