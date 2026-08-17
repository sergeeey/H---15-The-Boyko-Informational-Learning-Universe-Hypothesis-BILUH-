# Phase 12 — Partition-Level Analysis of the Cσ Modularity Effect

**Status: PROPOSED, 2026-08-14. Not approved, nothing run.** This document
is a pre-registration: it is written and committed BEFORE any Phase 12
measurement, so the pass/fail predicates below cannot be reshaped to fit
whatever the data turns out to show (`~/.claude/rules/estimand-ops.md`,
"Estimand defined after data access" anti-pattern).

---

## L0 Gate (EstimandOps, mandatory first step)

**Question type: DESCRIPTIVE.**

Phase 12 asks *what structure exists* in graphs already produced by Phase
11's dynamics — not *what would happen if we intervened* (causal), and
not *what will happen to a new case* (predictive). Every stage below
characterizes properties of an existing, already-generated population of
graphs.

**Consequence, binding on all downstream reporting:** no Phase 12 result
may be phrased as "noise causes X" or "correlations produce Y". Permitted
phrasing is "graphs generated under condition A differ from those under
condition B in property P". This is not pedantry — Phase 11's own `[A37]`
had to be walked back from a causal-sounding reading to a descriptive
one, and this gate exists to prevent a repeat.

---

## 1. Why this phase exists: the gap in Phase 11's own conclusion

Phase 11 Milestone 5 (`docs/assumptions.md` `[A37]`) concluded that the
`Cσ` modularity effect is **not specific to the real Hebbian correlation
structure**, because a shuffled-correlation control (H0) produced a
statistically indistinguishable *modularity value* (`d=-0.735`, CI
overlap).

**That comparison was made on a scalar summary statistic.** Modularity Q
is a single number describing how well *some* partition separates the
graph. Two entirely different partitions — different node groupings, no
overlap in membership — can score nearly identical Q. Milestone 5
therefore established that real and shuffled correlations produce
*equally modular* graphs. It did **not** establish that they produce
*the same communities*.

This is a genuine, unclosed gap in an already-recorded conclusion, and it
is cheap to close. It is the primary motivation for Phase 12.

**Second gap:** every Phase 11 seed varied the graph topology AND the
noise realization together (`graph_seed = 1000*seed_index + size`, and
`noise_seed = graph_seed`). No run ever held the graph fixed while
varying noise, or vice versa. Phase 11 therefore cannot distinguish
"this structure is a reproducible property of the graph" from "this
structure is one arbitrary noise realization". This too is cheap to fix.

---

## 2. Stage 0 — Substrate Gate: is the partition detector itself stable?

**This runs first and gates everything else** (FL Step 2a: an untrusted
measuring apparatus produces neither support nor refutation, only
`BLOCKED-INFRASTRUCTURE`).

Every stage below compares partitions using Adjusted Mutual Information
(AMI). That is meaningless if `networkx.greedy_modularity_communities` —
the detector `observables/conductance.py::modularity` already uses — is
itself unstable, i.e. returns different partitions for the same input.

| Check | Method | Required outcome |
|---|---|---|
| Determinism | Run detector twice on one identical graph | AMI = 1.0 exactly, or the detector is nondeterministic and every downstream AMI is confounded |
| Floor | AMI between partitions of two INDEPENDENT ER(N,3N) draws | Establishes the "no shared structure" baseline. Expected near 0; must be measured, not assumed |
| Ceiling sensitivity | AMI between a graph and the same graph with 1% of edge weights perturbed | Establishes how much AMI moves under a change we agree is negligible |

**Verdict rule:** if determinism fails → `BLOCKED-INFRASTRUCTURE`, replace
or seed the detector before proceeding. The measured floor and ceiling
become the interpretive scale for every AMI number reported later — an
AMI of 0.6 means nothing until we know whether the floor is 0.02 or 0.5.

**Cost:** minutes, no dynamics runs.

---

## 3. Stage 1 — Infrastructure: persist final graphs

