"""`V5-K1'-Exposure` (`docs/v5_spec.md` Sec13.4): aggregates per-seed
checkpoint results into a per-checkpoint dose-response `ΔR(B)` curve and
the frozen PASS/FAIL verdict at the primary (largest-window) checkpoint.

Reuses `statistics/cell_statistics.py`'s `mcid_gate` directly for the
`|Cohen's d| >= 0.8` + non-overlapping-95%-CI check -- the same MCID
this project has used since `estimand.md` `[A10]`, not reimplemented
here."""

from dataclasses import dataclass
from typing import Literal

import numpy as np

from boyko_benchmark.experiment.k1_prime_exposure_gate import K1PrimeExposureSeedResult
from boyko_benchmark.statistics.cell_statistics import (
    CellStatistics,
    cohens_d,
    compute_cell_statistics,
    mcid_gate,
)


@dataclass(frozen=True)
class CheckpointVerdict:
    window_count: int
    stats_a3: CellStatistics
    stats_a4: CellStatistics
    cohens_d: float
    delta_r_mean: float
    seeds_a3_beats_a4: int
    n_seeds: int
    majority_a3_beats_a4: bool
    mcid_pass: bool


@dataclass(frozen=True)
class K1PrimeExposureVerdict:
    checkpoints: tuple[CheckpointVerdict, ...]
    status: Literal["PASS", "FAIL"]


def _checkpoint_window_counts(result: K1PrimeExposureSeedResult) -> tuple[int, ...]:
    return tuple(cp.window_count for cp in result.arm_a3.checkpoints)


def aggregate_k1_prime_exposure_results(
    results: list[K1PrimeExposureSeedResult],
) -> K1PrimeExposureVerdict:
    """`docs/v5_spec.md` Sec13.4: status is decided ONLY at the primary
    checkpoint (the largest, frozen window count, `B=D`) -- every
    checkpoint is still aggregated and reported (Sec13.2's dose-response
    curve requirement), never silently dropped."""
    if not results:
        raise ValueError("aggregate_k1_prime_exposure_results: results must be non-empty.")
    expected_windows = _checkpoint_window_counts(results[0])
    for result in results:
        if _checkpoint_window_counts(result) != expected_windows:
            raise ValueError(
                f"aggregate_k1_prime_exposure_results: seed {result.seed_index} has "
                f"checkpoint windows {_checkpoint_window_counts(result)}, expected "
                f"{expected_windows} -- all seeds in one campaign must share the same "
                f"frozen checkpoint schedule."
            )
        if tuple(cp.window_count for cp in result.arm_a4.checkpoints) != expected_windows:
            raise ValueError(
                f"aggregate_k1_prime_exposure_results: seed {result.seed_index}'s A4 arm "
                f"checkpoint windows do not match its A3 arm."
            )

    checkpoints: list[CheckpointVerdict] = []
    for i, window_count in enumerate(expected_windows):
        samples_a3 = np.array([r.arm_a3.checkpoints[i].r_edge for r in results])
        samples_a4 = np.array([r.arm_a4.checkpoints[i].r_edge for r in results])
        stats_a3 = compute_cell_statistics(samples_a3)
        stats_a4 = compute_cell_statistics(samples_a4)
        n_seeds = len(results)
        wins = int(np.sum(samples_a3 > samples_a4))
        checkpoints.append(
            CheckpointVerdict(
                window_count=window_count,
                stats_a3=stats_a3,
                stats_a4=stats_a4,
                cohens_d=cohens_d(samples_a3, samples_a4),
                delta_r_mean=stats_a3.mean - stats_a4.mean,
                seeds_a3_beats_a4=wins,
                n_seeds=n_seeds,
                majority_a3_beats_a4=wins > n_seeds / 2,
                mcid_pass=mcid_gate(samples_a3, samples_a4),
            )
        )

    primary = checkpoints[-1]
    status: Literal["PASS", "FAIL"] = (
        "PASS"
        if (primary.delta_r_mean > 0 and primary.mcid_pass and primary.majority_a3_beats_a4)
        else "FAIL"
    )
    return K1PrimeExposureVerdict(checkpoints=tuple(checkpoints), status=status)
