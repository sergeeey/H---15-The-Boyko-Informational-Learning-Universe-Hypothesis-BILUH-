"""Top-level entry point: runs the full Gate-A pipeline for one config,
producing a `PhaseResult` with the Stage-1 verdict and full provenance
(CLAUDE.md Reproducibility section).

sweep -> per-(arm,N) cell statistics -> G1-G6 -> verdict, all in one call.

**Simplifications, documented not silent (not final production design):**
- G2/G3/G4 regress each size's Active MEAN value (from `cell_
  aggregation.aggregate_cell`) against N -- with only 2-3 configured
  sizes (e.g. smoke.yaml's 2), this is enough points to exercise the
  regression machinery but far short of `mathematical_contract.md` Sec6's
  production floor (>=5 sizes).
- G5 is evaluated on the largest-N, first-seed Active replicate's `[A27]`
  multi-source average (`g5_multisource.compute_g5_multisource`, probes
  the FINAL adapted graph with a fresh pulse per stored source node) --
  not averaged across SEEDS, only across the sources within one seed.
  `n_steps = dtau_steps * K` matches the adaptation run's own total
  length, so the resulting r_q(t) axis is directly comparable to the
  single-source measurement it replaced.
- G1's convergence check needs >=2 sizes (`check_finite_size_convergence`
  raises otherwise) -- documented, not silently caught.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.config import Arm, ExperimentConfig
from boyko_benchmark.experiment.cell_aggregation import CellObservableStatistics, aggregate_cell
from boyko_benchmark.experiment.g5_multisource import compute_g5_multisource
from boyko_benchmark.experiment.g6_wiring import build_g6_samples
from boyko_benchmark.experiment.provenance import (
    EnvironmentProvenance,
    collect_environment_provenance,
)
from boyko_benchmark.experiment.sweep import run_sweep
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.observables.propagation_front import fit_effective_velocity
from boyko_benchmark.phase_gates import (
    ExponentGateResult,
    G1Result,
    G3Result,
    G5Result,
    G6Result,
    StageOneVerdict,
    compute_verdict,
    evaluate_g1,
    evaluate_g2,
    evaluate_g3,
    evaluate_g4,
    evaluate_g5,
    evaluate_g6,
)
from boyko_benchmark.statistics.finite_size_scaling import SizeEstimate


@dataclass(frozen=True)
class PhaseResult:
    verdict: StageOneVerdict
    g1: G1Result
    g2: ExponentGateResult
    g3: G3Result
    g4: ExponentGateResult
    g5: G5Result
    g6: G6Result
    cell_statistics: dict[tuple[Arm, int], CellObservableStatistics]
    provenance: EnvironmentProvenance
    sizes: tuple[int, ...]


def run_phase(config: ExperimentConfig, t_values: NDArray[np.floating], q: float) -> PhaseResult:
    provenance = collect_environment_provenance()
    sweep = run_sweep(config)
    sizes = tuple(sorted(sweep.replicates_by_size.keys()))
    dt = config.fast_dynamics.dt

    cell_statistics: dict[tuple[Arm, int], CellObservableStatistics] = {}
    for n_nodes in sizes:
        replicates = sweep.replicates_by_size[n_nodes]
        for arm in config.arms:
            cell_statistics[(arm, n_nodes)] = aggregate_cell(replicates, arm, dt, t_values, q)

    g1_estimates = [
        SizeEstimate(
            size=n_nodes,
            mean=cell_statistics[(Arm.ACTIVE, n_nodes)].g1.mean,
            ci_95=cell_statistics[(Arm.ACTIVE, n_nodes)].g1.ci_95,
        )
        for n_nodes in sizes
    ]
    g1 = evaluate_g1(g1_estimates)

    sizes_array = np.array(sizes, dtype=float)
    g2_values = np.array([cell_statistics[(Arm.ACTIVE, n)].g2.mean for n in sizes])
    g2 = evaluate_g2(sizes_array, g2_values)

    g3_values = np.array([cell_statistics[(Arm.ACTIVE, n)].g3.mean for n in sizes])
    g3 = evaluate_g3(sizes_array, g3_values)

    g4_values = np.array([cell_statistics[(Arm.ACTIVE, n)].g4.mean for n in sizes])
    g4 = evaluate_g4(sizes_array, g4_values)

    largest_n = sizes[-1]
    first_seed_active = sweep.replicates_by_size[largest_n][0].arm_results[Arm.ACTIVE]
    n_steps = config.adaptation.dtau_steps * config.adaptation.K
    g5_mean, _g5_std = compute_g5_multisource(
        first_seed_active,
        laplacian_fn=normalized_laplacian,
        is_classical=False,
        dt=dt,
        n_steps=n_steps,
        q=q,
    )
    g5_times = np.arange(len(g5_mean)) * dt
    g5_fit = fit_effective_velocity(g5_times, g5_mean, fit_window=(0, len(g5_mean)))
    g5 = evaluate_g5(g5_fit)

    g6_cells = build_g6_samples(sweep, dt, t_values, q)
    g6 = evaluate_g6(g6_cells)

    verdict = compute_verdict(g1, g2, g3, g4, g5, g6)

    return PhaseResult(
        verdict=verdict,
        g1=g1,
        g2=g2,
        g3=g3,
        g4=g4,
        g5=g5,
        g6=g6,
        cell_statistics=cell_statistics,
        provenance=provenance,
        sizes=sizes,
    )
