#!/usr/bin/env python
"""`C_ij` Recall@D/AUPRC Signal Diagnostic (`docs/v5_spec.md` Sec14):
after `[A68]`'s FAIL, does `C_ij` itself carry information about which
lattice edges were removed (H2, operator problem) or not (H1, signal
problem)? No swap operator runs at all -- topology held frozen
(`IdentityStatefulTopology`) -- so this is far cheaper than `K1'-
Exposure`'s own `O(|E|^2)` candidate-enumeration cost.

Same T7/`[A32]` lattice, same 10% damage, same 10 seeds
(`master_seed=20260818`, identical damaged lattices to `K1'`/`K1'-
Exposure`), same checkpoints `{10,25,49}` and `eta=0.1`/`dt=0.05`/`K=50`
as `K1'-Exposure` -- direct comparability with the `[A68]` dose-response
curve already recorded.
"""

import sys

from boyko_benchmark.experiment.signal_diagnostic_gate import run_signal_diagnostic_one_seed

N_SIDE_LENGTH = 8  # N = 8^3 = 512
N_SEEDS = 10
DAMAGE_FRACTION = 0.10
CHECKPOINT_WINDOWS = (10, 25, 49)  # matches docs/v5_spec.md Sec13.1's schedule
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
MASTER_SEED = 20260818  # identical to K1/K1c/K1d/K1'/K1'-Exposure -- same damaged lattices


def main() -> int:
    print("=== C_ij Recall@D / AUPRC Signal Diagnostic (docs/v5_spec.md Sec14) ===")
    print(
        f"N={N_SIDE_LENGTH**3}, damage_fraction={DAMAGE_FRACTION}, "
        f"checkpoints={CHECKPOINT_WINDOWS}, eta={ETA}, dt={DT}, K={K_SUBSTEPS}, "
        f"{N_SEEDS} seeds, master_seed={MASTER_SEED}"
    )
    print()
    header = (
        f"{'seed':>4} {'n_damaged':>9} {'window':>7} {'recall@D':>10} {'baseline':>10} "
        f"{'ratio':>8} {'AUPRC':>8} {'AUPRC_base':>10} {'AUPRC_ratio':>11}"
    )
    print(header)

    results = []
    for seed_index in range(N_SEEDS):
        result = run_signal_diagnostic_one_seed(
            side_length=N_SIDE_LENGTH,
            damage_fraction=DAMAGE_FRACTION,
            checkpoint_windows=CHECKPOINT_WINDOWS,
            eta=ETA,
            dt=DT,
            k=K_SUBSTEPS,
            seed_index=seed_index,
            master_seed=MASTER_SEED,
        )
        results.append(result)
        for cp in result.checkpoints:
            ratio = cp.recall_at_d / cp.baseline_recall if cp.baseline_recall > 0 else float("nan")
            auprc_ratio = cp.auprc / cp.baseline_auprc if cp.baseline_auprc > 0 else float("nan")
            print(
                f"{seed_index:>4} {len(result.damaged_out):>9} {cp.window_count:>7} "
                f"{cp.recall_at_d:>10.4f} {cp.baseline_recall:>10.4f} {ratio:>8.2f} "
                f"{cp.auprc:>8.4f} {cp.baseline_auprc:>10.4f} {auprc_ratio:>11.2f}"
            )

    assert len(results) == N_SEEDS, (
        f"expected {N_SEEDS} completed seeds, got {len(results)} -- a partial/crashed "
        f"run must not silently produce aggregate numbers at the wrong n_seeds."
    )

    print()
    print("=== Aggregate, per checkpoint (mean across seeds) ===")
    for window in CHECKPOINT_WINDOWS:
        recalls = [
            cp.recall_at_d for r in results for cp in r.checkpoints if cp.window_count == window
        ]
        baselines = [
            cp.baseline_recall for r in results for cp in r.checkpoints if cp.window_count == window
        ]
        auprcs = [cp.auprc for r in results for cp in r.checkpoints if cp.window_count == window]
        auprc_baselines = [
            cp.baseline_auprc for r in results for cp in r.checkpoints if cp.window_count == window
        ]
        mean_recall = sum(recalls) / len(recalls)
        mean_baseline = sum(baselines) / len(baselines)
        mean_auprc = sum(auprcs) / len(auprcs)
        mean_auprc_baseline = sum(auprc_baselines) / len(auprc_baselines)
        ratio = mean_recall / mean_baseline if mean_baseline > 0 else float("nan")
        auprc_ratio = mean_auprc / mean_auprc_baseline if mean_auprc_baseline > 0 else float("nan")
        print(
            f"window={window:>3}  mean Recall@D={mean_recall:.4f}  "
            f"mean baseline={mean_baseline:.4f}  ratio={ratio:.2f}x  "
            f"mean AUPRC={mean_auprc:.4f}  mean AUPRC_baseline={mean_auprc_baseline:.4f}  "
            f"AUPRC_ratio={auprc_ratio:.2f}x"
        )

    print()
    print(
        "Interpretation (docs/v5_spec.md Sec14, pre-registered): ratio >> 1 (roughly >10x) "
        "at the final checkpoint favors H2 (operator problem, C_ij carries signal); "
        "ratio near 1 (roughly 2-3x or less) favors H1 (signal problem, C_ij does not "
        "discriminate genuinely-damaged edges at this scale)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
