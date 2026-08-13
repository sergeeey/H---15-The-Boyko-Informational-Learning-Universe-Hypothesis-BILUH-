#!/usr/bin/env python
"""Runs the frozen [A9] (K, eta) robustness/no-collapse sweep
(docs/assumptions.md [A9] entry) using configs/kappa_eta_sweep.yaml as the
base config, overriding adaptation.K/adaptation.eta for each of the 25
frozen grid points.

This is NOT a Stage-1 verdict search. Per [A9]'s frozen decision rule:
look for a broad plateau of (K, eta) where Active's G1-G5 raw values are
stable (low seed-to-seed variance, no NaN/divergence) -- not the single
point that maximizes any gate's pass rate. Do not report a "best" (K, eta)
here; report the stability landscape.

Writes each point's result to `results/kappa_eta_sweep/raw.jsonl`
incrementally (one JSON line per point, flushed immediately) so a
long-running sweep survives an interruption without losing completed
points -- re-running skips points already present in that file.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

from boyko_benchmark.config import AdaptationSection, Arm, ExperimentConfig
from boyko_benchmark.experiment.phase_runner import run_phase
from boyko_benchmark.statistics.cell_statistics import CellStatistics

K_GRID = [10, 25, 50, 100, 200]
ETA_GRID = [0.02, 0.05, 0.1, 0.2, 0.4]

BASE_CONFIG_PATH = Path("configs/kappa_eta_sweep.yaml")
OUTPUT_DIR = Path("results/kappa_eta_sweep")
RAW_OUTPUT_PATH = OUTPUT_DIR / "raw.jsonl"


def _load_completed_points() -> set[tuple[int, float]]:
    if not RAW_OUTPUT_PATH.exists():
        return set()
    completed = set()
    with open(RAW_OUTPUT_PATH, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            completed.add((record["K"], record["eta"]))
    return completed


def _cell_stats_to_dict(stats: CellStatistics) -> dict[str, float | list[float]]:
    return {"mean": stats.mean, "std": stats.std, "ci_95": list(stats.ci_95)}


def _run_one_point(
    base_config: ExperimentConfig, k: int, eta: float, t_values: np.ndarray, q: float
) -> dict[str, object]:
    config = base_config.model_copy(
        update={
            "adaptation": AdaptationSection(
                eta=eta, K=k, dtau_steps=base_config.adaptation.dtau_steps
            )
        }
    )
    start = time.perf_counter()
    result = run_phase(config, t_values=t_values, q=q)
    elapsed = time.perf_counter() - start

    per_size: dict[str, dict[str, object]] = {}
    any_nonfinite = False
    for n_nodes in result.sizes:
        cell = result.cell_statistics[(Arm.ACTIVE, n_nodes)]
        entry = {
            "g1": _cell_stats_to_dict(cell.g1),
            "g1_converged_fraction": cell.g1_converged_fraction,
            "g2": _cell_stats_to_dict(cell.g2),
            "g3": _cell_stats_to_dict(cell.g3),
            "g4": _cell_stats_to_dict(cell.g4),
            "g5_v_eff": _cell_stats_to_dict(cell.g5_v_eff),
        }
        per_size[str(n_nodes)] = entry
        for gate in (cell.g1, cell.g2, cell.g3, cell.g4, cell.g5_v_eff):
            if not np.isfinite(gate.mean) or not np.isfinite(gate.std):
                any_nonfinite = True

    return {
        "K": k,
        "eta": eta,
        "elapsed_s": elapsed,
        "verdict": result.verdict.value,
        "per_size_active": per_size,
        "any_nonfinite": any_nonfinite,
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_config = ExperimentConfig.from_yaml(BASE_CONFIG_PATH)
    t_values = np.geomspace(0.1, 10.0, num=12)
    q = base_config.propagation_front.q

    completed = _load_completed_points()
    grid = [(k, eta) for k in K_GRID for eta in ETA_GRID]
    remaining = [(k, eta) for k, eta in grid if (k, eta) not in completed]

    print(f"=== [A9] (K, eta) sweep: {len(grid)} points, {len(completed)} already done ===")
    print(f"base config: {BASE_CONFIG_PATH}")
    print(f"output: {RAW_OUTPUT_PATH}")
    print()

    sweep_start = time.perf_counter()
    with open(RAW_OUTPUT_PATH, "a", encoding="utf-8") as f:
        for i, (k, eta) in enumerate(remaining, start=1):
            print(f"[{i}/{len(remaining)}] K={k} eta={eta} ...", end=" ", flush=True)
            record = _run_one_point(base_config, k, eta, t_values, q)
            f.write(json.dumps(record) + "\n")
            f.flush()
            flag = " [NONFINITE]" if record["any_nonfinite"] else ""
            print(f"{record['elapsed_s']:.1f}s verdict={record['verdict']}{flag}")

    total_elapsed = time.perf_counter() - sweep_start
    print()
    print(f"=== sweep points run this session: {len(remaining)}, elapsed: {total_elapsed:.1f}s ===")
    print(f"Full raw results: {RAW_OUTPUT_PATH}")
    print("Per [A9]'s frozen decision rule: look for a broad stability plateau,")
    print("not the point with the 'best' verdict. Do not select a winning point")
    print("from this data -- report the stability landscape.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
