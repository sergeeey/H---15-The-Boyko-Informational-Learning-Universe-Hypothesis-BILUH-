"""Phase 11 mechanistic diagnostics (ТЗ §12.1-12.2): weight-trajectory
magnitude and open-vs-closed trajectory divergence. Neither is a Gate-A
observable (G1-G6) -- both are diagnostic signals for interpreting WHY a
Gate-A result did or didn't change between closed and open dynamics.
"""

import numpy as np
from numpy.typing import NDArray


def weight_trajectory_magnitude(
    weights_t: NDArray[np.floating], weights_0: NDArray[np.floating]
) -> float:
    """D_W(t) = ||W_t - W_0||_F / ||W_0||_F (ТЗ §12.1). Zero means no
    adaptation movement at all; this is a diagnostic for [A35]'s freezing
    concern -- a near-zero D_W on Active would mean a factorial-pilot
    cell "didn't destroy geometry" only because nothing moved, not
    because open dynamics enabled organization."""
    denominator = float(np.linalg.norm(weights_0))
    if denominator == 0.0:
        raise ValueError("weight_trajectory_magnitude: ||W_0||_F == 0, D_W is undefined")
    return float(np.linalg.norm(weights_t - weights_0)) / denominator


def open_vs_closed_divergence(
    weights_open: NDArray[np.floating], weights_closed: NDArray[np.floating]
) -> float:
    """D_OC(t) = ||W_open - W_closed||_F / ||W_closed||_F (ТЗ §12.2).
    D_OC ~= 0 means openness did not measurably affect adaptation --
    ТЗ §16's OPEN_DYNAMICS_NO_EFFECT criterion checks exactly this."""
    denominator = float(np.linalg.norm(weights_closed))
    if denominator == 0.0:
        raise ValueError("open_vs_closed_divergence: ||W_closed||_F == 0, D_OC is undefined")
    return float(np.linalg.norm(weights_open - weights_closed)) / denominator
