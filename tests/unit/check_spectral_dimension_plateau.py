"""Real G1 plateau detection (mathematical_contract.md Sec5.1), replacing
the provisional `d_s(t_last)` surrogate `cell_aggregation.reduce_g1` used
before 2026-08-13 (external red-team audit + project's own `activeContext.
md` self-disclosure: "not real plateau detection").

Algorithm (`[A30]`, docs/assumptions.md): scan all contiguous windows of
`t_values`/`d_s(t)` with at least `min_points` points; a window is a
"plateau candidate" if the slope of a linear fit of `d_s` against
`log(t)` over that window has `|slope| <= slope_tolerance`. Among
candidates, prefer (1) the most points, (2) the widest log-t span
`W = log(t_max/t_min)` as a tiebreak. Report `d_s_hat` as the window's
mean, plus the window bounds, `W`, `slope`, and `r_squared` -- so callers
get the full diagnostic the contract implicitly wants (persisted, not
just a bare scalar), not another silent single-number surrogate.

Deliberately NOT using an R^2-of-the-flat-fit threshold (an earlier
external proposal): for a genuinely flat window, R^2 of a linear fit is
near-meaningless (near-zero true slope makes R^2 numerically unstable,
close to 0 or even negative for `linregress`, regardless of how flat the
data actually is) -- `|slope| <= tolerance` directly tests the property
that matters ("is d_s roughly constant here"), and R^2 is reported
alongside as a secondary diagnostic, not used as the gate.
"""

import numpy as np

from boyko_benchmark.observables.spectral_dimension import PlateauResult, detect_plateau


def test_detect_plateau_finds_flat_middle_region() -> None:
    """t=[0.1,0.2,0.5,1,2,5,10], d_s rises from 0 toward 3, plateaus near 3
    for the middle stretch, then drifts up again at large t (finite-size
    saturation regime) -- the detector should find the flat middle, not
    the noisy tail."""
    t_values = np.array([0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0])
    d_s_values = np.array([0.5, 1.8, 2.95, 3.0, 3.02, 3.01, 3.9])

    result = detect_plateau(t_values, d_s_values, min_points=3, slope_tolerance=0.05)

    assert isinstance(result, PlateauResult)
    assert result.converged is True
    assert abs(result.d_s_hat - 3.0) < 0.05
    # the plateau should be the 4-point stretch [0.5, 1, 2, 5], not include
    # the t=0.1/0.2 rise or the t=10 finite-size drift.
    assert result.t_window == (0.5, 5.0)
    assert result.n_points == 4


def test_detect_plateau_reports_not_converged_when_no_flat_window_exists() -> None:
    """Strictly monotonic, no flat region anywhere -- must not silently
    return a plausible-looking number; converged must be False."""
    t_values = np.array([0.1, 0.5, 1.0, 2.0, 5.0])
    d_s_values = np.array([0.5, 1.2, 2.1, 3.4, 4.9])

    result = detect_plateau(t_values, d_s_values, min_points=3, slope_tolerance=0.02)

    assert result.converged is False


def test_detect_plateau_on_entirely_constant_data_uses_full_range() -> None:
    t_values = np.array([0.5, 1.0, 2.0, 4.0])
    d_s_values = np.array([2.0, 2.0, 2.0, 2.0])

    result = detect_plateau(t_values, d_s_values, min_points=3, slope_tolerance=0.05)

    assert result.converged is True
    assert abs(result.d_s_hat - 2.0) < 1e-9
    assert result.n_points == 4
    assert abs(result.slope) < 1e-9


def test_detect_plateau_prefers_more_points_over_narrower_perfect_fit() -> None:
    """Two candidate windows both satisfy the slope tolerance: a 3-point
    near-perfect-flat window and a 5-point slightly-less-flat (but still
    within tolerance) window. Point-count wins."""
    t_values = np.array([0.1, 0.5, 1.0, 2.0, 4.0, 8.0])
    d_s_values = np.array([0.5, 3.0, 3.01, 2.99, 3.02, 8.0])

    result = detect_plateau(t_values, d_s_values, min_points=3, slope_tolerance=0.05)

    assert result.converged is True
    assert result.n_points == 4
    assert result.t_window == (0.5, 4.0)


def test_detect_plateau_requires_minimum_points_below_which_it_cannot_converge() -> None:
    t_values = np.array([1.0, 2.0])
    d_s_values = np.array([3.0, 3.0])

    result = detect_plateau(t_values, d_s_values, min_points=3, slope_tolerance=0.05)

    assert result.converged is False
    assert result.n_points == 0


def test_detect_plateau_rejects_a_rise_then_fall_hump_with_near_zero_net_slope() -> None:
    """Regression for a real false positive found 2026-08-13 running the
    [A9] sweep: a genuine Active-arm d_s(t) curve rises toward a peak then
    falls (not a plateau at all), and the 6-point window spanning the peak
    had aggregate slope=-0.035 (within slope_tolerance=0.1) purely because
    the rise and fall cancel out -- while individual points scattered
    across range 3.5 (values [1.8, 3.5, 4.5, 5.0, 3.5, 1.5], hand-derived
    and cross-checked via Bash prototype before writing this assertion).
    The old slope-only gate reported this as `converged=True`; the
    range_tolerance gate must reject it."""
    t_values = np.array([0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0])
    d_s_values = np.array([0.5, 1.8, 3.5, 4.5, 5.0, 3.5, 1.5])

    result = detect_plateau(
        t_values, d_s_values, min_points=3, slope_tolerance=0.1, range_tolerance=0.3
    )

    assert result.converged is False
