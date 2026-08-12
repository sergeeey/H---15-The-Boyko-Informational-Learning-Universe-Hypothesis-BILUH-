"""Unit tests for ExperimentConfig (pydantic models over configs/*.yaml).

Two things are tested: (1) the real config files written in Stage B
actually parse into the expected typed values -- config.py and the YAML
files must stay in sync, and a round-trip test is what catches drift; (2)
a business-rule invariant (G6 tiering thresholds must be internally
consistent, falsification_gates.md's G6 Tiering) is enforced at load time,
not discovered later at verdict time.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from boyko_benchmark.config import Arm, ExperimentConfig

CONFIGS_DIR = Path(__file__).resolve().parents[2] / "configs"


def test_loads_smoke_config_with_expected_values() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")

    assert config.experiment.master_seed == 20260811
    assert config.sizes == [27, 64]
    assert config.seeds_per_arm_size == 2
    assert Arm.CLASSICAL_DIFFUSION_CONTROL in config.arms
    assert len(config.arms) == 7
    assert config.adaptation.K == 50
    assert config.mcid.cohens_d_threshold == 0.8
    assert config.g6_tiering.strong_threshold == 15
    assert config.g6_tiering.partial_threshold == 10


def test_loads_development_and_production_configs_without_error() -> None:
    """Not exhaustive per-field checks (smoke.yaml covers that) -- just
    confirms the other two real config files parse at all, so drift in any
    of the three is caught here, not at Phase-1-completion time."""
    ExperimentConfig.from_yaml(CONFIGS_DIR / "development.yaml")
    ExperimentConfig.from_yaml(CONFIGS_DIR / "production.yaml")


def _valid_config_dict() -> dict:
    return {
        "experiment": {"master_seed": 42},
        "sizes": [8, 27],
        "seeds_per_arm_size": 2,
        "arms": ["active", "frozen"],
        "fast_dynamics": {"dt": 0.05, "operator_independence_diagnostic": True},
        "adaptation": {"eta": 0.1, "K": 50, "dtau_steps": 5},
        "propagation_front": {"q": 0.9, "n_source_nodes": 5},
        "mcid": {"cohens_d_threshold": 0.8, "require_nonoverlapping_ci": True},
        "g6_tiering": {"total_cells": 15, "strong_threshold": 15, "partial_threshold": 10},
        "seed_scheme": "numpy_seedsequence",
    }


def test_rejects_unknown_arm_name() -> None:
    data = _valid_config_dict()
    data["arms"] = ["not_a_real_arm"]

    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(data)


def test_rejects_g6_tiering_where_strong_exceeds_total_cells() -> None:
    """falsification_gates.md's G6 Tiering: strong_threshold must never
    exceed total_cells (15) -- an inconsistent config would silently make
    G6_STRONG unreachable or ill-defined."""
    data = _valid_config_dict()
    data["g6_tiering"] = {"total_cells": 15, "strong_threshold": 20, "partial_threshold": 10}

    with pytest.raises(ValidationError, match="strong_threshold"):
        ExperimentConfig.model_validate(data)


def test_rejects_g6_tiering_where_partial_exceeds_strong() -> None:
    data = _valid_config_dict()
    data["g6_tiering"] = {"total_cells": 15, "strong_threshold": 10, "partial_threshold": 12}

    with pytest.raises(ValidationError, match="partial_threshold"):
        ExperimentConfig.model_validate(data)
