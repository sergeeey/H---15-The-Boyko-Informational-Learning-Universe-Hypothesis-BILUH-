#!/usr/bin/env python
"""Geometry Signal Audit (`docs/v5_spec.md` Sec15): after `[A69]` found
`C_ij` does not encode EXACT damaged-edge identity, does it encode
COARSE geometric locality instead? Runs on the UNDAMAGED T7/`[A32]`
lattice -- no damage, no swap operator, topology frozen -- the most
upstream possible check of whether `psi -> C_ij` produces any
detectable geometric signal at all.

10 trials vary the excitation source node (deterministic, not a damage
seed -- see Sec15.1 for why "seed" would be the wrong word here), same
checkpoints/eta/dt/K as Sec13/Sec14 for continuity.
"""

import sys

from boyko_benchmark.experiment.geometry_signal_audit_gate import (
    run_geometry_signal_audit_one_trial,
)

N_SIDE_LENGTH = 8  # N = 8^3 = 512
N_TRIALS = 10
CHECKPOINT_WINDOWS = (10, 25, 49)
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
MASTER_SEED = 20260818


def main() -> int:
    print("=== Geometry Signal Audit (docs/v5_spec.md Sec15) ===")
    print(
        f"N={N_SIDE_LENGTH**3} (UNDAMAGED), checkpoints={CHECKPOINT_WINDOWS}, eta={ETA}, "
        f"dt={DT}, K={K_SUBSTEPS}, {N_TRIALS} trials, master_seed={MASTER_SEED}"
    )
    print()
    header = (
        f"{'trial':>5} {'source':>6} {'window':>7} {'AUROC':>7} {'recall@D':>9} "
        f"{'AUPRC':>7} {'AUPRC_base':>10} {'spearman':>9}"
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
            a = cp.audit
            print(
                f"{trial_index:>5} {result.source_node:>6} {cp.window_count:>7} "
                f"{a.auroc_nn:>7.4f} {a.rank_metrics_nn.recall_at_d:>9.4f} "
                f"{a.rank_metrics_nn.auprc:>7.4f} {a.rank_metrics_nn.baseline_auprc:>10.4f} "
                f"{a.spearman_rho:>9.4f}"
            )

    assert len(results) == N_TRIALS, (
        f"expected {N_TRIALS} completed trials, got {len(results)} -- a partial/crashed "
        f"run must not silently produce aggregate numbers at the wrong n_trials."
    )

    print()
    print("=== Aggregate, per checkpoint (mean across trials) ===")
    for window in CHECKPOINT_WINDOWS:
        cps = [cp for r in results for cp in r.checkpoints if cp.window_count == window]
        mean_auroc = sum(cp.audit.auroc_nn for cp in cps) / len(cps)
        mean_recall = sum(cp.audit.rank_metrics_nn.recall_at_d for cp in cps) / len(cps)
        mean_auprc = sum(cp.audit.rank_metrics_nn.auprc for cp in cps) / len(cps)
        mean_auprc_base = sum(cp.audit.rank_metrics_nn.baseline_auprc for cp in cps) / len(cps)
        mean_spearman = sum(cp.audit.spearman_rho for cp in cps) / len(cps)
        print(
            f"window={window:>3}  mean AUROC={mean_auroc:.4f}  mean Recall@D={mean_recall:.4f}  "
            f"mean AUPRC={mean_auprc:.4f}  mean AUPRC_baseline={mean_auprc_base:.4f}  "
            f"mean Spearman={mean_spearman:.4f}"
        )

    print()
    print("=== Distance shells, final checkpoint, trial 0 (illustrative) ===")
    final_cp = next(
        cp for cp in results[0].checkpoints if cp.window_count == CHECKPOINT_WINDOWS[-1]
    )
    for shell in final_cp.audit.distance_shells:
        print(f"  d={shell.distance:>2}  mean_C={shell.mean_c:>10.6f}  n_pairs={shell.n_pairs}")

    print()
    print("=== Top-D distance distribution, final checkpoint, trial 0 (illustrative) ===")
    for d_val, frac in sorted(final_cp.audit.top_d_distance_fractions.items()):
        print(f"  P(d*={d_val:>2} | top-D) = {frac:.4f}")

    print()
    print(
        "Interpretation (docs/v5_spec.md Sec15.3): World A (no signal: AUROC~0.5, "
        "Spearman~0, shells indistinguishable) means the problem is upstream of topology "
        "learning. World B (Spearman meaningfully positive, top-D enriched for low distance, "
        "but [A69]'s exact-edge AUPRC stays at chance) means C_ij encodes locality, not exact "
        "adjacency -- reframe future work toward coarse distance/neighborhood learning."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
