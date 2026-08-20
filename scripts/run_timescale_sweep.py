#!/usr/bin/env python
"""Early-Time Timescale Sweep (`docs/v5_spec.md` Sec16): after `[A71]`'s
corrected World A held at windows {10,25,49}, does an EARLIER, less-
delocalized/less-adapted snapshot show geometric structure that later
windows wash out? `eta` stays FIXED at 0.1 (unchanged from every prior
test) -- ONLY the checkpoint schedule changes, per the Minimal
Relaxation Rule (falsification-ladder.md).

Reuses `run_geometry_signal_audit_one_trial` UNCHANGED -- `checkpoint_
windows` was already a free parameter, so this required zero new
source code. SAME 10 trials/master_seed as Sec15/[A70]/[A71] -- windows
{25,49} reproduce those results exactly within one continuous run.
"""

import sys

from boyko_benchmark.experiment.geometry_signal_audit_gate import (
    run_geometry_signal_audit_one_trial,
)

N_SIDE_LENGTH = 8  # N = 8^3 = 512
N_TRIALS = 10
CHECKPOINT_WINDOWS = (1, 2, 3, 5, 8, 10, 25, 49)  # docs/v5_spec.md Sec16 -- frozen schedule
ETA = 0.1  # FIXED, unchanged from Sec15 -- only timescale varies here
DT = 0.05
K_SUBSTEPS = 50
MASTER_SEED = 20260818


def main() -> int:
    print("=== Early-Time Timescale Sweep (docs/v5_spec.md Sec16) ===")
    print(
        f"N={N_SIDE_LENGTH**3} (UNDAMAGED), checkpoints={CHECKPOINT_WINDOWS}, eta={ETA} (FIXED), "
        f"dt={DT}, K={K_SUBSTEPS}, {N_TRIALS} trials, master_seed={MASTER_SEED}"
    )
    print(
        "Motivation: [A71]'s Recall@D_mag was higher at window 25 (0.0446) than window "
        "49 (0.0039) -- read as noise there since it didn't survive to the primary "
        "checkpoint. This sweep tests whether EARLIER windows show a real, decaying "
        "signal, or whether chance holds at every timescale too."
    )
    print()
    header = (
        f"{'trial':>5} {'source':>6} {'window':>7} "
        f"{'AUROC_re':>9} {'recall_re':>10}   "
        f"{'AUROC_mag':>10} {'recall_mag':>11} {'spear_mag':>10}"
    )
    print(header)

    results = []
    for trial_index in range(N_TRIALS):
        result = run_geometry_signal_audit_one_trial(
            side_length=N_SIDE_LENGTH,
            checkpoint_windows=CHECKPOINT_WINDOWS,
            eta=ETA,
            dt=DT,
            k=K_SUBSTEPS,
            trial_index=trial_index,
            master_seed=MASTER_SEED,
        )
        results.append(result)
        for cp in result.checkpoints:
            a, m = cp.audit, cp.audit_magnitude
            print(
                f"{trial_index:>5} {result.source_node:>6} {cp.window_count:>7} "
                f"{a.auroc_nn:>9.4f} {a.rank_metrics_nn.recall_at_d:>10.4f}   "
                f"{m.auroc_nn:>10.4f} {m.rank_metrics_nn.recall_at_d:>11.4f} "
                f"{m.spearman_rho:>10.4f}"
            )

    assert len(results) == N_TRIALS, (
        f"expected {N_TRIALS} completed trials, got {len(results)} -- a partial/crashed "
        f"run must not silently produce aggregate numbers at the wrong n_trials."
    )

    print()
    print("=== Aggregate, per checkpoint (mean across trials) -- the full timescale curve ===")
    for window in CHECKPOINT_WINDOWS:
        cps = [cp for r in results for cp in r.checkpoints if cp.window_count == window]
        mean_auroc_mag = sum(cp.audit_magnitude.auroc_nn for cp in cps) / len(cps)
        mean_recall_mag = sum(cp.audit_magnitude.rank_metrics_nn.recall_at_d for cp in cps) / len(
            cps
        )
        mean_baseline_mag = sum(
            cp.audit_magnitude.rank_metrics_nn.baseline_recall for cp in cps
        ) / len(cps)
        mean_spearman_mag = sum(cp.audit_magnitude.spearman_rho for cp in cps) / len(cps)
        ratio = mean_recall_mag / mean_baseline_mag if mean_baseline_mag > 0 else float("nan")
        print(
            f"window={window:>3}  [Mag] AUROC={mean_auroc_mag:.4f}  "
            f"Recall@D={mean_recall_mag:.4f}  (baseline={mean_baseline_mag:.4f}, "
            f"ratio={ratio:.2f}x)  Spearman={mean_spearman_mag:.4f}"
        )

    print()
    print(
        "Interpretation (docs/v5_spec.md Sec16, pre-registered before this ran): if "
        "AUROC/Spearman stay at chance at EVERY window including window=1, the "
        "timescale hypothesis is closed -- eta is the next, separately-motivated "
        "candidate. If early windows show clear elevation decaying toward the known "
        "near-chance value by window 49, that's a genuine positive finding motivating "
        "an early-sampled C_ij scorer design. Non-monotonic/single-spike patterns are "
        "reported honestly as such, not cherry-picked."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
