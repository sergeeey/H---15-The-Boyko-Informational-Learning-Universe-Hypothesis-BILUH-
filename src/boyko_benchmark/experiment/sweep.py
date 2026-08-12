"""Runs the full FSS grid (mathematical_contract.md Sec6): every
configured size x every configured seed index.

This is the layer above `orchestrator.run_replicate` -- one replicate is
the atomic unit; this module just calls it repeatedly and collects
results, nothing more. Observable computation and statistics aggregation
are separate, later stages (Phase 9 Cycles 21-22).
"""

from dataclasses import dataclass

from boyko_benchmark.config import ExperimentConfig
from boyko_benchmark.experiment.orchestrator import ReplicateResult, run_replicate


@dataclass(frozen=True)
class SweepResult:
    replicates_by_size: dict[int, tuple[ReplicateResult, ...]]


def run_sweep(config: ExperimentConfig) -> SweepResult:
    """One `run_replicate` call per `(size, seed_index)` pair in
    `config.sizes x range(config.seeds_per_arm_size)`."""
    replicates_by_size: dict[int, tuple[ReplicateResult, ...]] = {}
    for n_nodes in config.sizes:
        replicates = tuple(
            run_replicate(config, n_nodes, seed_index)
            for seed_index in range(config.seeds_per_arm_size)
        )
        replicates_by_size[n_nodes] = replicates
    return SweepResult(replicates_by_size=replicates_by_size)
