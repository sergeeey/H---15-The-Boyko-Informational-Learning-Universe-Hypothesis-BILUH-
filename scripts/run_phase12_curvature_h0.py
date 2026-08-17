#!/usr/bin/env python
"""Phase 12 / `[A44]` follow-up: does the curvature structural excess
depend on the REAL pairwise correlations, or would any pairwise rule do?

`[A44]` showed the Forman-Ricci structural excess survives a
node-strength-stratified null (68% retained, d=7.47) — so it is genuine
edge-level structure, not node-strength heterogeneity. But a mundane
explanation remains: `HebbianAdaptation` updates w_ij by the pairwise
correlation C_ij, so it writes pairwise information into the weights BY
CONSTRUCTION. Any shuffle destroys that, guaranteeing a nonzero excess
with no geometric content whatsoever.

The discriminator is the H0 control this project already has:
`CorrelationShuffleAdaptation` (`[A31]`) applies the identical
Oja-normalized update but shuffles the correlation term across edges
first — same magnitude distribution, wrong pairing. Run both at the same
budget and compare curvature structural excess:

    excess(H0) ~= excess(H1)  -> the excess is "a pairwise rule wrote
                                 pairwise numbers", nothing about WHICH
                                 pairs actually correlated. No content.
    excess(H0) <  excess(H1)  -> the real dynamical correlations produce
                                 structure a magnitude-matched shuffle
                                 does not. First positive result of its
                                 kind in this project.

This is Phase 11 Milestone 5's question (`[A37]`, left open with an
ambiguous d=-0.735 on a scalar) re-asked with an observable that has
already proven able to detect edge-level structure.
"""

import sys

import numpy as np

from boyko_benchmark.dynamics.adaptive import (
    AdaptationRule,
    CorrelationShuffleAdaptation,
    HebbianAdaptation,
)
from boyko_benchmark.dynamics.open_dynamics import PhenomenologicalOpenBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.observables.curvature import forman_ricci_curvature
from boyko_benchmark.statistics.cell_statistics import cohens_d, compute_cell_statistics
from boyko_benchmark.types import WeightedGraph

sys.path.insert(0, "scripts")
from run_phase12_strength_null import (  # noqa: E402
    global_shuffle,
    strength_stratified_shuffle,
)

N_SIZE = 512
N_SEEDS = 5


def _run(seed_index: int, rule_name: str) -> WeightedGraph:
    graph_seed = 1000 * seed_index + N_SIZE
    graph = generate_erdos_renyi(N_SIZE, 3 * N_SIZE, np.random.default_rng(graph_seed))
    psi0 = localized_psi0(N_SIZE, source_node=0)
    rule: AdaptationRule
    if rule_name == "H1_real":
        rule = HebbianAdaptation(eta=0.1)
    else:
        rule = CorrelationShuffleAdaptation(
            eta=0.1, rng=np.random.default_rng(graph_seed + 500_000)
        )
    return run_adaptive_dynamics_open(
        graph,
        psi0,
        rule,
        0.05,
        50,
        50,
        backend=PhenomenologicalOpenBackend(),
        gamma=0.0,
        sigma=0.05,
        noise_seed=graph_seed,
    ).final_graph


def main() -> int:
    print("=== Phase 12 / [A44] follow-up: curvature excess, real vs shuffled correlations ===")
    print(f"N={N_SIZE}, {N_SEEDS} seeds, both cells at sigma_tilde=0.05, gamma=0")
    print()
    print(f"{'seed':>4} {'rule':>10} {'F_real':>10} {'exc_global':>11} {'exc_strat':>11}")

    glob: dict[str, list[float]] = {"H1_real": [], "H0_shuffled": []}
    strat: dict[str, list[float]] = {"H1_real": [], "H0_shuffled": []}

    for seed_index in range(N_SEEDS):
        for rule_name in ("H1_real", "H0_shuffled"):
            graph = _run(seed_index, rule_name)
            real = float(forman_ricci_curvature(graph).mean())
            g = real - float(forman_ricci_curvature(global_shuffle(graph, 900)).mean())
            s = real - float(forman_ricci_curvature(strength_stratified_shuffle(graph, 900)).mean())
            glob[rule_name].append(g)
            strat[rule_name].append(s)
            print(f"{seed_index:>4} {rule_name:>10} {real:>10.4f} {g:>11.5f} {s:>11.5f}")

    print()
    print("=== Does the real correlation structure matter? ===")
    for key, label in (("glob", "global-shuffle"), ("strat", "strength-stratified")):
        source = glob if key == "glob" else strat
        h1 = compute_cell_statistics(np.array(source["H1_real"]))
        h0 = compute_cell_statistics(np.array(source["H0_shuffled"]))
        d = cohens_d(np.array(source["H1_real"]), np.array(source["H0_shuffled"]))
        overlap = not (h1.ci_95[0] > h0.ci_95[1] or h0.ci_95[0] > h1.ci_95[1])
        mcid = abs(d) >= 0.8 and not overlap
        print(f"  excess vs {label} null:")
        h1_ci = f"({h1.ci_95[0]:+.5f},{h1.ci_95[1]:+.5f})"
        h0_ci = f"({h0.ci_95[0]:+.5f},{h0.ci_95[1]:+.5f})"
        print(f"      H1 (real correlations)     = {h1.mean:+.5f} CI={h1_ci}")
        print(f"      H0 (shuffled correlations) = {h0.mean:+.5f} CI={h0_ci}")
        print(f"      d(H1 vs H0) = {d:+.3f}   CI overlap: {overlap}   MCID met: {mcid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
