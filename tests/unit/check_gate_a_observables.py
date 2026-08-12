"""Unit tests for Gate-A observable wiring (mathematical_contract.md Sec5).

Uses `run_arm_frozen` (NoAdaptation) on the same 3-node path graph reused
throughout this session, so the FINAL graph is bit-identical to the
INITIAL graph -- letting this test reuse Phase 6's independently
hand-derived reference values directly instead of re-deriving them for an
adapted (and therefore no-longer-hand-tractable) graph:
- G2 (L_norm gap): 1.0 exactly (characteristic polynomial roots {0,1,2}).
- G3 (resistance diameter, combinatorial L): 2.0 exactly (series circuit).
- G4 (IPR of lowest L_norm mode): 0.375 exactly.
All three already verified in `check_laplacian_gap.py`/
`check_graph_geometry.py`/`check_ipr.py` -- reused here as ground truth
for the WIRING, not re-derived.

Concatenated-density helper verified via Bash prototype before writing
the shape-based test below: window boundaries duplicate a point ([[1,4,9],
[9,16]] two-window example concatenates to [1,4,9,16], not [1,4,9,9,16]).
"""

import numpy as np

from boyko_benchmark.arms.shared_initialization import SharedInitialization
from boyko_benchmark.experiment.arms_runner import run_arm_frozen
from boyko_benchmark.experiment.gate_a_observables import (
    GateAObservables,
    compute_gate_a_observables,
)
from boyko_benchmark.types import WeightedGraph

_DT = 0.1
_K = 3
_DTAU_STEPS = 2
_T_VALUES = np.array([0.5, 1.0, 2.0])
_Q = 0.9


def _path_graph_3_nodes() -> WeightedGraph:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def _frozen_arm_result():
    shared_init = SharedInitialization(graph=_path_graph_3_nodes(), source_nodes=(0,))
    return run_arm_frozen(shared_init, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)


def test_g2_g3_g4_match_phase6_hand_derived_values_on_frozen_arm() -> None:
    arm_result = _frozen_arm_result()

    observables = compute_gate_a_observables(
        arm_result, is_l_driven=False, t_values=_T_VALUES, q=_Q
    )

    assert isinstance(observables, GateAObservables)
    assert abs(observables.g2_laplacian_gap - 1.0) < 1e-9
    assert abs(observables.g3_resistance_diameter - 2.0) < 1e-9
    assert abs(observables.g4_ipr - 0.375) < 1e-9


def test_g1_spectral_dimension_has_expected_shape() -> None:
    arm_result = _frozen_arm_result()

    observables = compute_gate_a_observables(
        arm_result, is_l_driven=False, t_values=_T_VALUES, q=_Q
    )

    assert observables.g1_spectral_dimension.shape == _T_VALUES.shape


def test_g5_propagation_front_has_full_concatenated_trajectory_length() -> None:
    arm_result = _frozen_arm_result()

    observables = compute_gate_a_observables(
        arm_result, is_l_driven=False, t_values=_T_VALUES, q=_Q
    )

    expected_length = _DTAU_STEPS * _K + 1
    assert observables.g5_propagation_front.shape == (expected_length,)
    assert np.all(observables.g5_propagation_front >= 0)
    assert np.all(observables.g5_propagation_front <= 2)  # graph diameter is 2


def test_is_l_driven_changes_g2_but_not_g3() -> None:
    """Operator-Matching Rule: G3 always uses combinatorial L regardless
    of `is_l_driven`; G2 must differ between the two Laplacians when they
    are genuinely different operators.

    Uses a WEIGHTED path (0-1 weight 1, 1-2 weight 2), not the uniform
    unit-weight path used elsewhere in this file: on the uniform path, L
    and L_norm coincidentally share the same gap (both give eigenvalues
    with gap 1.0 for N=3, verified via Bash prototype) -- a degenerate
    special case of that specific small symmetric graph, not evidence the
    two operators are interchangeable in general. The weighted path breaks
    this coincidence: verified via Bash prototype, L eigenvalues
    {0, 1.268, 4.732} (gap 1.268) vs L_norm's {0, 1.0, 2.0} (gap 1.0) --
    genuinely different operators, genuinely different gaps."""
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 2.0], [0.0, 2.0, 0.0]])
    weighted_graph = WeightedGraph(mask=mask, weights=weights)
    shared_init = SharedInitialization(graph=weighted_graph, source_nodes=(0,))
    arm_result = run_arm_frozen(shared_init, dt=_DT, k=_K, dtau_steps=_DTAU_STEPS)

    quantum_observables = compute_gate_a_observables(
        arm_result, is_l_driven=False, t_values=_T_VALUES, q=_Q
    )
    l_driven_observables = compute_gate_a_observables(
        arm_result, is_l_driven=True, t_values=_T_VALUES, q=_Q
    )

    assert quantum_observables.g3_resistance_diameter == l_driven_observables.g3_resistance_diameter
    assert abs(quantum_observables.g2_laplacian_gap - 1.0) < 1e-9
    assert abs(l_driven_observables.g2_laplacian_gap - 1.2679491924311228) < 1e-9
