#!/usr/bin/env python
"""V1b (`[A48]`, `null_results/20260814-open-system-geometrogenesis.md`):
the one regime `[A45]`'s REJECT verdict left untested with independent
(AOG-5-compliant) motivation.

`[A47]` proved `W=1` is an absorbing upper barrier and the rule's fixed
point `W* = C_ij/[(rho_i+rho_j)/2]` is only reachable by differential
DECAY from the uniform start. `[A48]` screened three initial-state
regimes for how much edge-to-edge spread `W*` has (cheapest
differentiating test, no adaptation run) and found random-phase
delocalization gives the most (std~0.53) -- more than the localized
state every other experiment in this project has used (std~0.41), and
far more than uniform delocalization (std~0.07, a worse candidate than
the status quo).

This script runs the actual closed-system adaptation (`gamma=sigma=0`,
no open-system machinery needed -- V1b changes the INITIAL STATE, not
the dynamics) with a random-phase delocalized `psi0`, then applies the
exact same structure-vs-null discipline that produced [A41]/[A44]/[A45]:
global weight-shuffle null and strength-stratified null on curvature.
Reports structural excess for THIS regime, comparable to the numbers
already on record for the localized-psi0 regime.

Per AOG-5 / Minimal Relaxation Rule: exactly ONE assumption changed from
every prior experiment in this project (initial state), gamma/sigma/rule/
N/budget all held at their established values.
"""

import sys

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
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


def random_phase_psi0(n_nodes: int, seed: int) -> np.ndarray:
    """`[A48]`'s winning regime: complex Gaussian amplitudes, normalized.
    Every node has nonzero density (unlike localized `psi0`), and phases
    are incoherent across nodes (unlike uniform `psi0`) -- the regime
    [A48] found gives W* the most edge-to-edge spread of the three
    screened."""
    rng = np.random.default_rng(seed)
    vec = rng.normal(size=n_nodes) + 1j * rng.normal(size=n_nodes)
    return vec / np.linalg.norm(vec)


def main() -> int:
    print("=== V1b: random-phase delocalized psi0, gamma=sigma=0 (AOG-5 compliant) ===")
    print(f"N={N_SIZE}, {N_SEEDS} seeds, HebbianAdaptation (unchanged rule)")
    print()
    print(f"{'seed':>4} {'F_real':>10} {'exc_global':>11} {'exc_strat':>11}")

    glob_excess = []
    strat_excess = []
    for seed_index in range(N_SEEDS):
        graph_seed = 1000 * seed_index + N_SIZE
        graph = generate_erdos_renyi(N_SIZE, 3 * N_SIZE, np.random.default_rng(graph_seed))
        psi0 = random_phase_psi0(N_SIZE, seed=graph_seed + 900_000)

        result = run_adaptive_dynamics_open(
            graph,
            psi0,
            HebbianAdaptation(eta=0.1),
            0.05,
            50,
            50,
            backend=ClosedUnitaryBackend(),
            gamma=0.0,
            sigma=0.0,
            noise_seed=None,
        )
        g = result.final_graph
        real = float(forman_ricci_curvature(g).mean())
        e_glob = real - float(forman_ricci_curvature(global_shuffle(g, 900)).mean())
        e_strat = real - float(forman_ricci_curvature(strength_stratified_shuffle(g, 900)).mean())
        glob_excess.append(e_glob)
        strat_excess.append(e_strat)
        print(f"{seed_index:>4} {real:>10.4f} {e_glob:>11.5f} {e_strat:>11.5f}")

    print()
    print("=== Structural excess under V1b (random-phase delocalized) ===")
    g_stat = compute_cell_statistics(np.array(glob_excess))
    s_stat = compute_cell_statistics(np.array(strat_excess))
    g_zero = g_stat.ci_95[0] <= 0.0 <= g_stat.ci_95[1]
    s_zero = s_stat.ci_95[0] <= 0.0 <= s_stat.ci_95[1]
    g_ci = f"({g_stat.ci_95[0]:+.5f},{g_stat.ci_95[1]:+.5f})"
    s_ci = f"({s_stat.ci_95[0]:+.5f},{s_stat.ci_95[1]:+.5f})"
    print(f"  global-shuffle excess     = {g_stat.mean:+.5f} CI={g_ci}  contains 0: {g_zero}")
    print(f"  strength-strat excess     = {s_stat.mean:+.5f} CI={s_ci}  contains 0: {s_zero}")
    print()
    print("Reference, prior regime (localized psi0, from [A43]/[A44]):")
    print("  C0 global excess  = +0.00004 (contains 0)   Csigma global excess = +0.01577")
    print("  C0 strat  excess  = +0.00003 (contains 0)   Csigma strat  excess = +0.01074")
    return 0


if __name__ == "__main__":
    sys.exit(main())
