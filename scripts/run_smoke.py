#!/usr/bin/env python
"""Runs the full Gate-A pipeline end-to-end against a config and prints a
report (CLAUDE.md's Completion Rule: a milestone is complete only after
the verification commands are run and their output is shown).

`configs/smoke.yaml`'s own header: this is a pipeline SMOKE test -- it
verifies every stage runs without error and produces every required
artifact. It is deliberately too small (few sizes, few seeds, short
adaptation budget) to support any real SURVIVES/FAILS conclusion. Never
treat this run's verdict as a scientific result.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np

from boyko_benchmark.config import ExperimentConfig
from boyko_benchmark.experiment.phase_runner import run_phase


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = ExperimentConfig.from_yaml(args.config)
    t_values = np.array([0.5, 1.0, 2.0])
    q = config.propagation_front.q

    print(f"=== boyko-benchmark smoke run: {args.config} ===")
    print(
        f"sizes={config.sizes} seeds_per_arm_size={config.seeds_per_arm_size} "
        f"arms={[a.value for a in config.arms]}"
    )
    print()

    start = time.perf_counter()
    result = run_phase(config, t_values=t_values, q=q)
    elapsed = time.perf_counter() - start

    print(f"Completed in {elapsed:.2f}s")
    print()
    print("--- Provenance ---")
    print(f"git_commit_hash: {result.provenance.git_commit_hash}")
    print(
        f"python: {result.provenance.python_version}  numpy: {result.provenance.numpy_version}  "
        f"scipy: {result.provenance.scipy_version}  networkx: {result.provenance.networkx_version}"
    )
    print(f"platform: {result.provenance.os_platform}")
    print()
    print("--- Gate-A results ---")
    print(
        f"G1 (finite-size convergence): {result.g1.status.value} (converges={result.g1.converges})"
    )
    print(
        f"G2 (spectral-gap closure):    {result.g2.status.value} "
        f"(gamma={result.g2.exponent_used:.4f}, R^2={result.g2.fit.r_squared:.4f})"
    )
    print(
        f"G3 (resistance-diameter growth): {result.g3.status.value} "
        f"(delta={result.g3.delta:.4f}, power_R^2={result.g3.power_fit.r_squared:.4f}, "
        f"log_R^2={result.g3.log_fit.r_squared:.4f})"
    )
    print(
        f"G4 (IPR delocalization):     {result.g4.status.value} "
        f"(eta={result.g4.exponent_used:.4f}, R^2={result.g4.fit.r_squared:.4f})"
    )
    print(
        f"G5 (propagation front):      {result.g5.status.value} "
        f"(v_eff={result.g5.fit.v_eff:.4f}, R^2={result.g5.fit.r_squared:.4f})"
    )
    print(
        f"G6 (negative-control separation): {result.g6.tier.value} "
        f"({result.g6.n_cleared}/15 cells cleared MCID)"
    )
    print()
    print(f"=== VERDICT: {result.verdict.value} ===")
    print()
    print("Reminder: this config is a pipeline smoke test, not a scientific")
    print("run (see configs/smoke.yaml header) -- the verdict above proves")
    print("the pipeline executed end-to-end, not that any geometric-phase")
    print("claim holds.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
