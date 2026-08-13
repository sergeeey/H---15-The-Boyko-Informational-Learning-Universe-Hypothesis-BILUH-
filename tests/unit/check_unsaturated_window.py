"""Regression for a contract deviation found 2026-08-13 external red-team
audit, tool-verified against the frozen contract before accepting: G5's
`fit_effective_velocity` was always called with `fit_window=(0, len(array))`
-- the FULL trajectory -- while `mathematical_contract.md:508` explicitly
requires "Fit, over the unsaturated (pre-plateau) regime only". Fitting the
saturated tail drags `v_eff` toward zero and is exactly what `check_
propagation_front.py::test_fit_effective_velocity_respects_fit_window_
subset` already demonstrates in isolation -- what was missing is a
function that actually PICKS that window from real data instead of a
caller-supplied constant.

`detect_unsaturated_window` finds the first index where `r_q(t)` stops
strictly increasing (the plateau onset, matching the contract's own
"where r_q(t) plateaus" language for saturation_radius) and returns
`(0, plateau_onset_index)` as the fit window -- clamped to a minimum of 2
points so `scipy.stats.linregress` always has enough data for a line.
"""

import numpy as np

from boyko_benchmark.observables.propagation_front import detect_unsaturated_window


def test_detect_unsaturated_window_stops_at_first_plateau_point() -> None:
    """[0,1,2,3,3,3]: strictly increasing through index 3, then repeats.
    The pre-plateau window is indices [0,4) -- the four increasing points,
    excluding the repeated plateau values."""
    radii = np.array([0, 1, 2, 3, 3, 3])

    window = detect_unsaturated_window(radii)

    assert window == (0, 4)


def test_detect_unsaturated_window_uses_full_trajectory_if_never_plateaus() -> None:
    radii = np.array([0, 1, 2, 3, 4])

    window = detect_unsaturated_window(radii)

    assert window == (0, 5)


def test_detect_unsaturated_window_never_returns_fewer_than_two_points() -> None:
    """Immediate plateau ([0,0,0]) would naively give window=(0,1) -- too
    few points for a linear fit. Clamped to a minimum of 2."""
    radii = np.array([0, 0, 0])

    window = detect_unsaturated_window(radii)

    assert window[1] - window[0] >= 2
