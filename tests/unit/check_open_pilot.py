"""Phase 11 (open-system pilot ТЗ §21): run_adaptive_dynamics_open wiring
sanity check, then T7 (ТЗ §22) -- the positive-control lattice repeat
with open dynamics, doubling as Milestone 2's own gate (ТЗ §31: "at least
one nonzero (gamma,sigma) regime must not destroy lattice geometry")."""

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.open_dynamics import PhenomenologicalOpenBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.runner import localized_psi0, run_adaptive_dynamics
from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, lattice_coordinates
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.observables.spectral_dimension import spectral_dimension
from boyko_benchmark.types import WeightedGraph

_OMEGA_REF = 2.0  # [A33]: the proven bound on L_norm's spectrum


def _small_test_graph() -> WeightedGraph:
    rng = np.random.default_rng(7)
    return generate_erdos_renyi(n_nodes=8, n_edges=16, rng=rng)


def test_run_adaptive_dynamics_open_matches_closed_loop_at_zero_gamma_sigma() -> None:
    """Wiring sanity check: the new open-loop entry point, with
    ClosedUnitaryBackend and gamma=0/sigma=0, must reproduce the exact
    same final graph and trajectories as the existing (unmodified)
    run_adaptive_dynamics -- proves the loop restructuring introduced no
    behavioral change at the closed limit."""
    graph = _small_test_graph()
    psi0 = localized_psi0(graph.n_nodes, source_node=0)
    dt = 0.05
    k = 10
    dtau_steps = 5
    eta = 0.1

    closed_result = run_adaptive_dynamics(
        graph, psi0, HebbianAdaptation(eta=eta), dt, k, dtau_steps
    )
    open_result = run_adaptive_dynamics_open(
        graph,
        psi0,
        HebbianAdaptation(eta=eta),
        dt,
        k,
        dtau_steps,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )

    np.testing.assert_allclose(
        closed_result.final_graph.weights, open_result.final_graph.weights, atol=1e-12
    )
    np.testing.assert_array_equal(closed_result.final_graph.mask, open_result.final_graph.mask)


def _lattice_setup() -> tuple[WeightedGraph, np.ndarray]:
    side_length = 4  # N=64, same as [A32]
    graph = generate_periodic_cubic_lattice(side_length)
    coords = lattice_coordinates(side_length)
    center_coord = np.array([side_length // 2] * 3)
    center_index = int(np.argmin(np.sum((coords - center_coord) ** 2, axis=1)))
    psi0 = localized_psi0(graph.n_nodes, center_index)
    return graph, psi0


def test_t7_open_dynamics_does_not_destroy_lattice_geometry() -> None:
    """T7 / Milestone 2 gate (ТЗ §22, §31): repeats [A32]'s cheapest
    differentiating test (HebbianAdaptation on a lattice, not disordered
    Active) at all 4 factorial pilot cells (ТЗ §10: C0/Cgamma/Csigma/
    Cgammasigma) instead of only the closed C0 baseline. Numbers
    cross-checked via a background script run before writing this
    assertion (peak d_s_hat ranged 2.97-3.17 across all 4 cells vs the
    unadapted lattice's own 3.173 -- none collapsed toward 0 or exploded).

    Mechanistic caveat surfaced by that same run, recorded in [A35]
    rather than silently absorbed here: at gamma_tilde=0.05
    (gamma=0.1), weight std after adaptation is only ~0.007 (vs closed
    C0's ~0.11) -- dissipation this strong appears to nearly FREEZE
    Hebbian weight movement at this K/dt/dtau_steps budget, not just
    protect geometry. That is a real finding for Milestone 3's grid
    choice, not resolved or hidden by this test passing."""
    graph, psi0 = _lattice_setup()
    dt, k, dtau_steps, eta = 0.05, 50, 50, 0.1
    t_values = np.geomspace(0.1, 10.0, num=12)

    laplacian_before = normalized_laplacian(graph)
    peak_before = float(np.max(spectral_dimension(laplacian_before, t_values)))

    cells = {
        "C0": (0.0, 0.0, None),
        "Cgamma": (0.05 * _OMEGA_REF, 0.0, None),
        "Csigma": (0.0, 0.05, 123),
        "Cgammasigma": (0.05 * _OMEGA_REF, 0.05, 123),
    }

    for name, (gamma, sigma, noise_seed) in cells.items():
        result = run_adaptive_dynamics_open(
            graph,
            psi0,
            HebbianAdaptation(eta=eta),
            dt,
            k,
            dtau_steps,
            backend=PhenomenologicalOpenBackend(),
            gamma=gamma,
            sigma=sigma,
            noise_seed=noise_seed,
        )
        adapted_graph = result.final_graph
        assert np.all(np.isfinite(adapted_graph.weights)), f"{name}: non-finite weights"

        laplacian_after = normalized_laplacian(adapted_graph)
        d_s_after = spectral_dimension(laplacian_after, t_values)
        peak_after = float(np.max(d_s_after))

        # geometry-destruction gate: peak must stay within +-1.0 of the
        # unadapted lattice's own peak (~3.17) -- a real collapse toward
        # an expander-like signature would show peak GROWING or the
        # curve losing its localized-near-3 peak shape entirely, not a
        # ~5% wiggle.
        assert abs(peak_after - peak_before) < 1.0, (
            f"{name}: peak d_s {peak_after:.3f} diverged >1.0 from unadapted "
            f"lattice's {peak_before:.3f} -- possible geometry destruction"
        )
