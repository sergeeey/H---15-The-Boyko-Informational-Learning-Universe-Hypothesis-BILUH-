#!/usr/bin/env python
"""V1 (`null_results/20260814-open-system-geometrogenesis.md`): does a
STRUCTURALLY DIFFERENT adaptation rule produce organization where
`HebbianAdaptation` did not?

`AlternativeObjective` (`[A4]`) is the best-motivated V1 candidate of the
two alternative rules already in the codebase:

- `AntiHebbianAdaptation` is already documented in its own docstring as
  "decay toward the non-negativity floor... a different, already-bounded
  pathology" -- re-running it would reproduce a known, pre-characterized
  decay pathology rather than test anything new. Skipped for that reason,
  not silently.
- `AlternativeObjective` is mechanistically opposite to everything tested
  so far: `dW_ij/dtau = eta*(rho_i+rho_j)/2`, PURE density-driven
  reinforcement with NO decay term and NO correlation/phase information
  at all. `_masked_nonnegative` only floors at 0 -- there is no ceiling
  analogous to `[A47]`'s theorem, so this rule can differentiate edges by
  GROWTH, the one direction Hebbian's rule structurally cannot reach.
  Sanity-checked first: after 50 windows, weights stay finite and grow
  modestly (mean ~1.01x, max ~1.07x of the uniform 1.0 start) -- no
  blowup.

Same discipline as [A41]/[A44]/[A49]: closed dynamics, localized psi0
(matching every prior baseline for direct comparability), N=512, 5
seeds, curvature structural excess under both the global weight-shuffle
null and the strength-stratified null.
"""

import sys

import numpy as np

from boyko_benchmark.dynamics.adaptive import AlternativeObjective
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.observables.curvature import forman_ricci_curvature
from boyko_benchmark.statistics.cell_statistics import compute_cell_statistics

sys.path.insert(0, "scripts")
from run_phase12_strength_null import (  # noqa: E402
    global_shuffle,
    strength_stratified_shuffle,
)

N_SIZE = 512
N_SEEDS = 5


def main() -> int:
    print("=== V1: AlternativeObjective (pure density-driven growth, no decay/correlation) ===")
    print(f"N={N_SIZE}, {N_SEEDS} seeds, closed dynamics, localized psi0 (baseline-comparable)")
    print()
    header = f"{'seed':>4} {'F_real':>10} {'mean_w':>8} {'max_w':>8} "
    header += f"{'exc_global':>11} {'exc_strat':>11}"
    print(header)

    glob_excess = []
    strat_excess = []
    for seed_index in range(N_SEEDS):
        graph_seed = 1000 * seed_index + N_SIZE
        graph = generate_erdos_renyi(N_SIZE, 3 * N_SIZE, np.random.default_rng(graph_seed))
        psi0 = localized_psi0(N_SIZE, source_node=0)

        result = run_adaptive_dynamics_open(
            graph,
            psi0,
            AlternativeObjective(eta=0.1),
            0.05,
            50,
            50,
            backend=ClosedUnitaryBackend(),
            gamma=0.0,
            sigma=0.0,
            noise_seed=None,
        )
        g = result.final_graph
        w = g.weights[np.triu(g.mask)]
        real = float(forman_ricci_curvature(g).mean())
        e_glob = real - float(forman_ricci_curvature(global_shuffle(g, 900)).mean())
        e_strat = real - float(forman_ricci_curvature(strength_stratified_shuffle(g, 900)).mean())
        glob_excess.append(e_glob)
        strat_excess.append(e_strat)
        print(
            f"{seed_index:>4} {real:>10.4f} {w.mean():>8.4f} {w.max():>8.4f} "
            f"{e_glob:>11.5f} {e_strat:>11.5f}"
        )

    print()
    print("=== Structural excess under V1 (AlternativeObjective) ===")
    g_stat = compute_cell_statistics(np.array(glob_excess))
    s_stat = compute_cell_statistics(np.array(strat_excess))
    g_zero = g_stat.ci_95[0] <= 0.0 <= g_stat.ci_95[1]
    s_zero = s_stat.ci_95[0] <= 0.0 <= s_stat.ci_95[1]
    g_ci = f"({g_stat.ci_95[0]:+.5f},{g_stat.ci_95[1]:+.5f})"
    s_ci = f"({s_stat.ci_95[0]:+.5f},{s_stat.ci_95[1]:+.5f})"
    print(f"  global-shuffle excess     = {g_stat.mean:+.5f} CI={g_ci}  contains 0: {g_zero}")
    print(f"  strength-strat excess     = {s_stat.mean:+.5f} CI={s_ci}  contains 0: {s_zero}")
    print()
    print("Reference, HebbianAdaptation (localized psi0, from [A43]/[A44]):")
    print("  C0 global excess = +0.00004 (contains 0)   strat excess = +0.00003 (contains 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
