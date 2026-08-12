"""Unit tests for the FSS sweep (mathematical_contract.md Sec6)."""

from pathlib import Path

from boyko_benchmark.config import Arm, ExperimentConfig
from boyko_benchmark.experiment.sweep import SweepResult, run_sweep

CONFIGS_DIR = Path(__file__).resolve().parents[2] / "configs"


def test_run_sweep_on_smoke_config_covers_every_size_and_seed() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")

    result = run_sweep(config)

    assert isinstance(result, SweepResult)
    assert set(result.replicates_by_size.keys()) == set(config.sizes)
    for n_nodes in config.sizes:
        replicates = result.replicates_by_size[n_nodes]
        assert len(replicates) == config.seeds_per_arm_size
        for seed_index, replicate in enumerate(replicates):
            assert replicate.n_nodes == n_nodes
            assert replicate.seed_index == seed_index
            assert set(replicate.arm_results.keys()) == set(Arm)
