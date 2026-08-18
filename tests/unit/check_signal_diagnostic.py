"""`docs/v5_spec.md` Sec14: the C_ij Recall@D / AUPRC signal diagnostic
-- H1 (signal problem) vs H2 (operator problem). Hand-derived fixture
(prototype verified via `.venv/Scripts/python.exe -c "..."` before any
assertion written): a 4-node graph with edges {(0,1),(0,2),(0,3),(1,2)},
leaving exactly 2 candidate (non-adjacent) pairs: (1,3) and (2,3).
"""

import numpy as np
import pytest

from boyko_benchmark.observables.signal_diagnostic import compute_signal_diagnostic


def _four_node_mask() -> np.ndarray:
    mask = np.zeros((4, 4), dtype=bool)
    for i, j in [(0, 1), (0, 2), (0, 3), (1, 2)]:
        mask[i, j] = mask[j, i] = True
    return mask


def test_perfect_signal_gives_recall_and_ap_of_one() -> None:
    """damaged_out={(1,3)}; C_ij ranks (1,3) above (2,3) -- top-D=top-1
    candidate is exactly the damaged edge. Hand-derived: recall@1=1/1=1.0,
    AP = precision_at_rank(1,3)=1/1=1.0 (only positive, ranked first)."""
    mask = _four_node_mask()
    c_ij = np.zeros((4, 4))
    c_ij[1, 3] = c_ij[3, 1] = 0.9
    c_ij[2, 3] = c_ij[3, 2] = 0.1
    damaged_out = frozenset({(1, 3)})

    result = compute_signal_diagnostic(mask, c_ij, damaged_out)

    assert result.d == 1
    assert result.n_candidates == 2
    assert result.recall_at_d == 1.0
    assert result.auprc == 1.0
    assert result.baseline_recall == 0.5  # D/M = 1/2
    # Reviewer-caught (2026-08-18): AUPRC's chance baseline is NOT D/M --
    # exact closed form for d=1: H_m/m. H_2 = 1 + 1/2 = 1.5, so E[AP] = 0.75,
    # confirmed by brute-force enumeration over both possible rankings.
    assert result.baseline_auprc == pytest.approx(0.75)


def test_anti_signal_gives_recall_and_ap_below_baseline() -> None:
    """Same fixture, C_ij now ranks the WRONG candidate (2,3) first --
    top-1 misses the damaged edge entirely. Hand-derived: recall@1=0/1=0.0;
    AP = precision_at_rank((1,3))=1/2=0.5 (found only at rank 2)."""
    mask = _four_node_mask()
    c_ij = np.zeros((4, 4))
    c_ij[1, 3] = c_ij[3, 1] = 0.1
    c_ij[2, 3] = c_ij[3, 2] = 0.9
    damaged_out = frozenset({(1, 3)})

    result = compute_signal_diagnostic(mask, c_ij, damaged_out)

    assert result.recall_at_d == 0.0
    assert result.auprc == 0.5


def test_raises_on_empty_damaged_out() -> None:
    mask = _four_node_mask()
    c_ij = np.zeros((4, 4))

    with pytest.raises(ValueError, match="empty"):
        compute_signal_diagnostic(mask, c_ij, frozenset())


def test_raises_when_fewer_than_two_candidates() -> None:
    """Reviewer-flagged hardening (2026-08-18): a near-fully-connected
    graph leaving 0 or 1 candidate pairs must fail loudly, not divide
    by zero inside `_expected_average_precision`. 5-node graph missing
    only edge (0,1) -- exactly 1 candidate."""
    mask = np.ones((5, 5), dtype=bool)
    np.fill_diagonal(mask, False)
    mask[0, 1] = mask[1, 0] = False
    c_ij = np.zeros((5, 5))

    with pytest.raises(ValueError, match="candidate"):
        compute_signal_diagnostic(mask, c_ij, frozenset({(0, 1)}))


def test_tie_break_is_deterministic_via_stable_sort() -> None:
    """Reviewer-flagged coverage gap (2026-08-18): 3 candidates, two tied
    at the top score, one of which is the true positive. `np.argsort(...,
    kind='stable')` preserves the `triu_indices`-generated (i,j) order
    among ties -- hand-derived: candidates in generation order are
    (0,2),(0,3),(1,3) [edges present: (0,1),(1,2),(2,3)]; tie between
    (0,2) and (0,3) at score 0.9 keeps (0,2) [generated first] ranked
    above (0,3). damaged_out={(0,3)} -> top-1 is (0,2), a miss."""
    mask = np.zeros((4, 4), dtype=bool)
    for i, j in [(0, 1), (1, 2), (2, 3)]:
        mask[i, j] = mask[j, i] = True
    c_ij = np.zeros((4, 4))
    c_ij[0, 2] = c_ij[2, 0] = 0.9
    c_ij[0, 3] = c_ij[3, 0] = 0.9
    c_ij[1, 3] = c_ij[3, 1] = 0.1
    damaged_out = frozenset({(0, 3)})

    result = compute_signal_diagnostic(mask, c_ij, damaged_out)

    assert result.n_candidates == 3
    assert result.recall_at_d == 0.0  # top-1 = (0,2), not the damaged (0,3)
