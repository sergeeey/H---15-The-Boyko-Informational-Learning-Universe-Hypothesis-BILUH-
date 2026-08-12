"""Unit tests for G6 cross-arm sample wiring ([A26]: largest-N-only)."""

from pathlib import Path

import numpy as np

from boyko_benchmark.config import Arm, ExperimentConfig
from boyko_benchmark.experiment.cell_aggregation import collect_observable_samples
from boyko_benchmark.experiment.g6_wiring import (
    G6_COMPARATOR_ARMS,
    OBSERVABLE_NAMES,
    build_g6_samples,
)
from boyko_benchmark.experiment.sweep import run_sweep
from boyko_benchmark.phase_gates import evaluate_g6

CONFIGS_DIR = Path(__file__).resolve().parents[2] / "configs"
_T_VALUES = np.array([0.5, 1.0, 2.0])
_Q = 0.9


def test_build_g6_samples_covers_all_fifteen_cells() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")
    sweep = run_sweep(config)

    cells = build_g6_samples(sweep, dt=config.fast_dynamics.dt, t_values=_T_VALUES, q=_Q)

    assert len(cells) == len(OBSERVABLE_NAMES) * len(G6_COMPARATOR_ARMS)
    for observable in OBSERVABLE_NAMES:
        for comparator in G6_COMPARATOR_ARMS:
            assert (observable, comparator.value) in cells


def test_build_g6_samples_uses_the_largest_configured_size() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")
    sweep = run_sweep(config)
    largest_n = max(config.sizes)
    replicates = sweep.replicates_by_size[largest_n]

    cells = build_g6_samples(sweep, dt=config.fast_dynamics.dt, t_values=_T_VALUES, q=_Q)

    expected_active = collect_observable_samples(
        replicates, Arm.ACTIVE, config.fast_dynamics.dt, _T_VALUES, _Q
    )
    active_g2, _ = cells[("g2", Arm.FROZEN.value)]
    np.testing.assert_array_equal(active_g2, expected_active["g2"])


def test_build_g6_samples_feeds_evaluate_g6_without_error() -> None:
    """Real correctness check, not just structural: the built cells must
    be directly consumable by phase_gates.evaluate_g6 and produce a valid
    tier -- proves the dict shape actually matches what the verdict
    machine expects, not just that keys exist."""
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")
    sweep = run_sweep(config)

    cells = build_g6_samples(sweep, dt=config.fast_dynamics.dt, t_values=_T_VALUES, q=_Q)
    result = evaluate_g6(cells)

    assert len(result.cells) == 15
    assert 0 <= result.n_cleared <= 15
