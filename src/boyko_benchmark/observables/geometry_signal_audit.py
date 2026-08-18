"""`docs/v5_spec.md` Sec15: the Geometry Signal Audit -- after `[A69]`
found C_ij does not encode EXACT damaged-edge identity (H1), does it
encode COARSE geometric locality instead (distance, neighborhood)? A
narrower, upstream question than `[A69]`'s: does `psi -> C_ij` produce
ANY detectable geometric signal at all, on the UNDAMAGED positive-
control lattice, decoupled entirely from damage/restoration.

Four levels, all computed over the SAME `(C_ij, ground-truth distance)`
pair for every `(i,j)`, `i<j` (the full N*(N-1)/2 pairs, not just
non-edges -- unlike `signal_diagnostic.py`'s recovery framing, here the
positive class (`d*=1`, nearest-neighbor) IS mostly existing edges,
which is exactly the point):
1. Nearest-neighbor discrimination: AUROC (Mann-Whitney U, `scipy.
   stats.mannwhitneyu`) + `Recall@D`/`AUPRC` (reusing `signal_
   diagnostic.py`'s reviewer-verified `compute_rank_metrics`).
2. Spearman rank correlation `rho(C_ij, -d*)` (`scipy.stats.spearmanr`)
   -- positive rho = higher correlation for closer pairs.
3. Distance shells: mean `C_ij` per hop-distance value.
4. Top-D distance distribution: among the top-`D` (`D`=count of true
   nearest-neighbor pairs) candidates ranked by `C_ij`, what fraction
   land at each true distance -- `P(d*=r | top-D)`.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.stats import mannwhitneyu, spearmanr

from boyko_benchmark.observables.signal_diagnostic import (
    SignalDiagnosticResult,
    compute_rank_metrics,
)


@dataclass(frozen=True)
class DistanceShellStats:
    distance: int
    mean_c: float
    n_pairs: int


@dataclass(frozen=True)
class GeometrySignalAuditResult:
    auroc_nn: float
    rank_metrics_nn: SignalDiagnosticResult
    spearman_rho: float
    spearman_pvalue: float
    distance_shells: tuple[DistanceShellStats, ...]
    top_d_distance_fractions: dict[int, float]
    """`P(d*=r | top-D)` for every distance value `r` present -- cumulative
    sum over increasing `r` gives `P(d*<=r | top-D)`."""


def compute_geometry_signal_audit(
    distances: NDArray[np.int64],
    c_ij: NDArray[np.floating],
) -> GeometrySignalAuditResult:
    """`distances` is the full all-pairs hop-distance matrix
    (`dynamics/topology_v4.py::graph_distance_matrix`) of the UNDAMAGED
    lattice -- ground truth, not derived from `c_ij` in any way."""
    n = distances.shape[0]
    rows, cols = np.triu_indices(n, k=1)
    dist_vals = distances[rows, cols]
    scores = c_ij[rows, cols]
    is_nn = dist_vals == 1

    if not is_nn.any():
        raise ValueError("compute_geometry_signal_audit: no nearest-neighbor (d*=1) pairs found.")

    pos_scores = scores[is_nn]
    neg_scores = scores[~is_nn]
    u_stat, _ = mannwhitneyu(pos_scores, neg_scores, alternative="two-sided")
    auroc = float(u_stat) / (len(pos_scores) * len(neg_scores))

    rank_metrics_nn = compute_rank_metrics(scores, is_nn)

    rho, pvalue = spearmanr(scores, -dist_vals)

    unique_distances = sorted(int(d) for d in np.unique(dist_vals) if d > 0)
    shells = tuple(
        DistanceShellStats(
            distance=d_val,
            mean_c=float(scores[dist_vals == d_val].mean()),
            n_pairs=int((dist_vals == d_val).sum()),
        )
        for d_val in unique_distances
    )

    d = int(is_nn.sum())
    order = np.argsort(-scores, kind="stable")
    top_d_distances = dist_vals[order[:d]]
    top_d_fractions = {
        d_val: float((top_d_distances == d_val).sum()) / d for d_val in unique_distances
    }

    return GeometrySignalAuditResult(
        auroc_nn=auroc,
        rank_metrics_nn=rank_metrics_nn,
        spearman_rho=float(rho),
        spearman_pvalue=float(pvalue),
        distance_shells=shells,
        top_d_distance_fractions=top_d_fractions,
    )
