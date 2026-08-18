"""M2 (`docs/v4_spec.md` Sec7/Sec8): aggregates per-seed K1 results into
the gate's PASS/FAIL verdict. Reuses `statistics/cell_statistics.py`
(`compute_cell_statistics`, `cohens_d`) rather than reimplementing --
same project-wide requirement (raw samples, mean, std, 95% CI, effect
size) every other cell/metric already follows.

PASS condition is the bare inequality `docs/v4_spec.md` Sec7 states
(`R_edge(A3) > R_edge(A4)` on the aggregate mean) -- NOT an MCID gate.
K1 is deliberately cheap and easy to fail; Cohen's d and CI are reported
for transparency, not as an additional pass requirement.
"""

from dataclasses import dataclass

import numpy as np

from boyko_benchmark.experiment.k1_damage_gate import K1SeedResult
from boyko_benchmark.statistics.cell_statistics import (
    CellStatistics,
    cohens_d,
    compute_cell_statistics,
)


@dataclass(frozen=True)
class K1GateVerdict:
    passed: bool
    stats_a3: CellStatistics
    stats_a4: CellStatistics
    cohens_d: float


def aggregate_k1_results(results: list[K1SeedResult]) -> K1GateVerdict:
    samples_a3 = np.array([r.r_edge_a3 for r in results])
    samples_a4 = np.array([r.r_edge_a4 for r in results])

    stats_a3 = compute_cell_statistics(samples_a3)
    stats_a4 = compute_cell_statistics(samples_a4)
    effect_size = cohens_d(samples_a3, samples_a4)

    return K1GateVerdict(
        passed=bool(stats_a3.mean > stats_a4.mean),
        stats_a3=stats_a3,
        stats_a4=stats_a4,
        cohens_d=effect_size,
    )
