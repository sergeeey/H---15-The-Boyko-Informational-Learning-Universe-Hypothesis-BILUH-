"""Phase 11 Milestone 1 (open-system pilot ТЗ §21): DynamicsBackend
interface + ClosedUnitaryBackend adapter over the unmodified
dynamics/fast.py.
"""

import numpy as np
import pytest

from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.fast import evolve_trajectory


def _two_node_hamiltonian() -> np.ndarray:
    return np.array([[1.0, -1.0], [-1.0, 1.0]])  # same fixture as test_fast.py


def test_closed_unitary_backend_matches_fast_module_exactly() -> None:
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0, 0.0], dtype=complex)
    dt = 0.1
    n_steps = 10

    backend_result = ClosedUnitaryBackend().evolve(
        hamiltonian, psi0, dt, n_steps, gamma=0.0, sigma=0.0, noise_seed=None
    )
    direct_result = evolve_trajectory(hamiltonian, psi0, dt, n_steps)

    np.testing.assert_array_equal(backend_result, direct_result)


def test_closed_unitary_backend_rejects_nonzero_gamma() -> None:
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0, 0.0], dtype=complex)

    with pytest.raises(ValueError, match="gamma=0, sigma=0"):
        ClosedUnitaryBackend().evolve(
            hamiltonian, psi0, 0.1, 10, gamma=0.1, sigma=0.0, noise_seed=None
        )


def test_closed_unitary_backend_rejects_nonzero_sigma() -> None:
    hamiltonian = _two_node_hamiltonian()
    psi0 = np.array([1.0, 0.0], dtype=complex)

    with pytest.raises(ValueError, match="gamma=0, sigma=0"):
        ClosedUnitaryBackend().evolve(
            hamiltonian, psi0, 0.1, 10, gamma=0.0, sigma=0.1, noise_seed=None
        )
