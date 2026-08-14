#!/usr/bin/env python
"""Milestone 5 (TZ Section 21's "dynamic control arms, only if Milestone
3-4 show a signal"): H0 secondary control for the Cσ modularity finding
recorded in docs/assumptions.md [A37].

[A37] found Cσ's modularity increase (open dynamics, sigma_tilde=0.05,
gamma=0) survives a negative control (the raw ER graph's own modularity
floor) -- MCID-significant vs both C0 and that floor. What is not yet
known: whether this reflects the REAL correlation structure the noisy
quantum dynamics builds (H1), or whether ANY noise-following adaptation
rule with the same correlation-magnitude distribution would produce the
same shift regardless of which node pairs actually correlated (H0,
CorrelationShuffleAdaptation, [A31]).

Runs the same pilot budget (N=512, K=50, dt=0.05, dtau_steps=50, eta=0.1,
sigma_tilde=0.05, gamma=0), same 5 graph seeds as configs/open_pilot.yaml,
but with CorrelationShuffleAdaptation instead of HebbianAdaptation, and
reports modularity/conductance/D_W against [A37]'s already-recorded real-
Hebbian numbers.
"""

import sys
import time
from pathlib import Path

import numpy as np

from boyko_benchmark.dynamics.adaptive import CorrelationShuffleAdaptation
from boyko_benchmark.dynamics.open_config import OpenPilotConfig
from boyko_benchmark.dynamics.open_dynamics import PhenomenologicalOpenBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.observables.conductance import modularity, spectral_conductance
from boyko_benchmark.observables.trajectory_divergence import weight_trajectory_magnitude
from boyko_benchmark.statistics.cell_statistics import cohens_d, compute_cell_statistics

CONFIG_PATH = Path("configs/open_pilot.yaml")
SIGMA_TILDE = 0.05
N_SIZE = 512
SEEDS = 5

# [A37]'s already-recorded real-Hebbian Csigma numbers, for direct comparison.
REAL_HEBBIAN_MODULARITY = np.array([0.419, 0.415, 0.428, 0.424, 0.422])
REAL_HEBBIAN_CONDUCTANCE = np.array([0.600, 0.594, 0.491, 0.522, 0.499])


def main() -> int:
    config = OpenPilotConfig.from_yaml(CONFIG_PATH)
    modularities = []
    conductances = []
    d_ws = []

    for seed_index in range(SEEDS):
        graph_seed = 1000 * seed_index + N_SIZE
        rng = np.random.default_rng(graph_seed)
        graph = generate_erdos_renyi(n_nodes=N_SIZE, n_edges=3 * N_SIZE, rng=rng)
        psi0 = localized_psi0(N_SIZE, source_node=0)
        shuffle_rng = np.random.default_rng(graph_seed + 500_000)
        adaptation = CorrelationShuffleAdaptation(eta=config.pilot.eta, rng=shuffle_rng)

        start = time.perf_counter()
        result = run_adaptive_dynamics_open(
            graph,
            psi0,
            adaptation,
            config.pilot.dt,
            config.pilot.k,
            config.pilot.dtau_steps,
            backend=PhenomenologicalOpenBackend(),
            gamma=0.0,
            sigma=SIGMA_TILDE,
            noise_seed=graph_seed,
        )
        elapsed = time.perf_counter() - start

        mod = modularity(result.final_graph)
        cond = spectral_conductance(result.final_graph)
        d_w = weight_trajectory_magnitude(result.final_graph.weights, graph.weights)
        modularities.append(mod)
        conductances.append(cond)
        d_ws.append(d_w)
        print(
            f"[{seed_index + 1}/{SEEDS}] {elapsed:.1f}s modularity={mod:.4f} "
            f"conductance={cond:.4f} d_w={d_w:.4f}"
        )

    mod_arr = np.array(modularities)
    cond_arr = np.array(conductances)
    mod_stat = compute_cell_statistics(mod_arr)
    cond_stat = compute_cell_statistics(cond_arr)
    real_mod_stat = compute_cell_statistics(REAL_HEBBIAN_MODULARITY)
    real_cond_stat = compute_cell_statistics(REAL_HEBBIAN_CONDUCTANCE)

    print()
    print("=== H0 (shuffled correlation) vs H1 (real Hebbian correlation), Csigma cell ===")
    print(f"H0 modularity:   mean={mod_stat.mean:.4f} CI={mod_stat.ci_95}")
    print(f"H1 modularity:   mean={real_mod_stat.mean:.4f} CI={real_mod_stat.ci_95}")
    d_mod = cohens_d(mod_arr, REAL_HEBBIAN_MODULARITY)
    overlap_mod = not (
        mod_stat.ci_95[0] > real_mod_stat.ci_95[1] or real_mod_stat.ci_95[0] > mod_stat.ci_95[1]
    )
    print(f"d(H0 vs H1) modularity = {d_mod:.3f}, CI_overlap={overlap_mod}")
    print()
    print(f"H0 conductance:  mean={cond_stat.mean:.4f} CI={cond_stat.ci_95}")
    print(f"H1 conductance:  mean={real_cond_stat.mean:.4f} CI={real_cond_stat.ci_95}")
    d_cond = cohens_d(cond_arr, REAL_HEBBIAN_CONDUCTANCE)
    overlap_cond = not (
        cond_stat.ci_95[0] > real_cond_stat.ci_95[1] or real_cond_stat.ci_95[0] > cond_stat.ci_95[1]
    )
    print(f"d(H0 vs H1) conductance = {d_cond:.3f}, CI_overlap={overlap_cond}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
