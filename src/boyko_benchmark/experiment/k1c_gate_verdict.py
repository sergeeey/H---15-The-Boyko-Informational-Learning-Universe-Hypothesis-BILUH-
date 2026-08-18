"""V4-K1c (`docs/v4_spec.md` Sec7d): aggregates per-seed K1c results
into ICE-1 (exposure)/ICE-2 (connectivity)/ICE-3 (cap activity) plus the
PASS/FAIL/INVALID verdict. INVALID (substrate/design problem, ICE gates
fail) is explicitly distinct from FAIL (substrate valid, `A3` did not
beat `A4`) -- never conflated, per the same Substrate-Gate discipline
`[A57]` already applied once to the original K1.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np

from boyko_benchmark.experiment.k1c_damage_gate import K1cArmResult, K1cSeedResult
from boyko_benchmark.statistics.cell_statistics import (
    CellStatistics,
    cohens_d,
    compute_cell_statistics,
)

EXPOSURE_THRESHOLD = 0.95
"""docs/v4_spec.md Sec7d ICE-1: below this, the cap is starving the
intended pruning rate by more than the tolerance allows."""

DISCONNECTION_RATE_THRESHOLD = 0.20
"""docs/v4_spec.md Sec3/Sec7d ICE-2: unchanged from the original K1."""


@dataclass(frozen=True)
class K1cVerdict:
    status: Literal["PASS", "FAIL", "INVALID"]
    reason: str
    exposure_ratio: float
    disconnection_rate: float
    f_cap: float
    max_node_prune_ever: int
    stats_a3: CellStatistics | None
    stats_a4: CellStatistics | None
    cohens_d: float | None


def _exposure_ratio(arms: list[K1cArmResult], m: int) -> float:
    pruned_total = 0
    target_total = 0
    for arm in arms:
        for diag in arm.diagnostics:
            if diag.window_index < m - 1:
                continue
            pruned_total += diag.n_pruned
            target_total += diag.n_target
    return pruned_total / target_total if target_total > 0 else 0.0


def _disconnection_rate(arms: list[K1cArmResult]) -> float:
    n_truncated = sum(1 for arm in arms if arm.truncated_at_window is not None)
    return n_truncated / len(arms) if arms else 0.0


def _cap_activity(arms: list[K1cArmResult]) -> float:
    eligible_total = 0
    rejected_total = 0
    for arm in arms:
        for diag in arm.diagnostics:
            eligible_total += diag.n_eligible
            rejected_total += diag.n_eligible - diag.n_pruned
    return rejected_total / eligible_total if eligible_total > 0 else 0.0


def _max_node_prune_ever(arms: list[K1cArmResult]) -> int:
    return max(
        (diag.max_node_prune for arm in arms for diag in arm.diagnostics),
        default=0,
    )


def aggregate_k1c_results(results: list[K1cSeedResult], m: int) -> K1cVerdict:
    all_arms = [r.arm_a3 for r in results] + [r.arm_a4 for r in results]

    exposure_ratio = _exposure_ratio(all_arms, m)
    disconnection_rate = _disconnection_rate(all_arms)
    f_cap = _cap_activity(all_arms)
    max_node_prune_ever = _max_node_prune_ever(all_arms)

    if exposure_ratio < EXPOSURE_THRESHOLD:
        return K1cVerdict(
            status="INVALID",
            reason=(
                f"ICE-1 exposure {exposure_ratio:.3f} < {EXPOSURE_THRESHOLD} -- "
                "the cap is starving the intended pruning rate"
            ),
            exposure_ratio=exposure_ratio,
            disconnection_rate=disconnection_rate,
            f_cap=f_cap,
            max_node_prune_ever=max_node_prune_ever,
            stats_a3=None,
            stats_a4=None,
            cohens_d=None,
        )

    if disconnection_rate > DISCONNECTION_RATE_THRESHOLD:
        return K1cVerdict(
            status="INVALID",
            reason=(
                f"ICE-2 disconnection rate {disconnection_rate:.3f} > "
                f"{DISCONNECTION_RATE_THRESHOLD} -- substrate still invalid under the cap"
            ),
            exposure_ratio=exposure_ratio,
            disconnection_rate=disconnection_rate,
            f_cap=f_cap,
            max_node_prune_ever=max_node_prune_ever,
            stats_a3=None,
            stats_a4=None,
            cohens_d=None,
        )

    samples_a3 = np.array([r.arm_a3.r_edge for r in results])
    samples_a4 = np.array([r.arm_a4.r_edge for r in results])
    stats_a3 = compute_cell_statistics(samples_a3)
    stats_a4 = compute_cell_statistics(samples_a4)
    effect_size = cohens_d(samples_a3, samples_a4)
    passed = stats_a3.mean > stats_a4.mean

    return K1cVerdict(
        status="PASS" if passed else "FAIL",
        reason="R_edge(A3) > R_edge(A4)" if passed else "R_edge(A3) did not beat R_edge(A4)",
        exposure_ratio=exposure_ratio,
        disconnection_rate=disconnection_rate,
        f_cap=f_cap,
        max_node_prune_ever=max_node_prune_ever,
        stats_a3=stats_a3,
        stats_a4=stats_a4,
        cohens_d=effect_size,
    )
