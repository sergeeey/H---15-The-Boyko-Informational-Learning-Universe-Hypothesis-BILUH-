"""Dynamics backend interface (Phase 11 ТЗ §21) -- lets the same caller
(experiment runner) swap between closed-unitary and open (dissipative/
stochastic) fast dynamics without touching either implementation.

`ClosedUnitaryBackend` wraps `dynamics/fast.py` UNMODIFIED (ТЗ §21: "the
existing closed backend must not be changed directly") -- it is a pure
adapter, not a reimplementation. `PhenomenologicalOpenBackend` (Phase 11
Milestone 1, `open_dynamics.py`) is the first new implementation of this
same interface.
"""

from typing import Protocol

import numpy as np
from numpy.typing import NDArray


class DynamicsBackend(Protocol):
    def evolve(
        self,
        hamiltonian: NDArray[np.floating],
        psi0: NDArray[np.complexfloating],
        dt: float,
        n_steps: int,
        gamma: float,
        sigma: float,
        noise_seed: int | None,
    ) -> NDArray[np.complexfloating]:
        """Returns the trajectory at t = 0, dt, ..., n_steps*dt, shape
        (n_steps+1, N) -- same contract as `fast.evolve_trajectory`.
        `gamma`/`sigma` are dimensionless (`[A33]`: normalized by
        `ω_ref=2`, the proven bound on `L_norm`'s spectrum) dissipation/
        noise strengths; a backend that does not support one or both
        must reject a nonzero value rather than silently ignore it.
        `noise_seed=None` is only valid for backends with no stochastic
        component."""
        ...


class ClosedUnitaryBackend:
    """Adapter over the existing, unmodified `dynamics/fast.py`. Rejects
    any nonzero `gamma`/`sigma` rather than silently dropping them --
    this backend has no dissipative or stochastic capability at all."""

    def evolve(
        self,
        hamiltonian: NDArray[np.floating],
        psi0: NDArray[np.complexfloating],
        dt: float,
        n_steps: int,
        gamma: float,
        sigma: float,
        noise_seed: int | None,
    ) -> NDArray[np.complexfloating]:
        if gamma != 0.0 or sigma != 0.0:
            raise ValueError(
                f"ClosedUnitaryBackend supports only gamma=0, sigma=0 "
                f"(got gamma={gamma}, sigma={sigma}) -- use "
                f"PhenomenologicalOpenBackend for nonzero dissipation/noise"
            )
        from boyko_benchmark.dynamics.fast import evolve_trajectory

        return evolve_trajectory(hamiltonian, psi0, dt, n_steps)
