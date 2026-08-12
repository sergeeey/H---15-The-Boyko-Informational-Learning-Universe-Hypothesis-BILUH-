"""Unit tests for the top-level phase runner (Phase 10 Cycle 25)."""

from pathlib import Path

import numpy as np

from boyko_benchmark.config import ExperimentConfig
from boyko_benchmark.experiment.phase_runner import PhaseResult, run_phase
from boyko_benchmark.phase_gates import StageOneVerdict

CONFIGS_DIR = Path(__file__).resolve().parents[2] / "configs"
_T_VALUES = np.array([0.5, 1.0, 2.0])
_Q = 0.9


def test_run_phase_on_smoke_config_produces_a_complete_result() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")

    result = run_phase(config, t_values=_T_VALUES, q=_Q)

    assert isinstance(result, PhaseResult)
    assert result.verdict in set(StageOneVerdict)
    assert result.sizes == tuple(sorted(config.sizes))
    # this repo has had a real commit since 2026-08-12 -- git_commit_hash
    # is a real 40-char hash now, not the earlier UNKNOWN- fallback
    # (see check_provenance.py's docstring for the full explanation)
    assert len(result.provenance.git_commit_hash) == 40
    assert result.provenance.numpy_version


def test_run_phase_cell_statistics_cover_every_arm_and_size() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")

    result = run_phase(config, t_values=_T_VALUES, q=_Q)

    for n_nodes in config.sizes:
        for arm in config.arms:
            assert (arm, n_nodes) in result.cell_statistics
            stats = result.cell_statistics[(arm, n_nodes)]
            assert stats.g1.seed_count == config.seeds_per_arm_size


def test_run_phase_g6_result_has_fifteen_cells() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")

    result = run_phase(config, t_values=_T_VALUES, q=_Q)

    assert len(result.g6.cells) == 15


def test_run_phase_verdict_is_never_the_survives_string_without_all_gates_passing() -> None:
    """Never claim SURVIVES/SURVIVES_PARTIAL unless G1-G5 genuinely all
    passed -- a real safety check on the wiring, not the science (smoke
    data isn't expected to survive anything, per smoke.yaml's own
    disclaimer)."""
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")

    result = run_phase(config, t_values=_T_VALUES, q=_Q)

    all_pass = all(
        gate.status.value == "PASS"
        for gate in (result.g1, result.g2, result.g3, result.g4, result.g5)
    )
    if result.verdict in (StageOneVerdict.SURVIVES, StageOneVerdict.SURVIVES_PARTIAL):
        assert all_pass
    if not all_pass:
        assert result.verdict == StageOneVerdict.FAILS
