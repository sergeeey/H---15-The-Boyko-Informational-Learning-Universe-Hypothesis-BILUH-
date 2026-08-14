#!/usr/bin/env python
"""Phase 11 open-system pilot runner (TZ Section 21's proposed file
layout: open_config.py + configs/open_pilot.yaml + this script).

Runs the C0/Cgamma/Csigma/Cgammasigma factorial cells (TZ Section 10) on
Active (Erdos-Renyi) graphs, using the diagnostic package built this
session: G1 plateau (spectral_dimension.detect_plateau), D_W
(trajectory_divergence.weight_trajectory_magnitude), D_OC
(open_vs_closed_divergence), conductance, and modularity.

RESOLVED STATUS ([A35], docs/assumptions.md, 2026-08-14): the pilot's own
T7 test found that gamma_tilde=0.05 (the only nonzero level in
configs/open_pilot.yaml) nearly freezes Hebbian weight movement. The user
explicitly chose option (c): proceed with this gamma_tilde AS IS and
treat a near-zero D_W / no-separation-from-C0 result as itself
informative (OPEN_DYNAMICS_NO_EFFECT, ТЗ §16), not as a reason to
re-parameterize after the fact.

Default mode is --dry-run: prints the full cell/size/seed plan and the
[A35] resolution note, runs nothing. Pass --run to actually execute.

Writes each (size, seed, cell) result to
results/open_pilot/raw.jsonl incrementally; re-running skips points
already present (same resumability pattern as run_kappa_eta_sweep.py).
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.open_config import OpenPilotConfig
from boyko_benchmark.dynamics.open_dynamics import PhenomenologicalOpenBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.open_provenance import (
    collect_open_pilot_provenance,
    provenance_to_dict,
)
from boyko_benchmark.experiment.runner import AdaptiveRunResult, localized_psi0
from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.observables.conductance import modularity, spectral_conductance
from boyko_benchmark.observables.spectral_dimension import detect_plateau, spectral_dimension
from boyko_benchmark.observables.trajectory_divergence import (
    open_vs_closed_divergence,
    weight_trajectory_magnitude,
)
from boyko_benchmark.types import WeightedGraph

CONFIG_PATH = Path("configs/open_pilot.yaml")
OUTPUT_DIR = Path("results/open_pilot")
RAW_OUTPUT_PATH = OUTPUT_DIR / "raw.jsonl"

_A35_WARNING = """
[A35] RESOLVED (docs/assumptions.md, 2026-08-14): user chose option (c)
-- proceed with gamma_tilde=0.05 AS IS. gamma_tilde=0.05 was found to
nearly freeze Hebbian weight movement on both the lattice (T7) and
Active, so a near-zero D_W / no-separation-from-C0 result here is
EXPECTED and must be read as "gamma=0.1 suppressed adaptation before
openness could act" (OPEN_DYNAMICS_NO_EFFECT), not as "openness cannot
create geometric organization" -- those are different claims.
""".strip()


def _cells(config: OpenPilotConfig) -> dict[str, tuple[float, float]]:
    gamma_tildes = config.open_dynamics.gamma_tilde_levels
    sigma_tildes = config.open_dynamics.sigma_tilde_levels
    gamma = gamma_tildes[0] * config.open_dynamics.omega_ref if gamma_tildes else 0.0
    sigma = sigma_tildes[0] if sigma_tildes else 0.0
    return {
        "C0": (0.0, 0.0),
        "Cgamma": (gamma, 0.0),
        "Csigma": (0.0, sigma),
        "Cgammasigma": (gamma, sigma),
    }


def _load_completed_points() -> set[tuple[int, int, str]]:
    if not RAW_OUTPUT_PATH.exists():
        return set()
    completed = set()
    with open(RAW_OUTPUT_PATH, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            completed.add((record["size"], record["seed_index"], record["cell"]))
    return completed


def _closed_baseline(
    config: OpenPilotConfig, graph: WeightedGraph, psi0: np.ndarray
) -> AdaptiveRunResult:
    """Runs ClosedUnitaryBackend once. C0's own cell reuses this result
    directly; every other cell needs it only as the D_OC reference -- NOT
    recomputed per cell (that was 4x redundant closed-dynamics compute
    per seed before this fix, ~half the pilot's N=512 wall-clock cost per
    the timing smoke test)."""
    return run_adaptive_dynamics_open(
        graph,
        psi0,
        HebbianAdaptation(eta=config.pilot.eta),
        config.pilot.dt,
        config.pilot.k,
        config.pilot.dtau_steps,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )


def _run_one_point(
    config: OpenPilotConfig,
    size: int,
    seed_index: int,
    cell_name: str,
    gamma: float,
    sigma: float,
    t_values: np.ndarray,
    graph: WeightedGraph,
    psi0: np.ndarray,
    closed_result: AdaptiveRunResult,
) -> dict[str, object]:
    graph_seed = 1000 * seed_index + size
    noise_seed = graph_seed if sigma > 0.0 else None

    start = time.perf_counter()
    if gamma == 0.0 and sigma == 0.0:
        result = closed_result
    else:
        result = run_adaptive_dynamics_open(
            graph,
            psi0,
            HebbianAdaptation(eta=config.pilot.eta),
            config.pilot.dt,
            config.pilot.k,
            config.pilot.dtau_steps,
            backend=PhenomenologicalOpenBackend(),
            gamma=gamma,
            sigma=sigma,
            noise_seed=noise_seed,
        )
    elapsed = time.perf_counter() - start

    laplacian_after = normalized_laplacian(result.final_graph)
    d_s_values = spectral_dimension(laplacian_after, t_values)
    plateau = detect_plateau(t_values, d_s_values)

    provenance = collect_open_pilot_provenance(
        config=config.model_dump(),
        graph_seed=graph_seed,
        initial_state_seed=None,
        noise_seed=noise_seed,
        control_seed=None,
    )

    return {
        "size": size,
        "seed_index": seed_index,
        "cell": cell_name,
        "gamma": gamma,
        "sigma": sigma,
        "elapsed_s": elapsed,
        "d_s_hat": plateau.d_s_hat,
        "converged": plateau.converged,
        "d_w": weight_trajectory_magnitude(result.final_graph.weights, graph.weights),
        "d_oc": open_vs_closed_divergence(
            result.final_graph.weights, closed_result.final_graph.weights
        ),
        "conductance": spectral_conductance(result.final_graph),
        "modularity": modularity(result.final_graph),
        **provenance_to_dict(provenance),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument(
        "--run",
        action="store_true",
        help="Actually execute the pilot. Without this flag, only the plan is printed.",
    )
    args = parser.parse_args()

    config = OpenPilotConfig.from_yaml(args.config)
    cells = _cells(config)
    grid = [
        (size, seed_index, cell_name)
        for size in config.sizes
        for seed_index in range(config.seeds_per_cell)
        for cell_name in cells
    ]

    print("=== Phase 11 open pilot ===")
    print(f"config: {args.config}")
    print(f"sizes: {config.sizes}, seeds_per_cell: {config.seeds_per_cell}, cells: {list(cells)}")
    print(f"total points: {len(grid)}")
    print()
    print(_A35_WARNING)
    print()

    if not args.run:
        print("Dry run only (pass --run to execute). No points were computed.")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    t_values = np.geomspace(0.1, 10.0, num=12)
    completed = _load_completed_points()
    remaining = [p for p in grid if p not in completed]
    remaining_seeds = sorted({(size, seed_index) for size, seed_index, _ in remaining})

    print(f"executing: {len(remaining)} remaining of {len(grid)} total points")
    point_counter = 0
    with open(RAW_OUTPUT_PATH, "a", encoding="utf-8") as f:
        for size, seed_index in remaining_seeds:
            seed_cells = [c for s, i, c in remaining if s == size and i == seed_index]
            graph_seed = 1000 * seed_index + size
            rng = np.random.default_rng(graph_seed)
            graph = generate_erdos_renyi(n_nodes=size, n_edges=3 * size, rng=rng)
            psi0 = localized_psi0(size, source_node=0)
            closed_start = time.perf_counter()
            closed_result = _closed_baseline(config, graph, psi0)
            print(
                f"size={size} seed={seed_index}: closed baseline "
                f"{time.perf_counter() - closed_start:.1f}s"
            )

            for cell_name in seed_cells:
                point_counter += 1
                gamma, sigma = cells[cell_name]
                print(
                    f"[{point_counter}/{len(remaining)}] size={size} seed={seed_index} "
                    f"cell={cell_name} ...",
                    end=" ",
                    flush=True,
                )
                record = _run_one_point(
                    config,
                    size,
                    seed_index,
                    cell_name,
                    gamma,
                    sigma,
                    t_values,
                    graph,
                    psi0,
                    closed_result,
                )
                f.write(json.dumps(record, default=str) + "\n")
                f.flush()
                elapsed_s, d_s_hat, d_w = record["elapsed_s"], record["d_s_hat"], record["d_w"]
                print(f"{elapsed_s:.1f}s d_s_hat={d_s_hat:.3f} d_w={d_w:.4f}")

    print()
    print(f"Full raw results: {RAW_OUTPUT_PATH}")
    print("Reminder: gamma=0.1 is expected to suppress D_W ([A35]) -- a near-zero")
    print("separation from C0 means OPEN_DYNAMICS_NO_EFFECT at this gamma, not that")
    print("openness cannot create geometric organization in general.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
