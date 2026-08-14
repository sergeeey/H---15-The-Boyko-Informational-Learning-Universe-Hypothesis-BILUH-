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


def test_t3_ou_stationary_variance_matches_analytic_prediction() -> None:
    """T3 (ТЗ §22): for the simple Ornstein-Uhlenbeck case (H=0, so
    components are independent and decoupled -- used here as a cheap
    2000-component ENSEMBLE, not a claim about physically meaningful
    multi-node correlation), the discrete recursion
    x_{n+1} = damping*x_n + sigma*sqrt(dt)*zeta gives a stationary
    second moment E[|x_inf|^2] = sigma^2*dt / (1 - damping^2)
    (damping = exp(-gamma*dt)) -- hand-derived from the AR(1) recursion's
    own fixed-point equation, cross-checked numerically via a Bash
    prototype (relative error ~2-4% at n_steps=200, well converged) before
    writing this assertion."""
    n_nodes = 2000  # ensemble via independent (H=0) components
    hamiltonian = np.zeros((n_nodes, n_nodes))
    psi0 = np.zeros(n_nodes, dtype=complex)
    dt = 0.05
    gamma = 0.5
    sigma = 1.0
    n_steps = 200

    trajectory = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=gamma, sigma=sigma, noise_seed=42
    )

    damping = np.exp(-gamma * dt)
    analytic_variance = sigma**2 * dt / (1 - damping**2)
    empirical_variance = np.mean(np.abs(trajectory[-1]) ** 2)

    assert abs(empirical_variance - analytic_variance) / analytic_variance < 0.1


def test_t9_sigma_zero_vs_nonzero_are_distinguishable() -> None:
    """T9 (ТЗ §22): sigma=0 and sigma>0 must give visibly different
    trajectories (sanity check that the noise sub-step actually runs);
    different noise_seed at the same sigma>0 must also differ (rules out
    a hardcoded/frozen noise draw)."""
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0, 0.0], dtype=complex)
    dt = 0.1
    n_steps = 20

    no_noise = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=0.0, sigma=0.0, noise_seed=None
    )
    with_noise_seed1 = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=0.0, sigma=0.3, noise_seed=1
    )
    with_noise_seed2 = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=0.0, sigma=0.3, noise_seed=2
    )

    assert not np.allclose(no_noise, with_noise_seed1)
    assert not np.allclose(with_noise_seed1, with_noise_seed2)
