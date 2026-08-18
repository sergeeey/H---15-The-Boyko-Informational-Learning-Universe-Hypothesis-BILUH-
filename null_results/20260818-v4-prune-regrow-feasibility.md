# NULL RESULT — V4 Independent Edge-Pruning Structural Plasticity (K1/K1c/K1d)

**Verdict: FEASIBILITY REJECT.** Recorded 2026-08-18 per
`~/.claude/rules/falsification-ladder.md`. Never delete; read this
before re-attempting independent-edge-deletion structural plasticity in
this codebase.

**Explicitly NOT a BILUH hypothesis FAIL.** This closes one specific
mechanism family (rank-then-delete edges independently, constrained
only by a per-node incidence cap), not the broader claim that
state-dependent structural plasticity can produce useful organization.
See "What is NOT killed" below and `docs/assumptions.md` `[A64]` for the
full reasoning.

## The claim that was tested

That `V4`'s `StatefulTopologyRule` family — persistence-gated,
weight-ranked independent edge pruning, followed by deterministic
Top-K regrowth, with the prune step optionally capped by a per-node
incidence limit (`RateBasedTopologyRule` / `BoundedIncidenceTopology
Rule`) — could restore a damaged periodic lattice better than a
distance-matched null (K1's `R_edge(A3) > R_edge(A4)`), while
simultaneously realizing its own pre-registered structural-exposure
target and staying connected.

Question type (EstimandOps L0): **causal** — `Δ_specific = Y(A3) −
Y(A4)`, potential outcomes over whole simulation runs (`docs/v4_spec.md`
§1). The causal claim was always scoped explicitly to "within this
simulator," never a physical claim.

## What was actually run

- `K1` (original, unconstrained `RateBasedTopologyRule`): N=512,
  damage=10%, ρ=0.01, m=3, 5 seeds, exact spec-frozen parameters.
- `K1c` (`BoundedIncidenceTopologyRule`, current-degree cap, `q=1/2`
  pre-registered before any run): identical scale.
- `K1d` (`BoundedIncidenceTopologyRule`, reference-degree cap, same
  `q=1/2`, no new calibration): identical scale.
- Two independent, exact (not heuristic) capacity audits, one per cap
  variant, solving the true maximum-cardinality capacitated edge
  selection via `scipy.optimize.milp`.
- One permutation-equivariance red-team test (random node relabeling,
  identical seeds, pruned-edge-set comparison).

## Why it was rejected — the exact capacity ceiling, not a bug

| stage | `ICE-1` exposure (actual) | exact optimum `CR*` | disconnection rate | disconnection window |
|---|---|---|---|---|
| K1 (unconstrained) | n/a (100% disconnect immediately) | n/a | 100% | window 2, every seed |
| K1c (current-degree cap) | 0.254 | 0.30 | 80% | windows 10-17 |
| K1d (reference-degree cap) | 0.487 | 0.52 | 100% | window 3, every seed |

The decisive fact: in BOTH capped variants, the GREEDY selector already
achieves 94-98% of the exact mathematical optimum (`CR_greedy/CR*`).
Fixing the selector cannot help — the ceiling itself (`CR*`) is far
below the 0.95 exposure threshold required for `R_edge` to be
trustworthy evidence about anything. This was verified by exact integer
programming (`observables/capacity_matching.py`), not estimated or
assumed.

**Mechanistic root cause, established via a chain of independent
checks:** under-propagated nodes' entire incident-edge groups get
depressed together by Hebbian dynamics (a common-mode effect of low
local density), so weight-ranked pruning selects whole "stars" at once.
This was confirmed GENUINE (not a tie-break/labeling artifact) via a
permutation-equivariance test whose pruned-edge set matched exactly
(15/15) after relabeling and re-running with identical seeds.

Capping how many of one node's edges can be pruned per window (K1c)
delays the failure roughly 5-8x in window-count but does not remove it,
and paradoxically fixing the specific feedback loop that caused K1c's
delay (K1d, reference-degree cap) made the connectivity failure BOTH
more reliable (80%→100%) and faster (windows 10-17 → uniformly window
3) — the same concentration mechanism simply routes around a static
per-window cap via two consecutive windows of targeting the same node,
instead of needing one window with an inflated cap.

## What is NOT killed (do not over-read this document)

- The fast-dynamics backend, Hamiltonian construction, and all prior
  Stage-1 arm infrastructure — untouched, unaffected.
- The damage/corruption toolkit (`corrupt_lattice_edges`, degree-
  preserving rewire via `networkx.double_edge_swap`) — reusable as-is,
  and directly relevant to `V5`'s proposed elementary operation.
- `SeedManager`'s independent seed-stream discipline (`[A11]`).
- The three ICE gates (Exposure/Connectivity/Cap-Activity) and the
  PASS/FAIL/INVALID trichotomy that correctly distinguished "substrate
  can't run this test" from "the test ran and disproved the claim" at
  every step — this discipline is exactly why K1/K1c/K1d never produced
  a false positive or false negative `R_edge` reading.
- The exact-capacity-audit technique (`observables/capacity_matching.py`,
  `scipy.optimize.milp`-based, unit-tested) — a new, reusable diagnostic
  for any future rate-limited selection mechanism in this project.
- The permutation-equivariance red-team protocol — a reusable pattern
  for distinguishing genuine mechanism properties from label/ordering
  artifacts, applicable well beyond V4.
- **`[A45]`'s separate open anomaly** (Phase 11-12, shuffled
  correlations beating real ones on curvature structural excess) is
  untouched by this result and remains its own unresolved open item.
- Phase 11-12's own REJECT verdict (`null_results/20260814-open-system-
  geometrogenesis.md`) stands independently, unaffected either way.

## Kill Analysis (per this project's Anti-Overfitting Gate discipline)

**What was explicitly killed:** the specific architectural decomposition
"rank all candidate edges independently by a state-derived desirability
score, then delete the highest-ranked ones, optionally subject to a
per-node incidence constraint" as a mechanism for damaged-lattice
restoration in this simulator, at the tested `ρ=0.01`, `m=3`, N=512
regime, across two independently-motivated cap formulations.

**What was NOT killed:** whether state-dependent structural plasticity
of ANY kind can produce useful organization; whether a DIFFERENT
elementary operation (e.g., degree-preserving connectivity-checked edge
swap/rewiring, proposed as `V5`) could avoid the diagnosed failure mode
by construction rather than by post-hoc constraint; whether smaller
`ρ`/different `m` combinations exist where independent pruning might
work (not tested, and per the user's own reasoning, unlikely to help
given `H-A`'s structural nature — but not formally excluded).

**Relaxation map for a future attempt, if independent pruning is ever
revisited (not recommended as the next step — see `[A64]`):** `ρ` itself
(smaller values only worsen `CR*` per `[A61]`/`[A63]`'s own finding that
`ρ↓` tightens, not loosens, the same binding constraint — deprioritized
by the user's own analysis); the eligibility/persistence mechanism
itself (`m` requirement, low-set quantile size); a fundamentally
different candidate-selection principle (e.g., allow ties in prune
desirability to break toward degree-diverse candidates). None of these
are pursued here.

## Revival condition

A future attempt at independent-edge-deletion structural plasticity in
this codebase must state explicitly which of `[A64]`'s established
facts it expects to be different, and why — re-running the same
architecture at a different `(ρ, q)` point without addressing the
`CR*` ceiling directly is not a revival, it is an unlicensed re-attempt
of a mechanism already shown structurally incompatible at two
independently-motivated cap formulations.
