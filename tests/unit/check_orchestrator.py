"""Unit tests for the per-replicate orchestrator (mathematical_contract.md
Sec4, Sec6 FSS grid unit).

Hand-derived reference: n_edges_for_mean_degree(8, mean_degree=6) =
8*6//2 = 24 exactly ([A7]: mean degree matched to Arm E's cubic lattice,
2*3=6 neighbors per node); n_edges_for_mean_degree(27) = 81.
round(27**(1/3))=3 -- verified via Bash prototype, exact cube, no
floating-point rounding risk.

N=27 (not N=8) is used for the end-to-end smoke-config tests below --
[A7]'s mean-degree-6 target makes N=8 an 85.7%-dense (near-complete)
Erdos-Renyi graph, where Arm D's degree-preserving rewiring is
combinatorially near-infeasible (found this session: even a single
requested swap succeeds only ~52% of the time on the actual graph,
essentially never for nswap>=8). This is exactly why smoke.yaml's own
`sizes` was changed from [8, 27] to [27, 64] -- see decisions.md and
graphs/rewiring.py's `_MAX_RETRY_ATTEMPTS` docstring for the full
investigation. n_edges_for_mean_degree(8) is still tested directly below
since the FORMULA itself is correct and reusable; it's specifically
COMBINING N=8 with Arm D's rewiring that is infeasible, not the edge-count
arithmetic.
"""

from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from boyko_benchmark.config import Arm, ExperimentConfig
from boyko_benchmark.experiment.orchestrator import (
    ReplicateResult,
    n_edges_for_mean_degree,
    run_replicate,
)

CONFIGS_DIR = Path(__file__).resolve().parents[2] / "configs"


def test_n_edges_for_mean_degree_matches_hand_derived_value() -> None:
    assert n_edges_for_mean_degree(8) == 24
    assert n_edges_for_mean_degree(27) == 81


def test_run_replicate_on_smoke_config_produces_all_seven_arms_and_oi_diagnostic() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")

    result = run_replicate(config, n_nodes=27, seed_index=0)

    assert isinstance(result, ReplicateResult)
    assert result.n_nodes == 27
    assert result.seed_index == 0
    assert set(result.arm_results.keys()) == set(Arm)
    assert result.operator_independence_result is not None


def test_run_replicate_is_deterministic_for_the_same_inputs() -> None:
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")

    result_1 = run_replicate(config, n_nodes=27, seed_index=0)
    result_2 = run_replicate(config, n_nodes=27, seed_index=0)

    for arm in Arm:
        np.testing.assert_array_equal(
            result_1.arm_results[arm].dynamics_result.final_graph.weights,
            result_2.arm_results[arm].dynamics_result.final_graph.weights,
        )


def test_run_replicate_differs_across_seed_indices() -> None:
    """A different seed_index must produce a genuinely different Active
    run -- otherwise seed derivation isn't actually varying anything."""
    config = ExperimentConfig.from_yaml(CONFIGS_DIR / "smoke.yaml")

    result_seed_0 = run_replicate(config, n_nodes=27, seed_index=0)
    result_seed_1 = run_replicate(config, n_nodes=27, seed_index=1)

    assert not np.allclose(
        result_seed_0.arm_results[Arm.ACTIVE].dynamics_result.final_graph.weights,
        result_seed_1.arm_results[Arm.ACTIVE].dynamics_result.final_graph.weights,
    )


def test_topology_scrambled_without_active_raises() -> None:
    """Early-exit error path -- never reaches graph generation for Arm D,
    so N=8's density pathology (see module docstring) is irrelevant here."""
    data = {
        "experiment": {"master_seed": 1},
        "sizes": [8],
        "seeds_per_arm_size": 1,
        "arms": ["topology_scrambled"],
        "fast_dynamics": {"dt": 0.05, "operator_independence_diagnostic": False},
        "adaptation": {"eta": 0.1, "K": 3, "dtau_steps": 2},
        "propagation_front": {"q": 0.9, "n_source_nodes": 5},
        "mcid": {"cohens_d_threshold": 0.8, "require_nonoverlapping_ci": True},
        "g6_tiering": {"total_cells": 15, "strong_threshold": 15, "partial_threshold": 10},
        "seed_scheme": "numpy_seedsequence",
    }
    config = ExperimentConfig.model_validate(data)

    with pytest.raises(ValueError, match="requires Arm.ACTIVE"):
        run_replicate(config, n_nodes=8, seed_index=0)


def test_config_rejects_unknown_topology_scrambled_field_typo() -> None:
    """Sanity check that ValidationError (not ValueError) is what pydantic
    itself raises for a genuinely malformed config -- distinguishing this
    from run_replicate's own ValueError above."""
    data = {
        "experiment": {"master_seed": 1},
        "sizes": [8],
        "seeds_per_arm_size": 1,
        "arms": ["active"],
        "fast_dynamics": {"dt": 0.05, "operator_independence_diagnostic": False},
        "adaptation": {"eta": 0.1, "K": 3, "dtau_steps": 2},
        "propagation_front": {"q": 0.9, "n_source_nodes": 5},
        "mcid": {"cohens_d_threshold": 0.8, "require_nonoverlapping_ci": True},
        "g6_tiering": {"total_cells": 15, "strong_threshold": 15, "partial_threshold": -1},
        "seed_scheme": "numpy_seedsequence",
    }

    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(data)
