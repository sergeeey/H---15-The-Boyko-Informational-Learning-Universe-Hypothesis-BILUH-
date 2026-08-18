"""M2 (`docs/v4_spec.md` Sec7): K1's primary endpoint, `R_edge` --
of the specific lattice edges a corruption actually removed, what
fraction does V4's regrowth rule restore. Corrected 2026-08-18 (see
`docs/v4_spec.md` Sec7's dated note): the numerator counts overlap with
`E_damaged_out` specifically, not with the full original edge set --
a graph that changes nothing about the damaged edges but happens to
keep every undamaged edge must score 0, not near-1.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Edge = tuple[int, int]


@dataclass(frozen=True)
class EdgeRecoveryResult:
    r_edge: float
    wrong_removal_rate: float


def compute_edge_recovery(
    original_edges: frozenset[Edge],
    damaged_out: frozenset[Edge],
    recovered_mask: NDArray[np.bool_],
) -> EdgeRecoveryResult:
    """`damaged_out` must be non-empty (a K1 run with zero actual damage
    is not a valid gate input) and `original_edges` must be a superset
    of it, matching `corrupt_lattice_edges`'s own contract."""
    if not damaged_out:
        raise ValueError("compute_edge_recovery: damaged_out is empty -- no damage to score.")

    recovered_edges = frozenset((int(i), int(j)) for i, j in np.argwhere(np.triu(recovered_mask)))
    r_edge = len(damaged_out & recovered_edges) / len(damaged_out)

    undamaged_edges = original_edges - damaged_out
    wrongly_removed = undamaged_edges - recovered_edges
    wrong_removal_rate = len(wrongly_removed) / len(undamaged_edges) if undamaged_edges else 0.0

    return EdgeRecoveryResult(r_edge=r_edge, wrong_removal_rate=wrong_removal_rate)
