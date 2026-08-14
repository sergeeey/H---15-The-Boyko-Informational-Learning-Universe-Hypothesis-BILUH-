"""Phase 11 diagnostics (ТЗ §12.1-12.2): D_W, D_OC. Hand-derived 2x2
fixture so both formulas are checkable by arithmetic, not by trusting
np.linalg.norm circularly."""

import numpy as np
import pytest

from boyko_benchmark.observables.trajectory_divergence import (
    open_vs_closed_divergence,
    weight_trajectory_magnitude,
)


def test_weight_trajectory_magnitude_hand_derived() -> None:
    """W_0 = [[0,1],[1,0]], W_t = [[0,2],[2,0]] -- both symmetric,
    diagonal zero (mask/topology unaffected). ||W_0||_F = sqrt(2),
    ||W_t-W_0||_F = ||[[0,1],[1,0]]||_F = sqrt(2). D_W = sqrt(2)/sqrt(2)
    = 1.0 exactly."""
    w0 = np.array([[0.0, 1.0], [1.0, 0.0]])
    wt = np.array([[0.0, 2.0], [2.0, 0.0]])

    d_w = weight_trajectory_magnitude(wt, w0)

    assert abs(d_w - 1.0) < 1e-12


def test_weight_trajectory_magnitude_is_zero_for_unchanged_weights() -> None:
    w0 = np.array([[0.0, 1.0], [1.0, 0.0]])

    assert weight_trajectory_magnitude(w0, w0) == 0.0


def test_weight_trajectory_magnitude_rejects_zero_reference() -> None:
    w0 = np.zeros((2, 2))
    wt = np.array([[0.0, 1.0], [1.0, 0.0]])

    with pytest.raises(ValueError, match="undefined"):
        weight_trajectory_magnitude(wt, w0)


def test_open_vs_closed_divergence_hand_derived() -> None:
    """Same arithmetic shape as D_W's test, different semantics: compares
    two independently-adapted graphs, not one graph's own trajectory."""
    w_closed = np.array([[0.0, 1.0], [1.0, 0.0]])
    w_open = np.array([[0.0, 2.0], [2.0, 0.0]])

    d_oc = open_vs_closed_divergence(w_open, w_closed)

    assert abs(d_oc - 1.0) < 1e-12


def test_open_vs_closed_divergence_is_zero_for_identical_graphs() -> None:
    w = np.array([[0.0, 1.0], [1.0, 0.0]])

    assert open_vs_closed_divergence(w, w) == 0.0
