# Phase 11 (Open-System Geometrogenesis Pilot) — Milestone 6 Analysis Freeze

Status: FROZEN 2026-08-14. This document fixes the interpretation of
Milestones 1-5 before any further Phase 11 work (Milestone 7's extended
FSS) proceeds. Per this project's Falsification Ladder discipline
(`~/.claude/rules/falsification-ladder.md`), reopening this freeze
requires a dated addendum here, never a silent rewrite.

## What was built (Milestones 1-2, infrastructure)

- `DynamicsBackend` protocol + `ClosedUnitaryBackend` (regression-matches
  the existing closed-system pipeline exactly) + `PhenomenologicalOpenBackend`
  (split-step: propagate -> damp -> noise, no renormalization).
- `experiment/open_pilot.py::run_adaptive_dynamics_open` — same
  fast/slow loop as `experiment/runner.py`, generalized over the backend.
- Full T1-T10 regression suite (closed-limit match, analytic pure-damping
  check, OU stationary-variance convergence, seed reproducibility across
  4 independent seed spaces, NaN/Inf invariants, symmetry invariants,
  provenance tuple).
- `detect_plateau` recalibrated on 9 reference curves (`[A36]`):
  **G1 has essentially zero resolving power below N~512** — this is the
  single most consequential infrastructure finding of Phase 11, and
  governs every interpretation below.
- T7 / Milestone 2 gate: at least one nonzero `(γ,σ)` cell does not
  destroy `[A32]`'s lattice positive control (`|Δpeak d_s| < 1.0` for all
  4 factorial cells).
- Mechanistic diagnostics: `D_W`, `D_OC` (weight trajectory divergence),
  `conductance`, `modularity`.
- Config/script layer (`open_config.py`, `configs/open_pilot.yaml`,
  `scripts/run_open_pilot.py`, `scripts/run_milestone5_h0_control.py`).

## The one pre-registered decision made this session (`[A35]`)

γ̃=0.05 (the only pilot level ever validated) nearly freezes Hebbian
weight movement — `D_W` ~10-12x smaller than the closed baseline, on
both the lattice and Active. **The user explicitly chose, before seeing
any Milestone 3 Active-arm result, to proceed with this γ̃ as-is and
treat a near-zero separation as itself informative
(`OPEN_DYNAMICS_NO_EFFECT`)**, and to run Milestone 3 at N=512 (per
`[A36]`). This was a genuine pre-registration, not a post-hoc rationalization.

## Milestone 3 result: G1 is uninformative here too

All 20 pilot points (N=512, 4 cells, 5 seeds) show `converged=False` —
the same non-plateauing "expander-like" `d_s(t)` signature already
recorded for closed-system Active at N=512 (`[A30]`). No cell separates
from any other on G1 with an MCID-passing effect (CI overlap on every
pairwise comparison attempted). **G1 answers nothing about open-system
Active at this budget** — consistent with, not contradicting, `[A36]`'s
warning, since N=512 alone does not guarantee convergence within a
reasonable `t`-range for every dynamics regime, only that the DETECTOR
itself is capable of resolving 3D geometry from an expander AT that N
when the underlying dimension estimate has in fact stabilized.

`Cγ`'s `D_W` reproduces `[A35]`'s prediction almost exactly (collapsed
toward `C0`) — `OPEN_DYNAMICS_NO_EFFECT` at γ̃=0.05 is confirmed on
Active, not just the lattice. This was pre-registered, not discovered.

## Milestone 4-5: the one real signal found, and what killed half of it

`Cσ` (noise only, γ=0) shows a modularity increase over `C0` that:

1. Is MCID-significant (`d=6.87`, non-overlapping 95% CI).
2. Survives a negative control against the raw ER-graph's own
   random-fluctuation modularity floor (`d=7.73` vs 10 fresh untouched
   graphs) — **not** an artifact of greedy-modularity's known tendency
   to find spurious structure in random graphs (Guimerà et al. 2004).
3. Does **NOT** survive a correlation-specificity control
   (`CorrelationShuffleAdaptation`, H0): shuffling which node pairs get
   reinforced, while preserving the correlation-magnitude distribution,
   produces a statistically indistinguishable result (`d=-0.735`, CI
   overlap).

**Frozen interpretation:** noise-driven reinforcement (structured or
not) measurably moves modularity off the random-graph floor at this
budget. This is a real, reproducible, MCID-passing effect. **It is NOT
evidence that the specific correlations the noisy quantum dynamics
builds matter** — a generic reinforcement rule with the same
correlation-magnitude statistics does the same thing. Neither the
original H1 ("real correlation structure organizes the graph") nor plain
H5 ("noise homogenizes, lowering modularity") is fully correct; the
data supports a third, narrower claim not pre-registered by either:
*sufficiently strong reinforcement noise raises modularity above the
random floor regardless of which edges it reinforces*, at this specific
`(K, dt, dtau_steps, η, σ̃)` budget.

