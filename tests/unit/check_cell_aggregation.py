"""Unit tests for per-(arm,N) cell statistics aggregation
(mathematical_contract.md Sec7)."""

from pathlib import Path

import numpy as np

from boyko_benchmark.config import Arm, ExperimentConfig
from boyko_benchmark.experiment.cell_aggregation import (
    CellObservableStatistics,
    aggregate_cell,
)
from boyko_benchmark.experiment.gate_a_observables import compute_gate_a_observables
from boyko_benchmark.experiment.sweep import run_sweep

CONFIGS_DIR = Path(__file__).resolve().parents[2] / "configs"
_T_VALUES = np.array([0.5, 1.0, 2.0])
_Q = 0.9


def test_aggregate_cell_matches_manually_computed_mean_for_frozen_arm() -> None:
    """Real correctness check: aggregate_cell's reported mean must match
    directly averaging the same two replicates' observables computed by
    hand (i.e. by calling compute_gate_a_observables ourselves), not just
    "some statistics object came back"."""
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")
    sweep = run_sweep(config)
    replicates = sweep.replicates_by_size[27]
    assert len(replicates) == 2

    manual_g2_samples = []
    for replicate in replicates:
        arm_result = replicate.arm_results[Arm.FROZEN]
        observables = compute_gate_a_observables(
            arm_result, is_l_driven=False, t_values=_T_VALUES, q=_Q
        )
        manual_g2_samples.append(observables.g2_laplacian_gap)

    stats = aggregate_cell(
        replicates, Arm.FROZEN, dt=config.fast_dynamics.dt, t_values=_T_VALUES, q=_Q
    )

    assert isinstance(stats, CellObservableStatistics)
    assert stats.g2.seed_count == 2
    assert abs(stats.g2.mean - (sum(manual_g2_samples) / 2)) < 1e-12
    assert stats.g2.raw_samples == tuple(manual_g2_samples)


def test_aggregate_cell_produces_all_five_observable_statistics() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")
    sweep = run_sweep(config)
    replicates = sweep.replicates_by_size[27]

    stats = aggregate_cell(
        replicates,
        Arm.CLASSICAL_DIFFUSION_CONTROL,
        dt=config.fast_dynamics.dt,
        t_values=_T_VALUES,
        q=_Q,
    )

    for cell_stat in (stats.g1, stats.g2, stats.g3, stats.g4, stats.g5_v_eff):
        assert cell_stat.seed_count == 2
        assert len(cell_stat.raw_samples) == 2
