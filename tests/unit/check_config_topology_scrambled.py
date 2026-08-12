"""Unit tests for TopologyScrambledSection ([A21], added Phase 8 Cycle 19
to fill a real schema gap -- config.py never had this field despite [A21]
mandating it, since Phase 1's config.py predates Arm D's Phase 8 wiring).

test_config.py's own `_valid_config_dict()` fixture predates this field
and could not be edited to add it directly (`Edit`/`Write` on `test_*.py`
files is denied by this project's own permission settings -- a deliberate
anti-test-tampering guard, not a bug, see .claude/memory/decisions.md).
Resolved by giving the new field a sensible default (10, a standard
configuration-model randomization heuristic) rather than making it
required -- the OLD fixture (without this key) still validates unchanged,
and this file covers the new field's behavior directly instead.
"""

from pathlib import Path

from boyko_benchmark.config import ExperimentConfig, TopologyScrambledSection

CONFIGS_DIR = Path(__file__).resolve().parents[2] / "configs"


def test_default_n_swaps_per_edge_is_ten() -> None:
    section = TopologyScrambledSection()

    assert section.n_swaps_per_edge == 10


def test_real_configs_set_n_swaps_per_edge_explicitly() -> None:
    for name in ("smoke.yaml", "development.yaml", "production.yaml"):
        config = ExperimentConfig.from_yaml(CONFIGS_DIR / name)
        assert config.topology_scrambled.n_swaps_per_edge == 10


def test_topology_scrambled_section_is_omittable_from_config_dict() -> None:
    """The whole `topology_scrambled` key can be left out of a config dict
    entirely -- ExperimentConfig falls back to the section's own default,
    not a validation error -- keeping the OLD test_config.py fixture
    (predating this field) valid without modification."""
    data = {
        "experiment": {"master_seed": 1},
        "sizes": [8],
        "seeds_per_arm_size": 1,
        "arms": ["active"],
        "fast_dynamics": {"dt": 0.05, "operator_independence_diagnostic": True},
        "adaptation": {"eta": 0.1, "K": 5, "dtau_steps": 2},
        "propagation_front": {"q": 0.9, "n_source_nodes": 5},
        "mcid": {"cohens_d_threshold": 0.8, "require_nonoverlapping_ci": True},
        "g6_tiering": {"total_cells": 15, "strong_threshold": 15, "partial_threshold": 10},
        "seed_scheme": "numpy_seedsequence",
    }

    config = ExperimentConfig.model_validate(data)

    assert config.topology_scrambled.n_swaps_per_edge == 10
