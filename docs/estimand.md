# Estimand — BILUH / boyko-benchmark Stage 1

Written per `estimand-ops.md` (Full-Ladder tier: this is a research project
with a causal L0 classification). Fills the gap Stage-1 planning (ТЗ.txt)
left open: it requires "statistically meaningful separation from negative
controls" (§10, §11) but never states a threshold. That threshold is fixed
*here*, before any production run, not chosen after seeing results.

## L0 — Question Classification

**Causal**, of a specific and narrow kind: a fully-controlled in-silico
factorial experiment, not an observational study. The question is "what
does turning the adaptation rule on/off/to-a-different-rule change in the
graph's geometric observables, at matched initialization?" — a
counterfactual contrast the simulation can literally realize for both arms
of the comparison from identical starting conditions, which is the strong
form of a causal question (no adjustment for confounding needed; see
Identifiability below).

**Hard boundary:** this causal claim is about *the model*, not about
physical reality. "Adaptive dynamics causes geometric-observable
separation in this simulation" is answerable; "adaptive dynamics is why
the physical universe has 3 spatial dimensions" is a different, unaddressed
question (Gate B, out of scope — see `falsification_gates.md`).

## L1 — Estimand Attributes

**Population.** The set of achievable `(initial graph draw, RNG seed)`
realizations under the generative model fixed in `mathematical_contract.md`
§4 and `assumptions.md` A7, restricted by design to **connected graphs
only** (disconnected draws are rejection-sampled, not analyzed — see ICE
note below; this keeps "population" well-defined rather than needing an ICE
strategy for a structural non-event). One population per system size `N`
in the FSS grid (§6 of the contract); the estimand is evaluated separately
at each `N`, then the *scaling* of the estimate across `N` is itself a
second-order estimand (the FSS exponents `γ, η, δ`).

**Intervention.** Arm A (Active): `HebbianAdaptation` applied for a fixed
adaptation budget (`η`, number of `dτ` steps — held constant across the
comparisons below).

**Comparator.** Five distinct comparators, each isolating a different
possible confound or alternative mechanism — this is a factorial design,
not a single treatment-vs-control:

| Comparator | Isolates |
|---|---|
| B — Frozen | effect of adaptation itself (identical init, adaptation off) |
| C — Parameter-Matched Random | effect of *this specific* graph realization vs. any degree-matched graph |
| D — Topology Scrambled | effect of *Active's specific wiring* vs. its degree sequence alone |
| E — Fixed Flat Geometry | positive calibration anchor, not a negative control |
| F — Alternative Objective | effect of *this specific* adaptation rule vs. any local correlation-driven rule |
| CD — Classical Diffusion Control (added 2026-08-11) | effect of the unitary/quantum carrier vs. classical diffusion — **not directly against Active** (Arm CD necessarily uses the combinatorial operator `L`, since `L_norm` cannot support a conserved diffusion on an irregular graph, `[A18]`); the carrier-isolating comparison is Arm CD vs. the Operator-Independence Diagnostic's `L`-driven quantum rerun (`mathematical_contract.md` §2.2, §5.6), both using `L`, differing only in carrier |

**Endpoint.** The five Gate-A observables from `mathematical_contract.md`
§5, each as a per-`(arm, N, seed)` scalar (or fitted-parameter) measurement:
spectral-dimension plateau value and stability, Laplacian-gap scaling
exponent `γ`, IPR scaling exponent `η`, diameter scaling exponent `δ`,
propagation-front velocity `v_eff`.

**Summary measure.** Difference in means between Active and each
comparator at matched `N`, standardized as Cohen's `d` (continuous
endpoints throughout — no odds ratio / hazard ratio noncollapsibility risk
here, so this is the direct, collapsible choice already recommended by the
project's own EstimandOps rule).

**MCID.** `|Cohen's d| ≥ 0.8` **and** non-overlapping 95% confidence
intervals, both required simultaneously, between Active and each
comparator, on each Gate-A observable. (= `mathematical_contract.md` §7,
`assumptions.md` A10. Restated here because the estimand is where an MCID
is supposed to live — the contract cites it, this document owns it.)

