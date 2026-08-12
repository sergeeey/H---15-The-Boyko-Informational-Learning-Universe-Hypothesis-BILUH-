"""Wires Active's per-seed observable samples against each of Frozen/
Parameter-Matched Random/Topology Scrambled, ready for `phase_gates.
evaluate_g6`.

[A26]: evaluated at the LARGEST size in the FSS grid only, not pooled
across sizes -- G1-G5's raw values are N-dependent by design (that is
what G2/G3/G4's exponents measure), so pooling different sizes' samples
into one comparison would conflate genuine finite-size scaling with the
arm-vs-arm separation G6 is trying to detect.
"""

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.config import Arm
from boyko_benchmark.experiment.cell_aggregation import collect_observable_samples
from boyko_benchmark.experiment.sweep import SweepResult

G6_COMPARATOR_ARMS: tuple[Arm, ...] = (
    Arm.FROZEN,
    Arm.PARAMETER_MATCHED_RANDOM,
    Arm.TOPOLOGY_SCRAMBLED,
)
"""falsification_gates.md: Active vs each of these three -- Arm E, F, CD
are explicitly NOT G6 negative controls (see that doc's own text)."""

OBSERVABLE_NAMES: tuple[str, ...] = ("g1", "g2", "g3", "g4", "g5")


def build_g6_samples(
    sweep: SweepResult, dt: float, t_values: NDArray[np.floating], q: float
) -> dict[tuple[str, str], tuple[NDArray[np.floating], NDArray[np.floating]]]:
    """15 cells: (observable, comparator_arm_value) -> (active_samples,
    comparator_samples), ready for `phase_gates.evaluate_g6`."""
    largest_n = max(sweep.replicates_by_size.keys())
    replicates = sweep.replicates_by_size[largest_n]

    active_samples = collect_observable_samples(replicates, Arm.ACTIVE, dt, t_values, q)

    cells: dict[tuple[str, str], tuple[NDArray[np.floating], NDArray[np.floating]]] = {}
    for comparator_arm in G6_COMPARATOR_ARMS:
        comparator_samples = collect_observable_samples(replicates, comparator_arm, dt, t_values, q)
        for observable_name in OBSERVABLE_NAMES:
            cells[(observable_name, comparator_arm.value)] = (
                active_samples[observable_name],
                comparator_samples[observable_name],
            )
    return cells
