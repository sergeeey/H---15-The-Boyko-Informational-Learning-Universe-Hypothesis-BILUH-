"""Typed, validated configuration objects over configs/*.yaml.

Parses the raw YAML written in Stage B into pydantic models, so a
malformed or internally inconsistent config fails fast at load time
instead of surfacing as a confusing downstream error mid-experiment.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, Field, model_validator


class Arm(StrEnum):
    """The seven experimental arms (mathematical_contract.md §4)."""

    ACTIVE = "active"
    FROZEN = "frozen"
    PARAMETER_MATCHED_RANDOM = "parameter_matched_random"
    TOPOLOGY_SCRAMBLED = "topology_scrambled"
    FIXED_FLAT_GEOMETRY = "fixed_flat_geometry"
    ALTERNATIVE_OBJECTIVE = "alternative_objective"
    CLASSICAL_DIFFUSION_CONTROL = "classical_diffusion_control"


class ExperimentSection(BaseModel):
    master_seed: int


class FastDynamicsSection(BaseModel):
    dt: float = Field(gt=0)
    operator_independence_diagnostic: bool


class AdaptationSection(BaseModel):
    eta: float = Field(gt=0)
    K: int = Field(gt=0)
    dtau_steps: int = Field(gt=0)


class PropagationFrontSection(BaseModel):
    q: float = Field(gt=0, lt=1)
    n_source_nodes: int = Field(gt=0)


class TopologyScrambledSection(BaseModel):
    """[A21]: n_swaps has no fixed default -- a raw swap COUNT would not
    scale correctly across the FSS grid (larger graphs need proportionally
    more swaps for the same randomization). `n_swaps_per_edge` is a
    multiplier instead: actual n_swaps = n_swaps_per_edge * n_edges(N),
    computed per-size by the orchestrator. This multiplier itself DOES get
    a default (10, a commonly-cited configuration-model randomization
    heuristic -- ~10 swaps per edge for near-complete randomization) --
    unlike a raw count, the multiplier is scale-invariant across N by
    construction, so A21's original "no default" concern does not apply to
    it; every real config still sets it explicitly for clarity."""

    n_swaps_per_edge: int = Field(default=10, gt=0)


class MCIDSection(BaseModel):
    """MCID = estimand.md's fixed threshold: |Cohen's d| >= this AND
    non-overlapping 95% CIs, both required."""

    cohens_d_threshold: float = Field(gt=0)
    require_nonoverlapping_ci: bool


class G6TieringSection(BaseModel):
    """falsification_gates.md's G6 Tiering: STRONG (15/15) / PARTIAL
    (>=10/15, pre-registered) / FAIL. Thresholds must be internally
    consistent -- partial_threshold <= strong_threshold <= total_cells."""

    total_cells: int = Field(gt=0)
    strong_threshold: int = Field(gt=0)
    partial_threshold: int = Field(gt=0)

    @model_validator(mode="after")
    def _thresholds_are_consistent(self) -> Self:
        if self.strong_threshold > self.total_cells:
            raise ValueError(
                f"strong_threshold ({self.strong_threshold}) must not exceed "
                f"total_cells ({self.total_cells})"
            )
        if self.partial_threshold > self.strong_threshold:
            raise ValueError(
                f"partial_threshold ({self.partial_threshold}) must not exceed "
                f"strong_threshold ({self.strong_threshold})"
            )
        return self


class ExperimentConfig(BaseModel):
    """Top-level config object, one instance per configs/*.yaml file."""

    experiment: ExperimentSection
    sizes: list[int]
    seeds_per_arm_size: int = Field(gt=0)
    arms: list[Arm]
    fast_dynamics: FastDynamicsSection
    adaptation: AdaptationSection
    propagation_front: PropagationFrontSection
    topology_scrambled: TopologyScrambledSection = Field(default_factory=TopologyScrambledSection)
    mcid: MCIDSection
    g6_tiering: G6TieringSection
    seed_scheme: str

    @classmethod
    def from_yaml(cls, path: Path) -> ExperimentConfig:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
