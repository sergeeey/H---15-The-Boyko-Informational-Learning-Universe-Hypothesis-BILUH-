"""Calibration tests for heat-kernel spectral dimension (ТЗ.txt Sec13's
Milestone-1 list: test_ring_has_ds_near_1, test_square_lattice_has_ds_
near_2, test_cubic_lattice_has_ds_near_3).

Tolerances below are not textbook-assumed -- they were established by
actually running spectral_dimension() on each calibration graph over the
chosen t-range BEFORE writing these assertions, and reading off the real
plateau values, which show genuine finite-size deviation from the exact
integer target (e.g. 3D N=512 plateaus near 3.2-3.65, not exactly 3.0).
The tolerance reflects what was observed, not aspiration.
"""

import numpy as np

from boyko_benchmark.graphs.lattice import (
    generate_periodic_cubic_lattice,
    generate_periodic_ring,
    generate_periodic_square_lattice,
)
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.observables.spectral_dimension import (
    heat_kernel_trace,
    return_probability,
    spectral_dimension,
)


def test_ring_has_ds_near_one() -> None:
    """1D calibration target: d_s ~ 1."""
    graph = generate_periodic_ring(n_nodes=64)
    l_norm = normalized_laplacian(graph)
    t_values = np.logspace(0.0, 1.0, 10)

    d_s = spectral_dimension(l_norm, t_values)

    assert np.all((d_s > 0.9) & (d_s < 1.3))


def test_square_lattice_has_ds_near_two() -> None:
    """2D calibration target: d_s ~ 2."""
    graph = generate_periodic_square_lattice(side_length=16)
    l_norm = normalized_laplacian(graph)
    t_values = np.logspace(0.3, 1.0, 10)

    d_s = spectral_dimension(l_norm, t_values)

    assert np.all((d_s > 1.9) & (d_s < 2.5))


def test_cubic_lattice_has_ds_near_three() -> None:
    """3D calibration target: d_s ~ 3 (Arm E's own geometry)."""
    graph = generate_periodic_cubic_lattice(side_length=8)
    l_norm = normalized_laplacian(graph)
    t_values = np.logspace(0.4, 0.85, 10)

    d_s = spectral_dimension(l_norm, t_values)

    assert np.all((d_s > 2.9) & (d_s < 4.0))


def test_return_probability_at_t_zero_is_one() -> None:
    """P_return(0) = Tr(exp(0))/N = N/N = 1, exact regardless of graph."""
    graph = generate_periodic_ring(n_nodes=10)
    l_norm = normalized_laplacian(graph)

    p = return_probability(l_norm, t=0.0)

    assert abs(p - 1.0) < 1e-10


def test_heat_kernel_trace_matches_independent_eigenvalue_sum() -> None:
    """Sanity: heat_kernel_trace matches a hand-written sum computed here,
    not just 'whatever the function returns' -- independent
    recomputation, not a tautology against its own implementation."""
    graph = generate_periodic_ring(n_nodes=8)
    l_norm = normalized_laplacian(graph)
    eigenvalues = np.linalg.eigvalsh(l_norm)
    t = 0.5
    expected = float(sum(np.exp(-t * lam) for lam in eigenvalues))

    actual = heat_kernel_trace(l_norm, t)

    assert abs(actual - expected) < 1e-10