`scripts/run_open_pilot.py` currently writes only scalar metrics to
`results/open_pilot/raw.jsonl`. Final graph weights are discarded, so
every new analysis idea costs a full dynamics re-run (~36s/point at
N=1024).

**Task:** persist each point's final weight matrix (compressed `.npz`,
keyed by `(size, seed_index, cell)`) alongside `raw.jsonl`. Everything is
already deterministic and seeded (verified by T4's reproducibility test),
so this changes no result — it only stops us from paying for the same
computation repeatedly.

**Cost:** ~30 min implementation + one re-run at N=512 to populate.

---

## 4. Stage 2 — The core test: partition-level comparison

All comparisons are **within-seed** (same graph, so node identities are
comparable) and reported as distributions across the 10 seeds. All at
N=512 first (cheap); N=1024 only if N=512 shows a signal.

### 2a. Does noise reorganize communities, or just re-weight them?

Compare `AMI(partition(Cσ), partition(C0))` on the same graph.

| Outcome | Reading |
|---|---|
| AMI near the Stage-0 ceiling (partition essentially unchanged) | The modularity increase is a **re-weighting** artifact — the same communities got sharper edges, nothing reorganized |
| AMI well below ceiling, well above floor | Noise genuinely moved community membership — a stronger finding than `[A37]` currently claims |
| AMI near floor | Noise destroyed and rebuilt the partition arbitrarily |

### 2b. The Milestone 5 re-test — the actual point of this phase

Compare `AMI(partition(Cσ), partition(H0-shuffle))` on the same graph,
same noise seed, so the ONLY difference is whether the correlation term
was shuffled.

| Outcome | Reading | Effect on `[A37]` |
|---|---|---|
| AMI high (near ceiling) | Real and shuffled correlations produce the *same communities*, not merely the same Q | **Strengthens** `[A37]`'s kill — correlations genuinely don't matter |
| AMI low (near floor) | Same modularity magnitude, *different communities* — correlations DO determine which nodes group together | **Reopens H1.** `[A37]`'s null was measured on a statistic blind to the thing H1 actually predicted |

Note honestly: the second outcome would mean Phase 11's Milestone 5
conclusion was drawn from an inadequate observable, not from a real null.
That is a live possibility and this test is designed to be able to say so.

### 2c. Variance decomposition: graph-driven or noise-driven?

Fix one `graph_seed`; run `Cσ` with 5 different `noise_seed` values.
Compute pairwise AMI among the 5 resulting partitions.

| Outcome | Reading |
|---|---|
| High pairwise AMI | The partition is a reproducible property of the graph — noise reveals structure that was latent in the topology |
| Low pairwise AMI | Each run finds a different arbitrary partition — the modularity number is real but the structure behind it is not reproducible |

Repeat for 3 different `graph_seed`s so this isn't itself a single-graph
accident.

**Pre-registered thresholds:** all three sub-stages are interpreted
against Stage 0's *measured* floor and ceiling, not against fixed
constants. Where a binary call is needed: "high" = within 20% of the
measured ceiling; "low" = within 20% of the measured floor; anything
between is reported as intermediate and explicitly NOT forced into a
binary. These cutoffs are pre-registered but heuristic — labelled
`[WEAK]`, not presented as calibrated.

**Cost:** ~15 min compute at N=512 after Stage 1's persistence lands.

---

## 5. Stage 3 — A second geometry probe (gated on nothing; runs in parallel)

G1 (spectral dimension) has never converged for open-system Active at any
N tested (`[A39]`: 0/80 points). Rather than assume "no geometry", test
with an observable that has no plateau requirement.

**Forman-Ricci curvature first** — a closed-form combinatorial formula
per edge, no optimal-transport solver, no new dependency. If it shows any
systematic difference between cells, escalate to **Ollivier-Ricci**
(requires the `POT` library, meaningfully more expensive, but the
better-established discrete curvature notion).

**What a result means:** a curvature difference between `Cσ` and `C0` is
a *descriptive* difference in graph geometry-like structure. Per the L0
gate above, it is NOT evidence of emergent physical geometry, and the
`docs/falsification_gates.md` grep canary still applies to all reporting.

**Cost:** Forman ~1 hour implementation, minutes to run on persisted
graphs.

---

## 6. Stage 4 — (γ̃, σ̃) landscape map — GATED, do not start early

**Gate:** run only if Stage 2 produces a signal worth localizing (2b low
AMI, or 2c high AMI). If Stage 2 shows the structure is non-reproducible
noise, mapping the parameter space of a non-reproducible effect is waste.

**Anti-parameter-fishing discipline, mandatory** — this stage is the one
place in Phase 12 where the project's stop rules are genuinely at risk:

- Grid frozen in this document BEFORE running: `γ̃ ∈ {0, 0.01, 0.05}`,
  `σ̃ ∈ {0.01, 0.05, 0.1}` — 3×3, small by design.
- **Report the landscape, never select a winner.** Same rule as `[A9]`'s
  (K,η) sweep, which this project already ran under exactly this
  constraint: look for a broad plateau of stability, do not report a
  "best" point.
- Any post-hoc grid extension requires a new dated pre-registration, not
  an edit to this one.

**Cost:** 9 cells × 10 seeds × ~10s at N=512 ≈ 15-20 min.

---

## 7. Stop Rules (kill conditions, pre-registered)

Phase 12 **terminates with a null result** — recorded in `null_results/`
per the global protocol, with full Kill Analysis — if ALL of:

1. Stage 2b shows high AMI (correlations don't determine communities), AND
2. Stage 2c shows low AMI (partitions aren't reproducible across noise), AND
3. Stage 3 shows no curvature difference between cells.

That combination means: the modularity effect is real as a number, but
corresponds to no reproducible, correlation-specific, or geometry-like
structure. At that point this rule family has been adequately tested and
the honest move is to stop, not to keep relaxing assumptions.

**Explicitly NOT a kill condition:** G1 continuing to not converge. That
is already known (`[A39]`) and is a statement about the observable, not
about the hypothesis.

---

## 8. What Phase 12 results will NOT mean

Written before results, per EstimandOps requirement:

1. Does **not** establish emergent physical geometry, spacetime, or any
   BILUH claim — the scientific boundary in `CLAUDE.md` is unchanged.
2. Does **not** generalize beyond the `(γ̃,σ̃)` values actually run.
3. Does **not** answer whether a *different* adaptation rule would behave
   differently — `AntiHebbianAdaptation` exists in the codebase but is
   out of Phase 12 scope.
4. A high-AMI result in 2b does **not** prove correlations are irrelevant
   in general — only that they don't determine community membership at
   this budget.

---

## 9. Cost summary and recommended order

| Stage | What | Cost | Gated? |
|---|---|---|---|
| 0 | Partition detector substrate gate | minutes | No — runs first, gates all |
| 1 | Persist final graphs | ~30 min impl + short re-run | No |
| 2 | Partition-level AMI analysis (2a/2b/2c) | ~15 min compute | No — the core of this phase |
| 3 | Forman-Ricci curvature | ~1 hr impl | No — parallel to 2 |
| 4 | (γ̃,σ̃) landscape map | ~20 min compute | **Yes** — only on a Stage-2 signal |

Total for Stages 0-3: roughly half a day of implementation, under an hour
of compute. Materially cheaper than Phase 11's Milestone 7 (~87 min
compute alone), and it closes a real gap in an already-recorded
conclusion rather than adding a new untested direction.

---

## 10. Open items carried forward, not silently dropped

- `boyko-minimal-experiment-v1.0.md` provenance: still `[UNKNOWN]`.
- `[A38]`'s retry cap is not scale-free; a future N > 1024 will need it
  revisited as a formula rather than a constant.
- Milestone 5's H0 control has never been run at N=1024 or at 10 seeds —
  Stage 2b addresses the *observable* gap but not the *power* gap; if
  Stage 2b is intermediate rather than clearly high/low, the power
  question returns and needs its own pre-registration.
