"""Reduces one (arm, N) cell's per-seed Gate-A observables (Cycle 21) into
per-observable `CellStatistics` (mathematical_contract.md Sec7).

G2/G3/G4 are already per-replicate scalars. G1 and G5 are arrays and need
a documented scalar reduction before they can be fed through Phase 7's
statistics machinery:
- G1: the LAST value of the caller-supplied `t_values` calibration grid --
  a provisional plateau estimate. Proper plateau detection is future work
  (see gate_a_observables.py's own scope note); this is not it.
- G5: `v_eff` from a full-window linear fit (Phase 6's `fit_effective_
  velocity`), not an auto-detected unsaturated-only window -- same
  "caller-supplied window, no auto-detection" scoping as Phase 6 itself.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.config import Arm
from boyko_benchmark.experiment.gate_a_observables import compute_gate_a_observables
from boyko_benchmark.experiment.orchestrator import ReplicateResult
from boyko_benchmark.observables.propagation_front import fit_effective_velocity
from boyko_benchmark.statistics.cell_statistics import CellStatistics, compute_cell_statistics

IS_L_DRIVEN_BY_ARM: dict[Arm, bool] = {
    Arm.ACTIVE: False,
    Arm.FROZEN: False,
    Arm.PARAMETER_MATCHED_RANDOM: False,
    Arm.TOPOLOGY_SCRAMBLED: False,
    Arm.FIXED_FLAT_GEOMETRY: False,
    Arm.ALTERNATIVE_OBJECTIVE: False,
    Arm.CLASSICAL_DIFFUSION_CONTROL: True,
}
"""Operator-Matching Rule (mathematical_contract.md Sec5): every arm's own
dynamics operator, except Arm CD's classical L-driven carrier. The
Operator-Independence Diagnostic (a separate rerun, not one of these seven
arms) is always L-driven -- handled by its own caller, not this table."""


@dataclass(frozen=True)
class CellObservableStatistics:
    g1: CellStatistics
    g2: CellStatistics
    g3: CellStatistics
    g4: CellStatistics
    g5_v_eff: CellStatistics


def reduce_g1(g1_array: NDArray[np.floating]) -> float:
    return float(g1_array[-1])


def reduce_g5(g5_array: NDArray[np.int64], dt: float) -> float:
    times = np.arange(len(g5_array)) * dt
    fit = fit_effective_velocity(times, g5_array.astype(float), fit_window=(0, len(g5_array)))
    return fit.v_eff


def collect_observable_samples(
    replicates: tuple[ReplicateResult, ...],
    arm: Arm,
    dt: float,
    t_values: NDArray[np.floating],
    q: float,
) -> dict[str, NDArray[np.floating]]:
    """Raw per-seed sample arrays for one (arm, N) cell, one array per
    observable name ("g1".."g5") -- shared by `aggregate_cell` (per-cell
    statistics) and G6's cross-arm wiring (Phase 10), so the collection
    logic exists exactly once."""
    is_l_driven = IS_L_DRIVEN_BY_ARM[arm]
    samples: dict[str, list[float]] = {"g1": [], "g2": [], "g3": [], "g4": [], "g5": []}
    for replicate in replicates:
        arm_result = replicate.arm_results[arm]
        observables = compute_gate_a_observables(arm_result, is_l_driven, t_values, q)
        samples["g1"].append(reduce_g1(observables.g1_spectral_dimension))
        samples["g2"].append(observables.g2_laplacian_gap)
        samples["g3"].append(observables.g3_resistance_diameter)
        samples["g4"].append(observables.g4_ipr)
        samples["g5"].append(reduce_g5(observables.g5_propagation_front, dt))
    return {name: np.array(values) for name, values in samples.items()}


def aggregate_cell(
    replicates: tuple[ReplicateResult, ...],
    arm: Arm,
    dt: float,
    t_values: NDArray[np.floating],
    q: float,
) -> CellObservableStatistics:
    """One (arm, N) cell's statistics across `replicates` (all sharing the
    same N, one per seed)."""
    samples = collect_observable_samples(replicates, arm, dt, t_values, q)
    return CellObservableStatistics(
        g1=compute_cell_statistics(samples["g1"]),
        g2=compute_cell_statistics(samples["g2"]),
        g3=compute_cell_statistics(samples["g3"]),
        g4=compute_cell_statistics(samples["g4"]),
        g5_v_eff=compute_cell_statistics(samples["g5"]),
    )
