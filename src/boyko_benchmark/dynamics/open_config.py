"""Phase 11 pilot config schema (ТЗ §21's proposed file layout). Mirrors
`config.py`'s pydantic-validation style for the closed-system pipeline,
scoped to the open-system pilot's own parameters -- does not replace or
extend `config.py` directly.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class OpenDynamicsSection(BaseModel):
    """Dissipation/noise pilot grid (ТЗ §9). `gamma_tilde_levels` and
    `sigma_tilde_levels` are DIMENSIONLESS (`[A33]`: normalized by
    `omega_ref=2`) -- 0.0 is always implicitly included as the closed
    baseline, so these lists should contain only the NONZERO levels
    (ТЗ §9: "no more than 2-3 nonzero levels ... forbidden wide parameter
    fishing"). `omega_ref` is provisional (`[A33]`) -- overridable per
    config for a future recalibration without touching the default."""

    gamma_tilde_levels: list[float] = Field(default_factory=list)
    sigma_tilde_levels: list[float] = Field(default_factory=list)
    omega_ref: float = Field(default=2.0, gt=0)

    def gamma_values(self) -> list[float]:
        return [g * self.omega_ref for g in self.gamma_tilde_levels]


class OpenPilotSection(BaseModel):
    """Fast/slow dynamics budget for the open pilot -- separate from
    `config.py`'s `AdaptationSection`/`FastDynamicsSection` since Phase
    11 is its own scope, not a closed-system config extension."""

    dt: float = Field(gt=0)
    k: int = Field(gt=0)
    dtau_steps: int = Field(gt=0)
    eta: float = Field(gt=0)


class OpenPilotConfig(BaseModel):
    """Top-level Phase 11 pilot config object, one instance per
    `configs/open_pilot*.yaml` file."""

    sizes: list[int]
    seeds_per_cell: int = Field(gt=0)
    open_dynamics: OpenDynamicsSection
    pilot: OpenPilotSection

    @classmethod
    def from_yaml(cls, path: Path) -> OpenPilotConfig:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
