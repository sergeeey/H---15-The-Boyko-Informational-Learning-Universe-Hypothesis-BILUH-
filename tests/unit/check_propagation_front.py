"""Unit tests for the operational finite-propagation front (G5,
mathematical_contract.md Sec5.5).

Hand-derived references, cross-checked numerically via Bash prototype
before writing these assertions (same discipline as every other observable
this session):

- hop distances on the 3-node path graph (0-1-2) from source 0: [0,1,2]
  (trivial BFS on a path -- no computation needed to derive by hand).
- propagation_front_radius on hop_distances=[0,1,2], density=[0.5,0.3,0.2]:
  q=0.9 needs r=2 (cumulative 0.5, 0.8, 1.0 -- crosses 0.9 only at r=2);
  q=0.7 needs r=1 (cumulative 0.5, 0.8 -- crosses 0.7 at r=1).
- fit_effective_velocity on EXACT synthetic line r=2t+1 (t=0..4): scipy
  linregress gives slope=2.0, rvalue=1.0, stderr=0.0 exactly (zero
  residuals) -- verified via Bash prototype, not assumed.
- average_over_sources on [[0,1,2],[0,2,4]]: mean=[0,1.5,3],
  std=[0,0.5,1] (population std, ddof=0) -- verified via Bash prototype.
"""

import numpy as np

from boyko_benchmark.observables.propagation_front import (
    PropagationFrontFit,
    average_over_sources,
    fit_effective_velocity,
    hop_distances_from_source,
    propagation_front_radius,
    propagation_front_trajectory,
)


def _path_graph_3_nodes_mask() -> np.ndarray:
    return np.array([[False, True, False], [True, False, True], [False, True, False]])


def test_hop_distances_from_source_matches_hand_derived_path_distances() -> None:
    mask = _path_graph_3_nodes_mask()

    distances = hop_distances_from_source(mask, source=0)

    np.testing.assert_array_equal(distances, np.array([0, 1, 2]))


def test_hop_distances_from_middle_node_is_symmetric() -> None:
    mask = _path_graph_3_nodes_mask()

    distances = hop_distances_from_source(mask, source=1)

    np.testing.assert_array_equal(distances, np.array([1, 0, 1]))


def test_propagation_front_radius_matches_hand_derived_cumulative_sum() -> None:
    hop_distances = np.array([0, 1, 2])
    density = np.array([0.5, 0.3, 0.2])

    assert propagation_front_radius(density, hop_distances, q=0.9) == 2
    assert propagation_front_radius(density, hop_distances, q=0.7) == 1


def test_propagation_front_radius_of_fully_localized_density_is_zero() -> None:
    """All mass at the source node itself -- r_q=0 for any q<=1, the mass
    at radius 0 already covers the full threshold."""
    hop_distances = np.array([0, 1, 2])
    density = np.array([1.0, 0.0, 0.0])

    assert propagation_front_radius(density, hop_distances, q=0.9) == 0


def test_propagation_front_radius_rejects_unreachable_nodes() -> None:
    hop_distances = np.array([0, 1, -1])
    density = np.array([0.5, 0.5, 0.0])

    try:
        propagation_front_radius(density, hop_distances, q=0.9)
        raise AssertionError("expected ValueError for unreachable (-1) node")
    except ValueError:
        pass


def test_propagation_front_trajectory_matches_per_step_radius() -> None:
    hop_distances = np.array([0, 1, 2])
    density_trajectory = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.5, 0.3, 0.2],
            [0.34, 0.33, 0.33],
        ]
    )

    trajectory = propagation_front_trajectory(density_trajectory, hop_distances, q=0.9)

    np.testing.assert_array_equal(trajectory, np.array([0, 2, 2]))


def test_fit_effective_velocity_recovers_exact_synthetic_slope() -> None:
    times = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    radii = 2.0 * times + 1.0

    fit = fit_effective_velocity(times, radii, fit_window=(0, 5))

    assert isinstance(fit, PropagationFrontFit)
    assert abs(fit.v_eff - 2.0) < 1e-9
    assert abs(fit.r_squared - 1.0) < 1e-9
    assert abs(fit.ci_95[0] - 2.0) < 1e-6
    assert abs(fit.ci_95[1] - 2.0) < 1e-6
    assert fit.fit_window == (0, 5)
    assert abs(fit.saturation_radius - float(np.max(radii))) < 1e-9


def test_fit_effective_velocity_respects_fit_window_subset() -> None:
    """Only the first 3 points are exactly linear (v=1); points after that
    plateau -- fitting only the unsaturated window must recover v_eff=1,
    not be dragged toward 0 by the plateau."""
    times = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    radii = np.array([0.0, 1.0, 2.0, 2.0, 2.0])

    fit = fit_effective_velocity(times, radii, fit_window=(0, 3))

    assert abs(fit.v_eff - 1.0) < 1e-9
    assert abs(fit.saturation_radius - 2.0) < 1e-9


def test_average_over_sources_matches_hand_derived_mean_and_std() -> None:
    trajectories = [np.array([0, 1, 2]), np.array([0, 2, 4])]

    mean, std = average_over_sources(trajectories)

    np.testing.assert_allclose(mean, np.array([0.0, 1.5, 3.0]))
    np.testing.assert_allclose(std, np.array([0.0, 0.5, 1.0]))
