"""Phase 11 T5 (no NaN/Inf across pilot configs) and T6 (symmetry
invariants) -- ТЗ §22. Cheap N=8 graph, all 4 factorial pilot cells."""

import numpy as np
import pytest

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.open_dynamics import PhenomenologicalOpenBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.graphs.generators import generate_erdos_renyi

_OMEGA_REF = 2.0  # [A33]

_CELLS = {
    "C0": (0.0, 0.0, None, ClosedUnitaryBackend()),
    "Cgamma": (0.05 * _OMEGA_REF, 0.0, None, PhenomenologicalOpenBackend()),
    "Csigma": (0.0, 0.05, 7, PhenomenologicalOpenBackend()),
    "Cgammasigma": (0.05 * _OMEGA_REF, 0.05, 7, PhenomenologicalOpenBackend()),
}


@pytest.mark.parametrize("cell_name", list(_CELLS.keys()))
def test_t5_no_nan_inf_across_pilot_cells(cell_name: str) -> None:
    gamma, sigma, noise_seed, backend = _CELLS[cell_name]
    rng = np.random.default_rng(11)
    graph = generate_erdos_renyi(n_nodes=8, n_edges=16, rng=rng)
    psi0 = localized_psi0(graph.n_nodes, source_node=0)

    result = run_adaptive_dynamics_open(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        dt=0.05,
        k=10,
        dtau_steps=10,
        backend=backend,
        gamma=gamma,
        sigma=sigma,
        noise_seed=noise_seed,
    )

    assert np.all(np.isfinite(result.final_graph.weights)), f"{cell_name}: non-finite weights"
    for window in result.window_trajectories:
        assert np.all(np.isfinite(window.states)), f"{cell_name}: non-finite states"


@pytest.mark.parametrize("cell_name", list(_CELLS.keys()))
def test_t6_weights_stay_symmetric_across_pilot_cells(cell_name: str) -> None:
    gamma, sigma, noise_seed, backend = _CELLS[cell_name]
    rng = np.random.default_rng(11)
    graph = generate_erdos_renyi(n_nodes=8, n_edges=16, rng=rng)
    psi0 = localized_psi0(graph.n_nodes, source_node=0)

    result = run_adaptive_dynamics_open(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        dt=0.05,
        k=10,
        dtau_steps=10,
        backend=backend,
        gamma=gamma,
        sigma=sigma,
        noise_seed=noise_seed,
    )

    # WeightedGraph.__post_init__ already enforces this at construction
    # time (types.py) -- this test additionally re-checks the RETURNED
    # object explicitly, so a future refactor that bypasses the
    # constructor invariant is still caught here.
    w = result.final_graph.weights
    np.testing.assert_array_equal(w, w.T)
    assert np.all(w >= 0.0), f"{cell_name}: negative weight"
    assert np.array_equal(result.final_graph.mask, graph.mask), f"{cell_name}: mask changed"
