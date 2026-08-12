"""Unit tests for the Operator-Independence Diagnostic
(mathematical_contract.md Sec5.6, corrected version -- full parallel
dynamics rerun, not a readout-only swap).

Real correctness check, not just "it runs": `run_operator_independence_
diagnostic` must be numerically IDENTICAL to calling `run_adaptive_
dynamics` directly with `hamiltonian_fn=combinatorial_laplacian` on the
same inputs -- proving the diagnostic actually drives the loop with L, not
just relabels an L_norm-driven run. It must also DIFFER from Active's own
(L_norm-driven) result on the same shared initialization, since L != L_norm
whenever any node's weighted degree != 1 (true here).
"""

import numpy as np

from boyko_benchmark.arms.shared_initialization import SharedInitialization
from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.experiment.arms_runner import run_arm_active
from boyko_benchmark.experiment.operator_independence import (
    run_operator_independence_diagnostic,
)
from boyko_benchmark.experiment.runner import run_adaptive_dynamics
from boyko_benchmark.graphs.weights import combinatorial_laplacian
from boyko_benchmark.types import WeightedGraph

_DT = 0.05
_K = 3
_DTAU_STEPS = 2
_ETA = 0.1


def _path_graph_3_nodes() -> WeightedGraph:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def test_diagnostic_matches_manual_l_driven_run_adaptive_dynamics_call() -> None:
    shared_init = SharedInitialization(graph=_path_graph_3_nodes(), source_nodes=(0,))

    diagnostic_result = run_operator_independence_diagnostic(
        shared_init, eta=_ETA, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS
    )

    psi0 = np.array([1.0, 0.0, 0.0], dtype=complex)
    manual_result = run_adaptive_dynamics(
        shared_init.graph,
        psi0,
        HebbianAdaptation(eta=_ETA),
        _DT,
        _K,
        _DTAU_STEPS,
        hamiltonian_fn=combinatorial_laplacian,
    )

    np.testing.assert_allclose(
        diagnostic_result.final_graph.weights, manual_result.final_graph.weights, atol=1e-12
    )
    np.testing.assert_allclose(
        diagnostic_result.window_trajectories[-1].states,
        manual_result.window_trajectories[-1].states,
        atol=1e-12,
    )


def test_diagnostic_diverges_from_actives_l_norm_driven_run() -> None:
    """On the same shared init, the L-driven diagnostic and Active's own
    L_norm-driven run must produce DIFFERENT final graphs -- proving the
    diagnostic genuinely uses a different operator, not accidentally
    reusing L_norm under a different name (the exact failure mode the 1st,
    superseded diagnostic version had -- a swap that stayed quiet)."""
    shared_init = SharedInitialization(graph=_path_graph_3_nodes(), source_nodes=(0,))

    active_result = run_arm_active(shared_init, eta=_ETA, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)
    diagnostic_result = run_operator_independence_diagnostic(
        shared_init, eta=_ETA, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS
    )

    assert not np.allclose(
        active_result.dynamics_result.final_graph.weights, diagnostic_result.final_graph.weights
    )


def test_run_adaptive_dynamics_default_hamiltonian_still_uses_l_norm() -> None:
    """Regression check on the Cycle-15 refactor: adding the
    `hamiltonian_fn` parameter must not change the DEFAULT behavior --
    Active's own arm runner (which calls run_adaptive_dynamics with no
    hamiltonian_fn override) must still be L_norm-driven, matching its
    pre-refactor result exactly."""
    shared_init = SharedInitialization(graph=_path_graph_3_nodes(), source_nodes=(0,))
    psi0 = np.array([1.0, 0.0, 0.0], dtype=complex)

    default_result = run_adaptive_dynamics(
        shared_init.graph, psi0, HebbianAdaptation(eta=_ETA), _DT, _K, _DTAU_STEPS
    )
    active_result = run_arm_active(shared_init, eta=_ETA, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)

    np.testing.assert_allclose(
        default_result.final_graph.weights,
        active_result.dynamics_result.final_graph.weights,
        atol=1e-12,
    )
