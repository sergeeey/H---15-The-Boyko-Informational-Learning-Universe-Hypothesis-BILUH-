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


def test_detect_unsaturated_window_skips_a_flat_lead_in_before_growth_starts() -> None:
    """Regression for a real bug found 2026-08-13 running the [A9] (K,eta)
    sweep: a real propagation front stays at radius 0 for several steps
    before the pulse spreads past the source node (a genuine "quiet
    period," not saturation) -- the original implementation only ever
    scanned a run starting at index 0, so it saw radii[1]<=radii[0] (both
    0) immediately and returned window=(0,2): two identical zeros, slope
    trivially 0, v_eff=0.0 regardless of the REAL growth that happens
    later in the array. The witness below is a simplified version of the
    exact shape observed in the sweep's raw G5 array (real data had 16
    leading zeros then 0->1->2->3; this test uses fewer points for a
    hand-checkable window bound, same qualitative shape)."""
    radii = np.array([0, 0, 0, 0, 1, 2, 3, 3, 3])

    window = detect_unsaturated_window(radii)

    # the real growth run is indices [3,7) (0->1->2->3, i.e. radii[3..6]);
    # must NOT be the leading flat run (0,2) or (0,4).
    assert window == (3, 7)
