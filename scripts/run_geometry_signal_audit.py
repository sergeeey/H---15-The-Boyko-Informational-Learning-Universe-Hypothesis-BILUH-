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
    print(
        "Reviewer-caught addendum ([A70]/[A71]): the lattice is exactly bipartite, so "
        "Re(C_ij) is analytically forced to ~0 for every cross-parity (d*=1) pair "
        "REGARDLESS of real coupling. Every row below reports BOTH the original "
        "Re(C_ij)-based audit AND a magnitude |C_ij|-based companion that is not "
        "blind to phase-encoded information."
    )
    print()
    header = (
        f"{'trial':>5} {'source':>6} {'window':>7} "
        f"{'AUROC_re':>9} {'recall_re':>10} {'spear_re':>9}   "
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
                f"{a.auroc_nn:>9.4f} {a.rank_metrics_nn.recall_at_d:>10.4f} "
                f"{a.spearman_rho:>9.4f}   "
                f"{m.auroc_nn:>10.4f} {m.rank_metrics_nn.recall_at_d:>11.4f} "
                f"{m.spearman_rho:>10.4f}"
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
        mean_spearman = sum(cp.audit.spearman_rho for cp in cps) / len(cps)
        mean_auroc_mag = sum(cp.audit_magnitude.auroc_nn for cp in cps) / len(cps)
        mean_recall_mag = sum(cp.audit_magnitude.rank_metrics_nn.recall_at_d for cp in cps) / len(
            cps
        )
        mean_spearman_mag = sum(cp.audit_magnitude.spearman_rho for cp in cps) / len(cps)
        print(
            f"window={window:>3}  [Re]  AUROC={mean_auroc:.4f}  Recall@D={mean_recall:.4f}  "
            f"Spearman={mean_spearman:.4f}"
        )
        print(
            f"window={window:>3}  [Mag] AUROC={mean_auroc_mag:.4f}  "
            f"Recall@D={mean_recall_mag:.4f}  Spearman={mean_spearman_mag:.4f}"
        )

    print()
    print("=== Distance shells, final checkpoint, trial 0 (illustrative, [Mag]) ===")
    final_cp = next(
        cp for cp in results[0].checkpoints if cp.window_count == CHECKPOINT_WINDOWS[-1]
    )
    for shell in final_cp.audit_magnitude.distance_shells:
        print(f"  d={shell.distance:>2}  mean_|C|={shell.mean_c:>10.6f}  n_pairs={shell.n_pairs}")

    print()
    print("=== Top-D distance distribution, final checkpoint, trial 0 (illustrative, [Mag]) ===")
    for d_val, frac in sorted(final_cp.audit_magnitude.top_d_distance_fractions.items()):
        print(f"  P(d*={d_val:>2} | top-D) = {frac:.4f}")

    print()
    print(
        "Interpretation (docs/v5_spec.md Sec15.3, applied to the [Mag] variant, which "
        "does not share the Re-variant's bipartite degeneracy): World A (no signal: "
        "AUROC~0.5, Spearman~0, shells indistinguishable) means the problem is upstream "
        "of topology learning. World B (Spearman meaningfully positive, top-D enriched "
        "for low distance) means C_ij encodes locality, not exact adjacency -- reframe "
        "future work toward coarse distance/neighborhood learning using a magnitude- or "
        "phase-aware observable, not the Re-only convention used throughout this project "
        "so far."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
