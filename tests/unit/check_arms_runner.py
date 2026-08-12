"""Unit tests for per-arm dynamics+adaptation runners
(mathematical_contract.md Sec4).

Hand-derived reference for Arm E's center-node index: side_length=3,
lattice_coordinates' own index() convention is `idx = x*L*L + y*L + z`;
center coordinate is `(L//2, L//2, L//2) = (1,1,1)` for L=3, giving
`idx = 1*9 + 1*3 + 1 = 13` -- computed by hand, matches
`lattice.py`'s own `index()` formula used to BUILD the lattice, so this is
an independent check that `run_arm_fixed_flat_geometry` picks the node its
own docstring claims to pick, not a tautological self-check.
"""

import numpy as np

from boyko_benchmark.arms.shared_initialization import SharedInitialization
from boyko_benchmark.config import Arm
from boyko_benchmark.experiment.arms_runner import (
    ArmRunResult,
    run_arm_active,
    run_arm_alternative_objective,
    run_arm_classical_diffusion_control,
    run_arm_fixed_flat_geometry,
    run_arm_frozen,
    run_arm_parameter_matched_random,
    run_arm_topology_scrambled,
)
from boyko_benchmark.types import WeightedGraph

_DT = 0.1
_K = 3
_DTAU_STEPS = 2


def _shared_init_fixture() -> SharedInitialization:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    graph = WeightedGraph(mask=mask, weights=weights)
    return SharedInitialization(graph=graph, source_nodes=(0, 1, 2))


def test_run_arm_active_changes_weights_and_tags_correctly() -> None:
    shared_init = _shared_init_fixture()

    result = run_arm_active(shared_init, eta=0.1, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)

    assert isinstance(result, ArmRunResult)
    assert result.arm == Arm.ACTIVE
    assert result.source_nodes == (0, 1, 2)
    assert not np.allclose(result.dynamics_result.final_graph.weights, shared_init.graph.weights)


def test_run_arm_frozen_leaves_weights_exactly_unchanged() -> None:
    shared_init = _shared_init_fixture()

    result = run_arm_frozen(shared_init, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)

    assert result.arm == Arm.FROZEN
    np.testing.assert_array_equal(
        result.dynamics_result.final_graph.weights, shared_init.graph.weights
    )


def test_run_arm_alternative_objective_diverges_from_hebbian_on_same_input() -> None:
    """Real correctness check, not just 'weights changed': AlternativeObjective
    ignores phase (density-only), Hebbian uses correlation -- on the SAME
    initial graph/state they must produce DIFFERENT final weights, proving
    the alternative rule's own math path is actually exercised."""
    shared_init = _shared_init_fixture()

    active_result = run_arm_active(shared_init, eta=0.1, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)
    alt_result = run_arm_alternative_objective(
        shared_init, eta=0.1, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS
    )

    assert alt_result.arm == Arm.ALTERNATIVE_OBJECTIVE
    assert not np.allclose(
        active_result.dynamics_result.final_graph.weights,
        alt_result.dynamics_result.final_graph.weights,
    )


def test_run_arm_classical_diffusion_control_conserves_probability() -> None:
    shared_init = _shared_init_fixture()

    result = run_arm_classical_diffusion_control(
        shared_init, eta=0.05, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS
    )

    assert result.arm == Arm.CLASSICAL_DIFFUSION_CONTROL
    final_p = result.dynamics_result.window_trajectories[-1].states[-1].real
    assert abs(np.sum(final_p) - 1.0) < 1e-9
    assert not np.allclose(result.dynamics_result.final_graph.weights, shared_init.graph.weights)


def test_run_arm_parameter_matched_random_matches_requested_size_and_is_frozen() -> None:
    rng = np.random.default_rng(42)

    result = run_arm_parameter_matched_random(
        n_nodes=10, n_edges=15, rng=rng, n_source_nodes=5, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS
    )

    assert result.arm == Arm.PARAMETER_MATCHED_RANDOM
    assert result.initial_graph.n_nodes == 10
    assert int(np.sum(result.initial_graph.mask)) // 2 == 15
    assert len(result.source_nodes) == 5
    assert len(set(result.source_nodes)) == 5  # drawn without replacement
    np.testing.assert_array_equal(
        result.dynamics_result.final_graph.weights, result.initial_graph.weights
    )


def _six_node_ring() -> WeightedGraph:
    n = 6
    mask = np.zeros((n, n), dtype=bool)
    weights = np.zeros((n, n), dtype=float)
    for i in range(n):
        j = (i + 1) % n
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = 1.0
    return WeightedGraph(mask=mask, weights=weights)


def test_run_arm_topology_scrambled_preserves_degree_sequence_of_actives_final_graph() -> None:
    shared_init = SharedInitialization(graph=_six_node_ring(), source_nodes=(0, 1, 2))
    active_result = run_arm_active(shared_init, eta=0.1, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)
    active_final_degree = active_result.dynamics_result.final_graph.mask.sum(axis=1)

    result = run_arm_topology_scrambled(
        active_result,
        rng=np.random.default_rng(7),
        n_swaps=20,
        dt=_DT,
        k=_K,
        dtau_steps=_DTAU_STEPS,
    )

    assert result.arm == Arm.TOPOLOGY_SCRAMBLED
    np.testing.assert_array_equal(result.initial_graph.mask.sum(axis=1), active_final_degree)


def test_run_arm_topology_scrambled_reuses_actives_source_nodes_and_is_frozen() -> None:
    shared_init = SharedInitialization(graph=_six_node_ring(), source_nodes=(0, 1, 2))
    active_result = run_arm_active(shared_init, eta=0.1, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)

    result = run_arm_topology_scrambled(
        active_result,
        rng=np.random.default_rng(7),
        n_swaps=20,
        dt=_DT,
        k=_K,
        dtau_steps=_DTAU_STEPS,
    )

    assert result.source_nodes == active_result.source_nodes
    np.testing.assert_array_equal(
        result.dynamics_result.final_graph.weights, result.initial_graph.weights
    )


def test_run_arm_fixed_flat_geometry_uses_hand_derived_center_index() -> None:
    result = run_arm_fixed_flat_geometry(side_length=3, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)

    assert result.arm == Arm.FIXED_FLAT_GEOMETRY
    assert result.initial_graph.n_nodes == 27
    assert result.source_nodes == (13,)
    np.testing.assert_array_equal(
        result.dynamics_result.final_graph.weights, result.initial_graph.weights
    )
