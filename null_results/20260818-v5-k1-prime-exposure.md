# NULL RESULT — V5-K1'-Exposure: State-Driven Swap Selection at B=D

**Verdict: FAIL** (bare, un-hedged Falsification-Ladder FAIL — not
`FEASIBILITY REJECT`, unlike `V4`'s prior closure). Recorded 2026-08-18
per `~/.claude/rules/falsification-ladder.md`. Never delete; read this
before re-attempting `CorrelationSwapScorer` state-driven selection at a
larger budget without addressing the points below.

**Explicitly NOT a rejection of the V5 swap operation itself.** The
substrate feasibility claim (`K_skip=0%`) this result is built on top
of is UNCHANGED and reconfirmed here at 2x the seed count and 5x the
budget of `K1'`. What failed is the STATE-SPECIFIC advantage of one
particular scorer (`CorrelationSwapScorer`) over the matched null, at
one particular scale — see "What is NOT killed" below and
`docs/assumptions.md` `[A68]` for the full reasoning.

## The claim that was tested

That `V5`'s `BalancedSwapTopologyRule`, driven by `CorrelationSwapScorer`
(`A3`, argmax `ΔS=C_added−C_removed`), restores a damaged periodic
lattice better than `DistanceStratifiedSwapScorer` (`A4`, matched null),
when given a swap budget equal to the number of damaged edges
(`B_total=D≈148`) — `docs/v5_spec.md` §13's frozen criterion:
`ΔR_edge(B=D)>0 AND Cohen's d≥0.8 (non-overlapping CI) AND majority of
paired seeds show A3>A4`, evaluated only at the final, largest
checkpoint.

Question type (EstimandOps L0): **causal**, identical framing to `K1'`
and `V4` — `Δ_specific = Y(A3) − Y(A4)`, potential outcomes over whole
simulation runs, scoped explicitly to "within this simulator."

## What was actually run

- `K1'` (prior, `n_swaps=3`/window, `dtau_steps=10`, 5 seeds): `[A66]`,
  PASS on the bare inequality but weak (`d=0.63<0.8`, 1/5 seeds carrying
  the effect).
- `V5-K1'-Exposure` (this document): identical `n_swaps=3`/window,
  ONE continuous run per arm/seed to `dtau_steps=49`, checkpoints
  recorded at window counts `{10,25,49}` (nominal `B≈{30,75,147}`
  committed swaps), 10 seeds (`master_seed=20260818`, seeds 0-4 the
  SAME damaged lattices as `K1'`), seed count decided from a real
  timing probe (`[A67]`) before any result from this follow-up existed.

## Why it was rejected — the effect never cleared the frozen bar, at any budget tested

| `B` (window) | `R_edge(A3)` mean | `R_edge(A4)` mean | `ΔR` | Cohen's `d` | MCID | wins A3>A4 |
|---|---|---|---|---|---|---|
| 30 | 0.0007 | 0.0000 | 0.0007 | 0.447 | False | 1/10 |
| 75 | 0.0007 | 0.0000 | 0.0007 | 0.447 | False | 1/10 |
| 147 (`B=D`) | 0.0027 | 0.0007 | 0.0021 | 0.708 | False | 3/10 |

At the pre-registered primary checkpoint (`B=D`): `d=0.708`, short of
the `0.8` MCID bar; CIs overlap (`A3: (0.0002,0.0053)` vs `A4:
(-0.0008,0.0022)`); only 3/10 seeds (not a majority) show `A3>A4`. All
three conditions were required — two of three fail.

**More important than the standardized effect: the absolute scale.**
At full budget (`B=D≈147`, as many committed swaps as damaged edges),
mean `R_edge(A3)=0.27%` — roughly 0.4 of ~147 damaged edges correctly
recovered on average. 6/10 seeds recovered literally zero correct edges
under EITHER arm even at full budget. `[HYPOTHESIS]`, not independently
verified further: the per-seed pattern (each nonzero seed lands almost
exactly at `1/n_damaged`) suggests exact-edge recovery may be close to
a rare, near-Bernoulli event per seed at this `N`/candidate-pool scale,
not a smoothly graded process — landing on the ONE specific pair among
~2.3 million legal candidates that reconstructs an originally-damaged
edge is structurally rare regardless of which arm is choosing.

**Feasibility (`K_skip`) was NOT the limiting factor** — `K_skip=0%`
across every seed, every checkpoint, both arms (`[A68]`). The
"insufficient exposure" explanation `[A66]` offered as `[HYPOTHESIS]`
is substantially weakened: budget was pushed all the way to `B=D` and
the state-specific advantage still did not clear the pre-registered
bar. This most closely matches interpretation bucket 2 (Null) of
`docs/v5_spec.md` §13.5, pre-registered before any of this ran.

## What is NOT killed (do not over-read this document)

- The swap operation's feasibility/substrate cleanliness — `K_skip=0%`,
  now confirmed TWICE, at 2x the seed count and 5x the budget of `K1'`.
  `V5`'s core design claim (degree-preserving connected rewiring avoids
  `V4`'s independent-edge-deletion feasibility collapse) is untouched
  by this result and stands on its own evidence.
- The `on_window` checkpoint infrastructure, `k1_prime_common.py`'s
  shared helpers, the damage/`R_edge` toolkit — all reusable as-is for
  any future follow-up.
- Any claim about a DIFFERENT `N`, a budget scaled to `|E|` rather than
  to `D`, a different scorer, or a different adaptation rate — only ONE
  configuration was tested here, not a sweep, per this project's
  anti-fishing discipline. None of these are excluded by this result.
- Whether an endpoint OTHER than exact-edge-match `R_edge` (e.g. a
  distance/resistance-based partial-credit metric) would show a
  state-specific advantage this endpoint's coarseness may be masking —
  genuinely untested, not ruled out.
- `V4`'s own, separately-reached `FEASIBILITY REJECT`
  (`null_results/20260818-v4-prune-regrow-feasibility.md`) — unaffected
  either way.
- `[A45]`'s separate open Phase 11-12 anomaly — untouched, still open.

## Kill Analysis (per this project's Anti-Overfitting Gate discipline)

**What was explicitly killed:** the state-specific advantage of
`CorrelationSwapScorer`'s deterministic-argmax selection rule over
`DistanceStratifiedSwapScorer`'s matched-null shuffle, specifically at
N=512, 10% damage, `B_total=D≈148`, `n_swaps=3`/window — this exact
configuration does not clear this project's own MCID even when given a
full damage-count worth of committed swaps, and the "just needed more
exposure" explanation for the prior weak result is substantially
weakened (not proven impossible, but no longer well-supported at this
scale).

**What was NOT killed:** the swap mechanism's feasibility; any other
`N`, budget-to-damage ratio, scorer, or endpoint; the broader claim that
SOME state-dependent structural plasticity mechanism could show a real
effect under a different operationalization.

**Relaxation map for a future attempt (not auto-triggered — a new,
separately-motivated pre-registration is required, per the frozen
stop-rule):** larger `N` (denser candidate structure); budget scaled to
`|E|` instead of `D` (a categorically different exposure definition,
not just a bigger number); a scorer that targets exact edge
reconstruction more directly than raw `C_ij`; an alternative,
coarser-grained endpoint than exact-edge-match `R_edge` if the "rare
exact match" hypothesis above holds up under scrutiny. None of these
are pursued here.

## Revival condition

A future attempt must state explicitly which of `[A68]`'s established
facts (the specific `N`/budget/scorer/endpoint combination that failed)
it expects to differ, and why — simply re-running at a larger `B`
without addressing the near-floor absolute-scale finding, or without a
different exposure definition, is not a revival; it is an unlicensed
re-attempt of a configuration already shown not to clear this project's
own bar, and is exactly what `docs/v5_spec.md` §13.4's frozen stop-rule
exists to prevent.
