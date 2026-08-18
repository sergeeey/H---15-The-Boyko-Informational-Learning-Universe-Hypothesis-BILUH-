"""M2 (`docs/v4_spec.md` Sec7/Sec8): aggregating K1SeedResults across
seeds into a PASS/FAIL verdict. `docs/v4_spec.md` Sec7's PASS condition
is a bare inequality on the aggregate (`R_edge(A3) > R_edge(A4)`), not
an MCID-gated claim -- K1 is deliberately a cheap, easy-to-fail gate, so
this reports full CellStatistics/Cohen's d (project-wide statistical
requirement) alongside the verdict, without requiring MCID separation
for PASS.
"""

import numpy as np

from boyko_benchmark.experiment.k1_damage_gate import K1SeedResult
from boyko_benchmark.experiment.k1_gate_verdict import aggregate_k1_results


def _make_result(seed_index: int, r_edge_a3: float, r_edge_a4: float) -> K1SeedResult:
    return K1SeedResult(
        seed_index=seed_index,
        r_edge_a3=r_edge_a3,
        r_edge_a4=r_edge_a4,
        wrong_removal_a3=0.0,
        wrong_removal_a4=0.0,
        damaged_out_a3=frozenset({(0, 1)}),
        damaged_out_a4=frozenset({(0, 1)}),
        truncated_at_window_a3=None,
        truncated_at_window_a4=None,
    )


def test_passes_when_a3_clearly_beats_a4() -> None:
    results = [
        _make_result(0, 0.80, 0.30),
        _make_result(1, 0.90, 0.40),
        _make_result(2, 0.70, 0.20),
        _make_result(3, 0.85, 0.35),
        _make_result(4, 0.75, 0.25),
    ]

    verdict = aggregate_k1_results(results)

    assert verdict.passed is True
    assert verdict.stats_a3.mean == 0.8
    assert verdict.stats_a4.mean == 0.3
    assert verdict.cohens_d > 0


def test_fails_when_a4_beats_or_ties_a3() -> None:
    results = [
        _make_result(0, 0.30, 0.80),
        _make_result(1, 0.40, 0.90),
        _make_result(2, 0.20, 0.70),
    ]

    verdict = aggregate_k1_results(results)

    assert verdict.passed is False
    assert verdict.cohens_d < 0


def test_raw_samples_are_preserved_per_seed() -> None:
    results = [_make_result(0, 0.5, 0.1), _make_result(1, 0.6, 0.2)]

    verdict = aggregate_k1_results(results)

    assert verdict.stats_a3.raw_samples == (0.5, 0.6)
    assert verdict.stats_a4.raw_samples == (0.1, 0.2)


def test_matches_hand_computed_cohens_d() -> None:
    a3 = np.array([0.80, 0.90, 0.70, 0.85, 0.75])
    a4 = np.array([0.30, 0.40, 0.20, 0.35, 0.25])
    results = [_make_result(i, float(a3[i]), float(a4[i])) for i in range(5)]

    verdict = aggregate_k1_results(results)

    # hand-derived: both samples have identical variance (a4 = a3 - 0.5),
    # so pooled_std = std(a3) = std(a4); d = (mean_a3-mean_a4)/pooled_std
    pooled_std = float(np.std(a3, ddof=1))
    expected_d = (float(np.mean(a3)) - float(np.mean(a4))) / pooled_std
    assert verdict.cohens_d == expected_d