### Intercurrent Events (ICE)

One genuine ICE identified: **numerical divergence of the unitary
integrator mid-run** (norm drift beyond the documented tolerance, §2 of the
contract) is a post-baseline event that changes what the endpoint measures
for that replicate.

- **Strategy: while-active.** Data up to the divergence point is retained
  for time-averaged quantities that don't require the full adaptation
  budget; the replicate's *final* observable values are only computed if
  ≥ 90% of the configured `dτ` budget completed before divergence.
  Replicates that diverge before that threshold are excluded and **counted
  explicitly** — `summary.csv` must report `n_attempted` and `n_used` per
  `(arm, N)` cell, never silently drop them into the denominator.

(Disconnected initial-graph draws are *not* treated as an ICE — they are
excluded from the population definition itself via rejection sampling,
per the Population field above. This is the cleaner fix per
`research-methodology.md`'s error classifier: a structural property known
before the run is a population-definition choice, not a post-baseline
event.)

## Identifiability (causal layer — all four checked)

This is a designed simulation experiment, not an observational study, so
identifiability is close to trivial by construction — stating it anyway
per the Full-Ladder requirement, because "obviously fine, it's just code"
is exactly the kind of unchecked premise `estimand-ops.md` exists to catch.

| Assumption | Check |
|---|---|
| **Consistency** | `Y = Y^a` when arm `A = a` holds by construction — the simulator directly executes the specified `AdaptationRule` for the assigned arm; there is no ambiguity about "which version of the treatment" was received (single implementation, deterministic given seed). |
| **Positivity** | Trivially satisfied — arm assignment is a config choice, not an observed/selected variable; every arm is run at every `N` with the full seed budget by protocol, `P(A=a | N) = 1` for the arm actually run (not a probabilistic assignment at all, which is the strongest possible form of positivity). |
| **Exchangeability** | By design: Active, Frozen, and Alternative Objective share bit-identical `(M(0), W(0), ψ(0))` and seed stream (`mathematical_contract.md` §4 shared-initialization rule) — there is no confounder that differs between these three arms except the intervention itself. Comparators C, D, E are deliberately *not* exchangeable with A in the same sense (they isolate different mechanisms, per the Comparator table) — they are not naive counterfactuals of A, and no claim here treats them as such. **Revised 2026-08-11 (DDD skeptic finding #5):** this earlier wording stated the non-exchangeability without drawing its consequence explicitly enough — see the corrected Primary vs. Secondary Comparator split immediately below, which G6's gating logic must respect. |

### Primary vs. secondary comparator (added 2026-08-11, skeptic finding #5)

Only **Active vs. Frozen** satisfies full exchangeability in the formal
causal sense (identical initialization, single intervention differs) —
this is the only comparison this estimand licenses as a strict causal
contrast. **Active vs. C/D/E are matched non-exchangeable comparisons**:
each isolates one specific alternative construction (a different random
graph with matched degree; the same degree sequence rewired; a periodic
lattice), but a difference observed there licenses only the narrower claim
*"this specific alternative construction does not reproduce Active's
signature,"* not a formal average-treatment-effect statement in the
Neyman–Rubin sense. `falsification_gates.md`'s G6 still gates on all three
comparators (per ТЗ.txt's own design intent — testing against *multiple*
distinct null models is deliberately more falsifying than testing against
one), but the causal-inference weight the three carry is not uniform:
Frozen is the causal anchor, C/D/E are mechanism-isolation diagnostics. Do
not describe a C/D/E separation, in any report, using language ("causes,"
"the effect of adaptation is X") that implies the same exchangeability
Frozen alone provides.
| **SUTVA** | Each seed is an independent simulation replicate; no interference between replicates (independent RNG streams, `[A11]`); no hidden treatment version (single `AdaptationRule` implementation per arm, config-frozen for the whole experiment). |

**Identification strategy:** design-based — equivalent to a factorial
randomized controlled experiment where "randomization" is replaced by
direct, deterministic, matched assignment (stronger than randomization,
since there is no assignment-mechanism confounding possible at all). No
adjustment model, no propensity score, no instrument needed.

## Estimator

Direct difference-in-means / Cohen's `d` on simulation output, aggregated
via ordinary least-squares regression across the FSS grid for the scaling
exponents (`γ, η, δ`) — matches the design-based identification strategy;
no doubly-robust or IPW machinery is needed because there is no
confounding to adjust for (see Identifiability above). Reference:
`docs/estimand-to-estimator-map.md` convention: design-based identification
→ direct estimator, not a model-based backup.

## Sensitivity Analyses (≥2 required, Full-Ladder)

1. **Alternative ICE strategy.** Re-run the Gate-A verdict machine treating
   integrator divergence as *composite* (any divergence before full budget
   = automatic Gate-A FAIL for that replicate) instead of *while-active*
   truncation. If the Stage-1 verdict flips between the two ICE strategies,
   the result is ICE-strategy-dependent and must be reported as `[WEAK]`,
   not promoted cleanly.
2. **Robustness to `(K, η)`.** `assumptions.md` A9 already flags that the
   fast/slow timescale-separation window `K` (default 50) and adaptation
   rate `η` are arbitrary starting points requiring a sweep before trust.
   This sensitivity analysis *is* that sweep: re-run the Active-vs-Frozen
   comparison (the core separation the whole hypothesis rests on) across a
   small grid of `(K, η)` values and confirm the qualitative separation
   (sign and rough magnitude of the effect, not necessarily the exact
   Cohen's `d`) is stable. A result that only appears for one specific
   `(K, η)` pair is a calibration artifact, not a geometric-phase
   candidate.

## Natural Language Statement

*We estimate the standardized mean difference (Cohen's d) in five
geometric observables (spectral-dimension plateau, Laplacian-gap exponent,
IPR exponent, diameter exponent, propagation-front velocity) between the
Active arm and each of five comparator arms (Frozen, Parameter-Matched
Random, Topology Scrambled, Fixed Flat Geometry, Alternative Objective),
across a finite-size-scaling grid of network sizes N, handling integrator
divergence via a while-active truncation strategy, in a fully-controlled
simulation with design-based identification.*

## What This Result Does NOT Mean

1. Does **not** establish anything about physical spacetime, Lorentz
   invariance, gravity, or gauge structure — Gate B is out of scope by
   construction (`falsification_gates.md`).
2. Does **not** generalize beyond the specific rule and parameterization
   tested — `HebbianAdaptation` with the correlation-rule form fixed in
   `mathematical_contract.md` §3.2, at the `(K, η)` values actually swept.
   A different functional form for the adaptive rule is an untested,
   separate hypothesis (Minimal Relaxation Rule: change one assumption at
   a time, new experiment ID).
3. Does **not** establish that adaptive dynamics is *necessary* for the
   observed geometric signature, only that this specific rule is
   *sufficient* to produce it and *distinguishable* from the tested
   negative controls. Other, untested mechanisms could conceivably produce
   a similar signature.
4. Even a full `SURVIVES_GEOMETRIC_PHASE_SCREEN` verdict is a Stage-1
   candidate screen bounded by the FSS grid actually run (`N ≤ 512` in
   development, whatever the production grid extends to) — it says nothing
   about behavior at system sizes beyond what was tested.
5. **Does not license a uniform causal claim across all three negative
   controls** (added 2026-08-11, skeptic finding #5) — only the Active vs.
   Frozen contrast is a formally exchangeable causal comparison. Separation
   from Parameter-Matched Random, Topology Scrambled, or Fixed Flat
   Geometry supports the narrower claim "this specific alternative
   construction doesn't reproduce it," not a Neyman–Rubin average
   treatment effect. See § Primary vs. secondary comparator above.