## What this does NOT establish (scientific boundary, CLAUDE.md)

- Not evidence of emergent physical geometry.
- Not evidence that open-system dynamics can or cannot produce geometric
  organization in general — only that, at this one budget, G1 cannot
  see any such organization if it exists, and the one metric that DID
  move (modularity) moved for a reason unrelated to which correlations
  are real.
- Not a confirmation or refutation of BILUH.
- The strongest defensible verdict for Phase 11 to date:
  `SURVIVES_GEOMETRIC_PHASE_SCREEN` is **not reachable** from this data
  — G1 (the metric the screen is actually defined on, `docs/
  falsification_gates.md`) never converges for any open-system Active
  cell tested. No Gate-A verdict is issued here; Phase 11 remains
  exploratory pilot work, not a Gate-A run.

## Caveats carried forward, not silently dropped

- 5 seeds is small for an effect size this close to the MCID threshold
  in the negative direction (`Cσ` vs `Cγ` shuffle: `d=-0.735`, just
  under `0.8`) — genuinely underpowered to rule out a smaller real
  correlation-specific effect, not proven absent.
- Only one `(γ̃, σ̃)` level pair was ever tested (`0.05, 0.05`) — by
  design (anti-parameter-fishing), but it means every finding above is
  conditional on this specific budget and does not generalize to other
  dissipation/noise strengths without new, separately pre-registered runs.
- `boyko-minimal-experiment-v1.0.md`'s provenance is still `[UNKNOWN]` —
  unresolved from earlier in this project, unaffected by Phase 11.

## Before Milestone 7 (extended FSS)

Milestone 7 is a materially larger compute campaign than anything run so
far: multiple N values (not just 512), more seeds per cell, likely
multiple `(γ̃, σ̃)` pairs if the modularity finding above is to be
followed up properly (e.g. a real power analysis for the H0-vs-H1
comparison). A single N=512 seed already costs several minutes; a
genuine FSS grid at this cost per point is a multi-hour-to-multi-day
undertaking, not something to launch silently. **This freeze
deliberately stops here** — Milestone 7 needs the user's explicit go/no-go
on scope and compute budget before any further pilot work begins.

## Addendum (2026-08-14, later same day) — Milestone 7 ran (N=512+1024, 10 seeds); this freeze's conclusions hold, one strengthened, one new caveat added

Per Checkpoint Fidelity discipline (`~/.claude/rules/memory-protocol.md`),
this is a dated addendum, not a silent rewrite of the freeze above.

User approved Milestone 7's scope explicitly: N=512 AND N=1024,
`seeds_per_cell=10` (80-point grid, `[A39]` full detail). Along the way,
hit and fixed a real infrastructure bug (`[A38]`): mean degree 6 falls
below Erdős–Rényi's connectivity threshold at N=1024, so the graph
generator's retry cap (sized for N≤512) needed raising from 20 to 150 —
fixed via TDD (regression test on the exact failing seed), not by
changing the scientific mean-degree parameter.

**What held:** G1 is still fully uninformative for open-system Active at
both N — `converged=False` for all 80 points, same non-plateauing
expander signature as before, just shifted higher with N (as it already
did for the closed system, `[A30]`). No Gate-A verdict is reachable from
this data either; the "exploratory pilot work, not a Gate-A run" framing
above still stands.

**What strengthened:** `Cσ`'s modularity effect (Milestone 4/`[A37]`)
replicated at both N with MORE seeds, and grew rather than shrank
(`d=7.66` at N=512 → `d=13.9` at N=1024, both MCID-passing) — the
negative control (raw-ER-graph floor) was re-checked at N=1024 too and
`C0` still doesn't clear it. This argues against the effect being a
finite-size or underpowered artifact.

**What's new and NOT resolved:** Milestone 5's H0-vs-H1
correlation-specificity question (`CorrelationShuffleAdaptation` vs real
Hebbian, `d=-0.735` at 5 seeds) was **not** re-run with more power in
Milestone 7 — the approved scope was the 4-cell factorial grid, not the
H0 control. The "if wrong: a larger seed count... could reveal a
real-vs-shuffled separation" caveat in `[A37]` therefore remains exactly
as open as it was before Milestone 7. Anyone reading only the modularity
replication above should not conclude the correlation-specificity
question was also answered — it wasn't touched.
