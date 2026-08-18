"""`docs/v5_spec.md` Sec15: the Geometry Signal Audit -- does C_ij
encode COARSE distance, decoupled from exact edge identity (`[A69]`).
Hand-derived fixture (prototype verified via `.venv/Scripts/python.exe
-c "..."` before any assertion written): a 4-node cycle
`{(0,1),(1,2),(2,3),(0,3)}`. Distances: 4 pairs at d=1 (the edges
themselves), 2 pairs at d=2 (the diagonals `(0,2)`,`(1,3)`).
"""

import numpy as np
import pytest

from boyko_benchmark.dynamics.topology_v4 import graph_distance_matrix
from boyko_benchmark.observables.geometry_signal_audit import compute_geometry_signal_audit


def _cycle_distances() -> np.ndarray:
    mask = np.zeros((4, 4), dtype=bool)
    for i, j in [(0, 1), (1, 2), (2, 3), (0, 3)]:
        mask[i, j] = mask[j, i] = True
    return graph_distance_matrix(mask)


def test_perfect_geometric_signal() -> None:
    """C_ij=0.9 for all 4 nearest-neighbor (d=1) pairs, 0.1 for the 2
    far (d=2) pairs -- perfect separation. Hand-derived: AUROC=1.0
    (Mann-Whitney U, 4 positives all rank above 2 negatives),
    Recall@4=1.0, AUPRC=1.0, Spearman(C,-d)=+1.0 (monotone: only 2
    distinct distance values, both perfectly ordered)."""
    distances = _cycle_distances()
    c_ij = np.zeros((4, 4))
    for i, j in [(0, 1), (1, 2), (2, 3), (0, 3)]:
        c_ij[i, j] = c_ij[j, i] = 0.9
    for i, j in [(0, 2), (1, 3)]:
        c_ij[i, j] = c_ij[j, i] = 0.1

    result = compute_geometry_signal_audit(distances, c_ij)

    assert result.auroc_nn == 1.0
    assert result.rank_metrics_nn.recall_at_d == 1.0
    assert result.rank_metrics_nn.auprc == 1.0
    assert result.spearman_rho == pytest.approx(1.0)
    assert result.top_d_distance_fractions == {1: 1.0, 2: 0.0}
    shells = {s.distance: s.mean_c for s in result.distance_shells}
    assert shells == {1: pytest.approx(0.9), 2: pytest.approx(0.1)}


def test_anti_signal_gives_auroc_and_spearman_below_chance() -> None:
    """Reversed: C_ij=0.1 for d=1 pairs, 0.9 for d=2 pairs. Hand-derived
    (and independently confirmed via a throwaway script before writing
    this assertion): AUROC=0.0, Recall@4=0.5 (top-4 = both d=2 pairs
    plus 2 of the 4 d=1 pairs, order-dependent), AUPRC=0.525,
    Spearman=-1.0."""
    distances = _cycle_distances()
    c_ij = np.zeros((4, 4))
    for i, j in [(0, 1), (1, 2), (2, 3), (0, 3)]:
        c_ij[i, j] = c_ij[j, i] = 0.1
    for i, j in [(0, 2), (1, 3)]:
        c_ij[i, j] = c_ij[j, i] = 0.9

    result = compute_geometry_signal_audit(distances, c_ij)

    assert result.auroc_nn == 0.0
    assert result.rank_metrics_nn.recall_at_d == pytest.approx(0.5)
    assert result.rank_metrics_nn.auprc == pytest.approx(0.525)
    assert result.spearman_rho == pytest.approx(-1.0)


def test_raises_when_no_nearest_neighbor_pairs_exist() -> None:
    """A graph with no edges at all (e.g. isolated nodes under a
    distance matrix where every finite distance is >1) has no d=1
    pairs to use as the positive class."""
    distances = np.full((3, 3), -1, dtype=np.int64)
    np.fill_diagonal(distances, 0)
    c_ij = np.zeros((3, 3))

    with pytest.raises(ValueError, match="nearest-neighbor"):
        compute_geometry_signal_audit(distances, c_ij)
