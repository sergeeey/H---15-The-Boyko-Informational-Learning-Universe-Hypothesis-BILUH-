"""Unit tests for full [A17]/[A27] multi-source G5 propagation-front
averaging.

Reference values cross-checked via Bash prototype before writing these
assertions: 3-node path graph (0-1-2, unit weights, source_nodes=(0,1,2)
-- one per node, exercising every hop-distance pattern the graph has),
dt=0.1, n_steps=6, q=0.9, L_norm-driven quantum evolution:
  source 0: r_q(t) = [0,0,0,0,0,1,1]
  source 1: r_q(t) = [0,0,0,0,1,1,1]
  source 2: r_q(t) = [0,0,0,0,0,1,1]
  mean = [0, 0, 0, 0, 0.33333333, 1, 1]
  std  = [0, 0, 0, 0, 0.47140452, 0, 0]
(source 1 is the middle node -- symmetric to both neighbors at hop
distance 1, so its front reaches r=1 one step earlier than the endpoint
sources 0/2, whose r=1 neighborhood is asymmetric -- this asymmetry
between source 1 and sources {0,2} is exactly why [A17] requires
averaging in the first place, not a single fixed node.)
"""

import numpy as np

from boyko_benchmark.arms.shared_initialization import SharedInitialization
from boyko_benchmark.experiment.arms_runner import run_arm_frozen
from boyko_benchmark.experiment.g5_multisource import compute_g5_multisource
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.types import WeightedGraph

_DT = 0.1
_N_STEPS = 6
_Q = 0.9


def _path_graph_3_nodes() -> WeightedGraph:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def test_g5_multisource_matches_hand_prototyped_values_for_frozen_arm() -> None:
    """Frozen (NoAdaptation): final_graph == initial_graph, so the
    quantum evolution driving this test matches the hand-prototyped
    values exactly."""
    shared_init = SharedInitialization(graph=_path_graph_3_nodes(), source_nodes=(0, 1, 2))
    arm_result = run_arm_frozen(shared_init, dt=_DT, k=3, dtau_steps=2)

    mean, std = compute_g5_multisource(
        arm_result,
        laplacian_fn=normalized_laplacian,
        is_classical=False,
        dt=_DT,
        n_steps=_N_STEPS,
        q=_Q,
    )

    expected_mean = np.array([0.0, 0.0, 0.0, 0.0, 1.0 / 3.0, 1.0, 1.0])
    expected_std = np.array([0.0, 0.0, 0.0, 0.0, 0.47140452, 0.0, 0.0])
    np.testing.assert_allclose(mean, expected_mean, atol=1e-6)
    np.testing.assert_allclose(std, expected_std, atol=1e-6)


def test_g5_multisource_returns_arrays_of_correct_length() -> None:
    shared_init = SharedInitialization(graph=_path_graph_3_nodes(), source_nodes=(0, 1, 2))
    arm_result = run_arm_frozen(shared_init, dt=_DT, k=3, dtau_steps=2)

    mean, std = compute_g5_multisource(
        arm_result,
        laplacian_fn=normalized_laplacian,
        is_classical=False,
        dt=_DT,
        n_steps=_N_STEPS,
        q=_Q,
    )

    assert mean.shape == (_N_STEPS + 1,)
    assert std.shape == (_N_STEPS + 1,)


def test_g5_multisource_std_is_zero_when_all_sources_agree() -> None:
    """A single-source arm_result (all three 'sources' identical) must
    give exactly zero std -- a real sanity check on average_over_sources
    wiring, not just 'some numbers came back'."""
    shared_init = SharedInitialization(graph=_path_graph_3_nodes(), source_nodes=(0, 0, 0))
    arm_result = run_arm_frozen(shared_init, dt=_DT, k=3, dtau_steps=2)

    _, std = compute_g5_multisource(
        arm_result,
        laplacian_fn=normalized_laplacian,
        is_classical=False,
        dt=_DT,
        n_steps=_N_STEPS,
        q=_Q,
    )

    np.testing.assert_allclose(std, np.zeros(_N_STEPS + 1), atol=1e-12)
