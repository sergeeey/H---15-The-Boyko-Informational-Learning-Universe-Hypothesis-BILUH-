"""M2 (`docs/v4_spec.md` Sec7, K1 gate, corrected formula 2026-08-18):
`R_edge = |E_recovered ∩ E_damaged_out| / |E_damaged_out|` -- of the
specific edges that were actually broken, what fraction reappear in the
final graph. Plus the wrong-edge-removal rate (correct, never-damaged
edges V4 deletes) reported alongside per Sec7.

Hand-derived fixture: 6-node ring, `E* = {(0,1),(0,5),(1,2),(2,3),(3,4),
(4,5)}`, `E_damaged_out = {(0,1),(2,3)}` (matches `check_lattice_damage.
py`'s own hand-derived example). Recovered graph keeps (0,1) [restored],
loses (2,3) [not restored], loses (4,5) [wrongly deleted, was never
damaged] -> R_edge = 1/2 = 0.5, wrong_removal_rate = 1/4 = 0.25 (4
undamaged edges: (0,5),(1,2),(3,4),(4,5); exactly one missing).
"""

import numpy as np

from boyko_benchmark.observables.edge_recovery import compute_edge_recovery

ORIGINAL_EDGES = frozenset({(0, 1), (0, 5), (1, 2), (2, 3), (3, 4), (4, 5)})
DAMAGED_OUT = frozenset({(0, 1), (2, 3)})


def _mask_from_edges(n_nodes: int, edges: frozenset[tuple[int, int]]) -> np.ndarray:
    mask = np.zeros((n_nodes, n_nodes), dtype=bool)
    for i, j in edges:
        mask[i, j] = mask[j, i] = True
    return mask


def test_r_edge_matches_hand_derived_partial_recovery() -> None:
    recovered_edges = frozenset({(0, 1), (0, 5), (1, 2), (3, 4)})
    mask = _mask_from_edges(6, recovered_edges)

    result = compute_edge_recovery(ORIGINAL_EDGES, DAMAGED_OUT, mask)

    assert result.r_edge == 0.5
    assert result.wrong_removal_rate == 0.25


def test_r_edge_is_one_when_every_damaged_edge_is_restored() -> None:
    recovered_edges = frozenset({(0, 1), (2, 3), (0, 5), (1, 2), (3, 4), (4, 5)})
    mask = _mask_from_edges(6, recovered_edges)

    result = compute_edge_recovery(ORIGINAL_EDGES, DAMAGED_OUT, mask)

    assert result.r_edge == 1.0
    assert result.wrong_removal_rate == 0.0


def test_r_edge_is_zero_when_no_damaged_edge_is_restored() -> None:
    recovered_edges = frozenset({(0, 5), (1, 2), (3, 4), (4, 5)})
    mask = _mask_from_edges(6, recovered_edges)

    result = compute_edge_recovery(ORIGINAL_EDGES, DAMAGED_OUT, mask)

    assert result.r_edge == 0.0


def test_r_edge_numerator_ignores_undamaged_edges_present_in_recovered() -> None:
    """Regression for the spec's original (corrected) formula bug: a
    graph that keeps every undamaged edge but restores NONE of the
    actually-damaged ones must score R_edge=0, not near-1 from counting
    all-of-E* overlap."""
    recovered_edges = frozenset({(0, 5), (1, 2), (3, 4), (4, 5)})
    mask = _mask_from_edges(6, recovered_edges)

    result = compute_edge_recovery(ORIGINAL_EDGES, DAMAGED_OUT, mask)

    assert result.r_edge == 0.0
    assert result.wrong_removal_rate == 0.0
