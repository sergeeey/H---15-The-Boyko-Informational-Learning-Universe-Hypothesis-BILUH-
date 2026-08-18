"""`dynamics/adaptive.py::time_averaged_correlation_magnitude` --
reviewer-caught addition (2026-08-18, `docs/v5_spec.md` Sec15,
`docs/assumptions.md` `[A70]`/`[A71]`): on the project's own exactly-
bipartite T7 lattice, `Re(<psi_i* psi_j>_K)` cancels to machine epsilon
for cross-parity pairs regardless of real coupling -- this function
exposes the MAGNITUDE instead, which does not share that degeneracy.

Hand-derived minimal case: single snapshot (K=1), `psi = [1, 1j]` --
`conj(psi_0)*psi_1 = 1j`, `Re(1j)=0` but `|1j|=1.0`. This is the
smallest possible demonstration of exactly the phenomenon that
motivated writing this function.
"""

import numpy as np

from boyko_benchmark.dynamics.adaptive import (
    StateTrajectory,
    time_averaged_correlation,
    time_averaged_correlation_magnitude,
)


def test_magnitude_nonzero_where_real_part_is_zero() -> None:
    trajectory = StateTrajectory(states=np.array([[1 + 0j, 0 + 1j]]))

    re_part = time_averaged_correlation(trajectory)
    magnitude = time_averaged_correlation_magnitude(trajectory)

    assert re_part[0, 1] == 0.0
    assert magnitude[0, 1] == 1.0
    assert magnitude[1, 0] == 1.0  # |conj(psi_1)*psi_0| = |-1j| = 1.0 too


def test_magnitude_matches_real_part_when_correlation_is_purely_real() -> None:
    """When psi_i*psi_j is already real (no phase difference), |z|
    should equal |Re(z)| -- sanity check that the two functions agree
    in the non-degenerate case, not just diverge arbitrarily."""
    trajectory = StateTrajectory(states=np.array([[1 + 0j, 0.5 + 0j]]))

    re_part = time_averaged_correlation(trajectory)
    magnitude = time_averaged_correlation_magnitude(trajectory)

    assert magnitude[0, 1] == abs(re_part[0, 1])


def test_magnitude_time_averages_the_complex_value_not_the_magnitude() -> None:
    """`|mean(z)|`, not `mean(|z|)` -- these differ whenever phase
    varies across snapshots. Two snapshots with opposite-sign
    correlation should partially cancel in the mean, not add."""
    # snapshot 1: conj(1)*1j = 1j (magnitude 1)
    # snapshot 2: conj(1)*(-1j) = -1j (magnitude 1)
    # mean(z) = 0 -> |mean(z)| = 0, NOT mean(|z|) = 1
    trajectory = StateTrajectory(states=np.array([[1 + 0j, 0 + 1j], [1 + 0j, 0 - 1j]]))

    magnitude = time_averaged_correlation_magnitude(trajectory)

    assert magnitude[0, 1] == 0.0
