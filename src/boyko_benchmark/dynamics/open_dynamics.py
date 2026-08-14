"""Phenomenological open-system fast dynamics (Phase 11 ТЗ §6 Backend A,
§7 split-step integrator). NOT claimed as physically-valid open quantum
mechanics -- `X(t)` is a phenomenological carrier, not asserted to be a
quantum state (ТЗ §6: "Backend A ... results cannot be used for claims
about physically correct open quantum mechanics"). A GKSL/Lindblad-valid
Backend B is deferred to Phase 11B, only if this backend shows a signal.

One step, split into three sub-steps per ТЗ §7 (never fused into one
Euler-Maruyama update on the full right-hand side):

    A. Deterministic propagation: X' = exp(-iH dt) X
    B. Dissipation:                X'' = exp(-gamma dt) X'
    C. Noise:                      X(t+dt) = X'' + sigma sqrt(dt) zeta

Critically: NO renormalization after any step. ТЗ §5's own warning is the
reason -- normalizing after uniform damping (`-gamma X`) can silently
cancel gamma's entire effect, since damping shrinks every component by
the same factor. `[A33]`'s `[A34]` entry (docs/assumptions.md) records
the noise model: `zeta` is complex standard normal (independent real/
imag parts, each N(0, 0.5), so E[|zeta|^2]=1).
"""

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.fast import build_propagator


class PhenomenologicalOpenBackend:
    """Backend A (ТЗ §6): dissipative + stochastic carrier, split-step
    integrated (ТЗ §7). At `gamma=0, sigma=0` this must reduce EXACTLY to
    `ClosedUnitaryBackend`'s trajectory -- both use the same
    `build_propagator` for step A, and steps B/C become no-ops
    (`exp(-0*dt)=1`, no noise term added) -- verified by T1."""

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
        if sigma != 0.0 and noise_seed is None:
            raise ValueError(
                "PhenomenologicalOpenBackend: sigma != 0 requires an explicit "
                "noise_seed (ТЗ §8 -- no shared/implicit seed pseudo-replication)"
            )

        propagator = build_propagator(hamiltonian, dt)
        damping = np.exp(-gamma * dt)
        rng = np.random.default_rng(noise_seed) if sigma != 0.0 else None
        n_nodes = hamiltonian.shape[0]

        trajectory = np.empty((n_steps + 1, n_nodes), dtype=complex)
        trajectory[0] = psi0
        x = psi0.astype(complex).copy()
        for step in range(1, n_steps + 1):
            x = propagator @ x  # A. deterministic
            x = damping * x  # B. dissipation, no renormalization (ТЗ §5)
            if sigma != 0.0:
                assert rng is not None
                real = rng.normal(0.0, np.sqrt(0.5), size=n_nodes)
                imag = rng.normal(0.0, np.sqrt(0.5), size=n_nodes)
                zeta = real + 1j * imag
                x = x + sigma * np.sqrt(dt) * zeta  # C. noise
            trajectory[step] = x
        return trajectory
