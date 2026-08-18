#!/usr/bin/env python
"""One-off timing probe for `V5-K1'-Exposure` (`docs/v5_spec.md` Sec13.3):
measures real per-window cost at N=512 scale with a SHORT run, to decide
5 vs 10 paired seeds by measured compute cost -- never by tuning after
seeing any `R_edge`. Not part of the pre-registered campaign itself.
"""

import sys
import time

from boyko_benchmark.experiment.k1_prime_exposure_gate import run_k1_prime_exposure_gate_one_seed

N_SIDE_LENGTH = 8  # N = 512, matches K1'/K1/K1c/K1d
DAMAGE_FRACTION = 0.10
N_SWAPS = 3
PROBE_WINDOWS = (3, 5)  # small checkpoints just to time a handful of real windows
MASTER_SEED = 20260818


def main() -> int:
    print("=== V5-K1'-Exposure timing probe (N=512, 1 seed, 5 windows/arm) ===")
    start = time.perf_counter()
    result = run_k1_prime_exposure_gate_one_seed(
        side_length=N_SIDE_LENGTH,
        damage_fraction=DAMAGE_FRACTION,
        n_swaps=N_SWAPS,
        checkpoint_windows=PROBE_WINDOWS,
        eta=0.1,
        dt=0.05,
        k=50,
        seed_index=0,
        master_seed=MASTER_SEED,
    )
    elapsed = time.perf_counter() - start

    windows_run = max(PROBE_WINDOWS) * 2  # 2 arms
    per_window = elapsed / windows_run
    print(f"n_damaged: {len(result.damaged_out)}")
    print(
        f"elapsed: {elapsed:.2f}s for {windows_run} total windows (2 arms x {max(PROBE_WINDOWS)})"
    )
    print(f"measured per-window cost: {per_window:.3f}s")
    print()
    for label, n_seeds in (("5-seed campaign", 5), ("10-seed campaign", 10)):
        total_windows = 49 * 2 * n_seeds
        estimate_min = total_windows * per_window / 60.0
        print(f"{label}: {total_windows} windows -> estimated {estimate_min:.1f} minutes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
