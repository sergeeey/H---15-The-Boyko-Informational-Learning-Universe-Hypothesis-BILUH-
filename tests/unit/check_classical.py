"""Unit tests for the classical diffusion carrier (mathematical_contract.md
Sec2.2, Arm CD). Correctness checked against a closed-form solution
hand-derived by eigendecomposition on paper (not via scipy.expm) for the
3-node path graph (degrees 1,2,1) also used in test_weights.py.

Eigenvalues of L=[[1,-1,0],[-1,2,-1],[0,-1,1]]: 0, 1, 3 (characteristic
polynomial -lambda(lambda-1)(lambda-3), factored by hand).
Eigenvectors (normalized): u0=(1,1,1)/sqrt(3), u1=(1,0,-1)/sqrt(2),
u3=(1,-2,1)/sqrt(6) -- orthonormal since L is symmetric with distinct
eigenvalues.
p(0)=(1,0,0) decomposes as c0=1/sqrt(3), c1=1/sqrt(2), c3=1/sqrt(6).

p(t) = (1/3 + exp(-t)/2 + exp(-3t)/6,
        1/3 - exp(-3t)/3,
        1/3 - exp(-t)/2 + exp(-3t)/6)
"""

import numpy as np

from boyko_benchmark.dynamics.classical import (
    build_classical_propagator,
    evolve_classical_trajectory,
)
from boyko_benchmark.graphs.weights import combinatorial_laplacian
from boyko_benchmark.types import WeightedGraph


def _path_graph_3_nodes() -> WeightedGraph:
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def _analytic_solution(t: float) -> np.ndarray:
    e_t = np.exp(-t)
    e_3t = np.exp(-3 * t)
    return np.array(
        [
            1 / 3 + e_t / 2 + e_3t / 6,
            1 / 3 - e_3t / 3,
            1 / 3 - e_t / 2 + e_3t / 6,
        ]
    )


def test_evolve_classical_trajectory_conserves_probability() -> None:
    laplacian = combinatorial_laplacian(_path_graph_3_nodes())
    p0 = np.array([1.0, 0.0, 0.0])

    trajectory = evolve_classical_trajectory(laplacian, p0, dt=0.1, n_steps=20)

    sums = trajectory.sum(axis=1)
    np.testing.assert_allclose(sums, np.ones(21), atol=1e-10)


def test_evolve_classical_trajectory_matches_hand_derived_analytic_solution() -> None:
    laplacian = combinatorial_laplacian(_path_graph_3_nodes())
    p0 = np.array([1.0, 0.0, 0.0])
    dt = 0.05
    n_steps = 20

    trajectory = evolve_classical_trajectory(laplacian, p0, dt=dt, n_steps=n_steps)

    for step in range(n_steps + 1):
        t = step * dt
        expected = _analytic_solution(t)
        np.testing.assert_allclose(trajectory[step], expected, atol=1e-9)


def test_evolve_classical_trajectory_approaches_uniform_at_equilibrium() -> None:
    """ker(L) = span{1} -- long-time limit is uniform (1/3,1/3,1/3), the
    'heat death' mathematical_contract.md Sec2.2's equilibration caveat
    warns about."""
    laplacian = combinatorial_laplacian(_path_graph_3_nodes())
    p0 = np.array([1.0, 0.0, 0.0])

    trajectory = evolve_classical_trajectory(laplacian, p0, dt=0.5, n_steps=40)

    np.testing.assert_allclose(trajectory[-1], np.array([1 / 3, 1 / 3, 1 / 3]), atol=1e-6)


def test_build_classical_propagator_preserves_nonnegativity() -> None:
    """-L is a valid continuous-time Markov generator (off-diagonal >= 0,
    rows sum to zero) -- exp(-L dt) is entrywise non-negative for any
    dt >= 0, a standard Markov-chain-theory fact, not merely a sanity
    check that happens to pass on this example."""
    laplacian = combinatorial_laplacian(_path_graph_3_nodes())
    propagator = build_classical_propagator(laplacian, dt=0.1)

    p0 = np.array([1.0, 0.0, 0.0])
    p1 = propagator @ p0

    assert np.all(p1 >= -1e-12)


def test_evolve_classical_trajectory_has_correct_shape() -> None:
    laplacian = combinatorial_laplacian(_path_graph_3_nodes())
    p0 = np.array([1.0, 0.0, 0.0])

    trajectory = evolve_classical_trajectory(laplacian, p0, dt=0.1, n_steps=5)

    assert trajectory.shape == (6, 3)
