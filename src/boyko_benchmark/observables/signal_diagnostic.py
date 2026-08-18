"""`docs/v5_spec.md` Sec14: does C_ij alone discriminate genuinely-
damaged lattice edges from other non-edges, independent of any
structural (swap) operator -- H1 (signal problem) vs H2 (operator
problem) after `[A68]`'s FAIL. `Recall@D` and `AUPRC` (`average
precision`, sklearn's piecewise-constant definition, computed directly
since sklearn is not a project dependency) over the candidate universe
of currently-non-adjacent pairs, ranked by `C_ij` descending.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Edge = tuple[int, int]


@dataclass(frozen=True)
class SignalDiagnosticResult:
    recall_at_d: float
    auprc: float
    baseline_recall: float
    """Chance expectation of `Recall@D` under a uniformly random ranking:
    `D / n_candidates` (hypergeometric mean) -- exact by a simple
    argument (mean overlap of a random D-subset with the positive set)."""
    baseline_auprc: float
    """Chance expectation of `AUPRC` under a uniformly random ranking.
    Reviewer-caught error (2026-08-18, `docs/assumptions.md` [A69]
    addendum): this is NOT the same as `baseline_recall` despite the
    superficial resemblance (both "a ratio over D and M") -- confirmed
    by hand-derivation, brute-force enumeration on small cases, and a
    4000-trial Monte Carlo at real campaign scale. See
    `_expected_average_precision`'s docstring for the closed form."""
    d: int
    n_candidates: int


def _expected_average_precision(d: int, m: int) -> float:
    """Exact `E[AP]` under a uniformly random ranking of `m` items with
    `d` positives: `H_m/m + ((d-1)/(m(m-1)))*(m-H_m)`, `H_m` = the `m`-th
    harmonic number. Verified against brute-force enumeration over all
    distinct rankings for `(d,m)` up to `(3,5)` (exact match to floating-
    point precision) and against `signal_diagnostic.py`'s reviewer via an
    independent 4000-trial Monte Carlo at `d=146, m=129000` scale."""
    if m <= 1:
        raise ValueError(f"_expected_average_precision: m={m} must be > 1.")
    harmonic_m = float(np.sum(1.0 / np.arange(1, m + 1)))
    return harmonic_m / m + ((d - 1) / (m * (m - 1))) * (m - harmonic_m)


def compute_rank_metrics(
    scores: NDArray[np.floating], is_positive: NDArray[np.bool_]
) -> SignalDiagnosticResult:
    """Shared core: given per-candidate scores and positive labels, rank
    descending by score and compute `Recall@D` (`D=is_positive.sum()`),
    `AUPRC` (average precision), and their exact chance baselines.
    Extracted 2026-08-18 (`docs/v5_spec.md` Sec15) so `compute_signal_
    diagnostic` (exact edge recovery) and `compute_geometry_signal_audit`
    (nearest-neighbor classification) share ONE reviewer-verified
    implementation of this math, rather than risking a second
    independently-derived (and possibly independently-buggy, `[A69]`'s
    own correction) copy."""
    d = int(is_positive.sum())
    m = len(scores)
    if d == 0:
        raise ValueError("compute_rank_metrics: no positives -- nothing to rank.")
    if m <= 1:
        raise ValueError(f"compute_rank_metrics: only {m} candidate(s) -- need at least 2.")

    order = np.argsort(-scores, kind="stable")
    is_positive_sorted = is_positive[order]

    recall_at_d = float(is_positive_sorted[:d].sum()) / d

    cum_tp = np.cumsum(is_positive_sorted)
    ranks = np.arange(1, m + 1)
    precision_at_k = cum_tp / ranks
    auprc = float(np.sum(precision_at_k * is_positive_sorted)) / d

    return SignalDiagnosticResult(
        recall_at_d=recall_at_d,
        auprc=auprc,
        baseline_recall=d / m,
        baseline_auprc=_expected_average_precision(d, m),
        d=d,
        n_candidates=m,
    )


def compute_signal_diagnostic(
    mask: NDArray[np.bool_],
    c_ij: NDArray[np.floating],
    damaged_out: frozenset[Edge],
) -> SignalDiagnosticResult:
    """`damaged_out` must be non-empty -- mirrors `compute_edge_recovery`'s
    own contract (`observables/edge_recovery.py`). Candidate universe =
    every `(i,j)`, `i<j`, not currently adjacent in `mask`."""
    if not damaged_out:
        raise ValueError("compute_signal_diagnostic: damaged_out is empty -- nothing to rank.")

    n = mask.shape[0]
    rows, cols = np.triu_indices(n, k=1)
    is_non_edge = ~mask[rows, cols]
    cand_rows, cand_cols = rows[is_non_edge], cols[is_non_edge]
    if cand_rows.size <= 1:
        raise ValueError(
            f"compute_signal_diagnostic: only {cand_rows.size} candidate pair(s) -- "
            f"need at least 2 for a meaningful ranking/baseline."
        )
    scores = c_ij[cand_rows, cand_cols]
    is_positive = np.array(
        [(int(i), int(j)) in damaged_out for i, j in zip(cand_rows, cand_cols, strict=True)]
    )

    return compute_rank_metrics(scores, is_positive)
