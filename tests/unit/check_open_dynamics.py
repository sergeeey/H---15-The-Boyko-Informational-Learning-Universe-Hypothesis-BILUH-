"""Phase 11 Milestone 1 (open-system pilot ТЗ §22): mandatory unit/
regression tests T1, T2, T8 for PhenomenologicalOpenBackend.

Hand-derived reference (same 2-node fixture as test_fast.py/
check_dynamics_backend.py): L_norm of a 2-node single-edge graph,
eigenvalues 0 and 2, so exp(-iH t) is exactly solvable by hand -- no
numerical method is assumed correct circularly.
"""

import numpy as np

from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.open_dynamics import PhenomenologicalOpenBackend


def _two_node_hamiltonian() -> np.ndarray:
    return np.array([[1.0, -1.0], [-1.0, 1.0]])


def test_t1_closed_limit_matches_closed_unitary_backend_exactly() -> None:
    """T1 (ТЗ §22): at gamma=0, sigma=0, the open backend must reproduce
    the closed backend within numerical error -- both use the same
    build_propagator for the deterministic step; damping/noise become
    no-ops."""
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0, 0.0], dtype=complex)
    dt = 0.1
    n_steps = 20

    open_result = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=0.0, sigma=0.0, noise_seed=None
    )
    closed_result = ClosedUnitaryBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=0.0, sigma=0.0, noise_seed=None
    )

    np.testing.assert_allclose(open_result, closed_result, atol=1e-12)


def test_t2_pure_damping_matches_analytic_exponential_decay() -> None:
    """T2 (ТЗ §22): with H=0 (no rotation, isolates damping), sigma=0,
    |X(t)| must follow the exact analytic solution |X(t)| = |X(0)| *
    exp(-gamma*t) -- hand-derivable in closed form since damping is
    applied as a uniform per-step scalar factor exp(-gamma*dt), and NO
    renormalization ever intervenes (ТЗ §5's own point)."""
    n_nodes = 2
    hamiltonian = np.zeros((n_nodes, n_nodes))  # H=0: no rotation at all
    psi0 = np.array([1.0, 0.0], dtype=complex)
    dt = 0.1
    n_steps = 50
    gamma = 0.3

    trajectory = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=gamma, sigma=0.0, noise_seed=None
    )

    times = np.arange(n_steps + 1) * dt
    magnitudes = np.linalg.norm(trajectory, axis=1)
    expected = np.linalg.norm(psi0) * np.exp(-gamma * times)

    np.testing.assert_allclose(magnitudes, expected, rtol=1e-10)


def test_t8_gamma_does_not_vanish_from_normalization() -> None:
    """T8 (ТЗ §22, the exact pitfall ТЗ §5 warns about): a backend that
    silently renormalizes psi after damping would show IDENTICAL |X(t)|
    trajectories for gamma=0 and gamma>0 (uniform damping shrinks every
    component by the same factor, exactly cancelled by renormalization).
    This backend must NOT do that -- gamma>0 must produce a strictly
    smaller norm than gamma=0 at the same t>0."""
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0, 0.0], dtype=complex)
    dt = 0.1
    n_steps = 20

    undamped = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=0.0, sigma=0.0, noise_seed=None
    )
    damped = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=0.5, sigma=0.0, noise_seed=None
    )

    undamped_norms = np.linalg.norm(undamped, axis=1)
    damped_norms = np.linalg.norm(damped, axis=1)

    # undamped norm is conserved (unitary); damped norm must strictly
    # decrease and end up strictly below the undamped trajectory.
    np.testing.assert_allclose(undamped_norms, 1.0, atol=1e-12)
    assert damped_norms[-1] < undamped_norms[-1] - 1e-6
    assert damped_norms[-1] < damped_norms[0]
