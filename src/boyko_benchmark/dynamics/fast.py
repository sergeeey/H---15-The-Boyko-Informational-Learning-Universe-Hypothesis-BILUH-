"""Unitary fast dynamics: i dpsi/dt = H psi (mathematical_contract.md Sec2).

For a time-independent Hamiltonian -- true throughout Phase 2, since
adaptation (which would make W, and hence H, change over time) is not
wired in until Phase 3 -- the exact solution is psi(t) = exp(-i H t)
psi(0). Using the matrix exponential directly, rather than a discretized
stepper (RK4 etc.), gives an exact propagator with no truncation error,
only floating-point round-off.

Once Phase 3 wires in adaptation, H changes between (not within) K-step
windows (assumptions.md [A9]); this module's per-window constant-H
propagator composes naturally into that piecewise-constant scheme without
modification -- each window gets its own build_propagator call.
"""

import numpy as np
import scipy.linalg
from numpy.typing import NDArray


def build_propagator(hamiltonian: NDArray[np.floating], dt: float) -> NDArray[np.complexfloating]:
    """One-step unitary propagator U = exp(-i H dt)."""
    result: NDArray[np.complexfloating] = scipy.linalg.expm(-1j * hamiltonian * dt)
    return result


def evolve_trajectory(
    hamiltonian: NDArray[np.floating],
    psi0: NDArray[np.complexfloating],
    dt: float,
    n_steps: int,
) -> NDArray[np.complexfloating]:
    """Return psi at t = 0, dt, 2*dt, ..., n_steps*dt -- shape (n_steps+1, N).

    Applies the same precomputed propagator n_steps times (exact for
    constant H: exp(-iHdt)^n = exp(-iH*n*dt)) rather than recomputing the
    matrix exponential from scratch at every step.
    """
    propagator = build_propagator(hamiltonian, dt)
    n_nodes = hamiltonian.shape[0]
    trajectory = np.empty((n_steps + 1, n_nodes), dtype=complex)
    trajectory[0] = psi0
    for step in range(1, n_steps + 1):
        trajectory[step] = propagator @ trajectory[step - 1]
    return trajectory
