"""Unit tests for unitary fast dynamics (mathematical_contract.md Sec2).

Correctness is checked against a closed-form solution for a trivial
2-node system, derived independently by hand (eigendecomposition on
paper, not by calling any matrix-exponential routine) -- so this is not
circular against whatever numerical method the implementation itself
uses internally.

Derivation: 2-node graph, single edge weight 1. Degrees (1,1) ->
L_norm = [[1,-1],[-1,1]]. Eigenvalues 0 and 2, eigenvectors
(1,1)/sqrt(2) and (1,-1)/sqrt(2). Starting from psi(0) = (1,0):
  psi(t) = ((1 + exp(-2it))/2, (1 - exp(-2it))/2)
"""

import numpy as np

from boyko_benchmark.dynamics.fast import build_propagator, evolve_trajectory


def _two_node_hamiltonian() -> np.ndarray:
    return np.array([[1.0, -1.0], [-1.0, 1.0]])  # L_norm of a 2-node single-edge graph


def _analytic_two_node_solution(t: float) -> np.ndarray:
    phase = np.exp(-2j * t)
    return np.array([(1 + phase) / 2, (1 - phase) / 2])


def test_evolve_trajectory_conserves_norm_at_every_step() -> None:
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0 + 0j, 0.0 + 0j])

    trajectory = evolve_trajectory(hamiltonian, psi0, dt=0.1, n_steps=20)

    norms = np.linalg.norm(trajectory, axis=1)
    np.testing.assert_allclose(norms, np.ones(21), atol=1e-10)


def test_evolve_trajectory_matches_hand_derived_analytic_solution() -> None:
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0 + 0j, 0.0 + 0j])
    dt = 0.05
    n_steps = 10

    trajectory = evolve_trajectory(hamiltonian, psi0, dt=dt, n_steps=n_steps)

    for step in range(n_steps + 1):
        t = step * dt
        expected = _analytic_two_node_solution(t)
        np.testing.assert_allclose(trajectory[step], expected, atol=1e-10)


def test_evolve_trajectory_reaches_full_transfer_at_pi_over_2() -> None:
    """At t = pi/2, the closed form gives exactly psi = (0, 1) -- complete
    population transfer to the other node, a clean numeric target."""
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0 + 0j, 0.0 + 0j])
    t_target = np.pi / 2
    n_steps = 100
    dt = t_target / n_steps

    trajectory = evolve_trajectory(hamiltonian, psi0, dt=dt, n_steps=n_steps)

    np.testing.assert_allclose(trajectory[-1], np.array([0.0, 1.0]), atol=1e-8)


def test_build_propagator_is_unitary() -> None:
    hamiltonian = _two_node_hamiltonian()
    propagator = build_propagator(hamiltonian, dt=0.1)

    identity = propagator.conj().T @ propagator
    np.testing.assert_allclose(identity, np.eye(2), atol=1e-10)


def test_evolve_trajectory_has_correct_shape() -> None:
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0 + 0j, 0.0 + 0j])

    trajectory = evolve_trajectory(hamiltonian, psi0, dt=0.1, n_steps=5)

    assert trajectory.shape == (6, 2)
