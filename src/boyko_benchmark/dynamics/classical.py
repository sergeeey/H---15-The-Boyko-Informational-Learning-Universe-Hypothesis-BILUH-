"""Classical diffusion carrier for Arm CD (mathematical_contract.md Sec2.2).

dp/dt = -L(W) p -- the COMBINATORIAL Laplacian, not L_norm ([A18] Choice 1,
self-corrected during Phase-0 drafting: L_norm cannot support a conserved
diffusion on an irregular graph, since its zero eigenvector is D^1/2.1,
not 1). Exact propagator via matrix exponential, same discipline as
dynamics/fast.py's quantum case (no discretization error for constant L).
"""

import numpy as np
import scipy.linalg
from numpy.typing import NDArray


def build_classical_propagator(laplacian: NDArray[np.floating], dt: float) -> NDArray[np.floating]:
    """One-step propagator U = exp(-L dt).

    -L is a valid continuous-time Markov generator (off-diagonal entries
    W_ij >= 0, rows sum to zero) -- a standard fact from Markov chain
    theory guarantees exp(-L dt) is entrywise non-negative for any dt >= 0,
    so this propagator never manufactures negative probability mass.
    """
    result: NDArray[np.floating] = scipy.linalg.expm(-laplacian * dt)
    return result


def evolve_classical_trajectory(
    laplacian: NDArray[np.floating],
    p0: NDArray[np.floating],
    dt: float,
    n_steps: int,
) -> NDArray[np.floating]:
    """Return p at t = 0, dt, ..., n_steps*dt -- shape (n_steps+1, N).

    Conserves Sum(p) exactly (L symmetric, L.1=0 -- see
    mathematical_contract.md Sec2.2's corrected conservation proof), but
    dissipates toward the uniform stationary distribution as t grows
    (ker(L) = span{1}) -- the "heat death" the equilibration caveat warns
    about, unlike the quantum carrier which never settles.
    """
    propagator = build_classical_propagator(laplacian, dt)
    n_nodes = laplacian.shape[0]
    trajectory = np.empty((n_steps + 1, n_nodes))
    trajectory[0] = p0
    for step in range(1, n_steps + 1):
        trajectory[step] = propagator @ trajectory[step - 1]
    return trajectory
