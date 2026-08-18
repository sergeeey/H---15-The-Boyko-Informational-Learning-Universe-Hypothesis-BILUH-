"""V5-K1' (`docs/v5_spec.md` Sec7): aggregates per-seed results into
the `K_skip` diagnostic and the PASS/FAIL verdict. No INVALID status --
unlike V4's K1/K1c/K1d, V5 has no analogous substrate-feasibility risk
(§7: connectivity is enforced by construction, and exposure has no
eligibility bottleneck comparable to persistence-gated pruning), so a
bare PASS/FAIL is the full verdict space here.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np

from boyko_benchmark.experiment.k1_prime_damage_gate import K1PrimeArmResult, K1PrimeSeedResult
from boyko_benchmark.statistics.cell_statistics import (
    CellStatistics,
    cohens_d,
    compute_cell_statistics,
)

K_SKIP_WARN_THRESHOLD = 0.20
"""`docs/v5_spec.md` Sec7: above this, `R_edge` is flagged [WEAK], not
silently trusted -- mirrors, without claiming to be identical to,
V4's own ICE-1 threshold philosophy."""


@dataclass(frozen=True)
class K1PrimeVerdict:
    status: Literal["PASS", "FAIL"]
    k_skip_rate: float
    weak_flag: bool
    stats_a3: CellStatistics
    stats_a4: CellStatistics
    cohens_d: float


def _k_skip_rate(arms: list[K1PrimeArmResult]) -> float:
    total_committed = sum(arm.total_committed for arm in arms)
    total_skipped = sum(arm.total_skipped for arm in arms)
    total = total_committed + total_skipped
    return total_skipped / total if total > 0 else 0.0


def aggregate_k1_prime_results(results: list[K1PrimeSeedResult]) -> K1PrimeVerdict:
    all_arms = [r.arm_a3 for r in results] + [r.arm_a4 for r in results]
    k_skip_rate = _k_skip_rate(all_arms)

    samples_a3 = np.array([r.arm_a3.r_edge for r in results])
    samples_a4 = np.array([r.arm_a4.r_edge for r in results])
    stats_a3 = compute_cell_statistics(samples_a3)
    stats_a4 = compute_cell_statistics(samples_a4)
    effect_size = cohens_d(samples_a3, samples_a4)

    return K1PrimeVerdict(
        status="PASS" if stats_a3.mean > stats_a4.mean else "FAIL",
        k_skip_rate=k_skip_rate,
        weak_flag=k_skip_rate > K_SKIP_WARN_THRESHOLD,
        stats_a3=stats_a3,
        stats_a4=stats_a4,
        cohens_d=effect_size,
    )
