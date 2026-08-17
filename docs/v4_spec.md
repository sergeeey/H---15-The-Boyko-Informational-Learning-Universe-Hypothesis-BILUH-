# V4 — Autonomous Topology Dynamics: Technical Specification

**Status: PROPOSED, 2026-08-14. Not approved. Nothing implemented, nothing run.**

**Revision 1 (2026-08-14, same day, before M1 — legitimate pre-
registration refinement, not a post-hoc fit).** The user reviewed the
original spec and an external critique of it, accepted the parts that
strengthened the design, and rejected the parts that would have added
unmotivated new degrees of freedom or overclaimed physics. Changes in
this revision, each explained where it appears below:

1. Causal framing sharpened to explicit potential outcomes over whole
   simulation *runs* as the unit, with the causal claim scoped
   explicitly to "within this simulator" (§1).
2. Independent seed streams enumerated explicitly — six, not one (§3).
3. **The primary comparator is redefined.** Arm A4 is no longer "random
   regrowth matched to A3's distance profile" (which requires assuming a
   functional form for how selection probability depends on distance).
   It is now a **distance-stratified shuffle of the real `C_ij` values**
   — permute correlations only among candidate pairs at the same graph
   distance, then apply the identical deterministic Top-K rule. This
   preserves the event count, the `C_ij` distribution, and the
   correlation-vs-distance dependence, destroying only pair-specific
   information. `Δ_specific = Y(A3) − Y(A4)` is now the **primary**
   estimand; the original naive-uniform-random arm is kept as `A2`, a
   secondary diagnostic (§4, §5).
4. **K1 is redefined around edge recovery, not spectral appearance.**
   Primary K1 endpoint is the fraction of genuinely-corrupted lattice
   edges V4 actually restores, `R_edge` — spectral observables
   (`d_s`, `λ₂`, IPR, conductance) are demoted to secondary. A metric can
   look "more lattice-like" without recovering the actual damaged edges;
   `R_edge` cannot be gamed that way (§7).
5. **New kill criterion, topology churn `χ`** — the fraction of edges
   that are pruned and re-added repeatedly. An effect that only appears
   at `χ → 1` is oscillatory rewiring, not stable emergent structure,
   and is a separate failure mode from K1–K4 (§7).
6. **Four frozen predictions (`P1`–`P4`)** stated before any run, so the
   verdict is checked against a pre-committed target, not read off the
   data after the fact (§7b, new).
7. **§12 is now decided, not open**: deterministic Top-K is the primary
   rule. Stochastic/temperature-based regrowth (`Softmax` over `C_ij/T`)
   is explicitly deferred to a possible future robustness extension,
   never as V4's confirmatory test — it adds an unmotivated new
   parameter (`T_topo` and its schedule) at exactly the moment this
   project's anti-fishing discipline says not to.
8. **Explicit guardrails added, to preempt scope drift during
   implementation** (§4, §12): the candidate regrowth set is ALL
   non-adjacent pairs, never restricted to a local hop radius — an
   `r`-hop restriction would bake locality into the mechanism and then
   "discover" it, i.e. target leakage against an emergent-locality
   claim. A global Top-K over all candidates is labelled exactly as what
   it is — a nonlocal algorithmic prior in the simulation's update rule
   — never described as a proven Lieb–Robinson violation, which is a
   much stronger and untested physical claim this spec does not make.
   No stochastic regrowth mechanism in this spec is described as
   physically isomorphic to quantum vacuum fluctuations or as
   instantiating a physical temperature; that reading is not licensed by
   anything derived here and is explicitly rejected if proposed later.

This document is a pre-registration: written and committed BEFORE any V4
measurement, so its pass/fail predicates cannot be reshaped to fit
results (`~/.claude/rules/estimand-ops.md`, "estimand defined after data
access" anti-pattern). Same discipline as `docs/phase12_spec.md`.

**V4 is a NEW research programme, not a continuation of Phase 11–12.**
Its claim is different, its estimand is different, and — critically — its
null models and controls must be rebuilt from scratch, because every
control in `[A41]`/`[A44]` was calibrated for a *fixed* topology.

Read `docs/final_knowledge_map.md` first. This spec's §9 lists exactly
what does and does not carry over from Phase 11–12, so V4 does not
silently re-inherit killed assumptions.

---

## 1. L0 Gate (EstimandOps — mandatory first step)

**Question type: CAUSAL, identified by simulation design — with the
experimental unit defined as the WHOLE RUN, not a node or an edge.**

This is a deliberate change from Phase 11–12, which were classified
*descriptive* throughout and therefore forbade causal language.

**Experimental unit and potential outcomes (Revision 1 — sharper than
the original draft).** A unit is one full simulation trajectory
`u = (G₀, ψ₀, ξ, seed streams)` — an entire run, not a node or an edge
within it. This choice matters: node- or edge-level interference
(one node's neighbourhood affecting another's) is *part of the
mechanism under study*, not a violation to control for — the standard
network-experiment SUTVA concern (unit-level interference through the
network) does not apply once the unit is the whole graph trajectory,
because there is no *other* unit for a run to interfere with. Each arm
defines a policy applied to the same unit type; potential outcomes are
`Y_SDR(u)` (state-driven regrowth policy) and `Y_control(u)` (a control
policy — `A4`, §3), and the estimand is

```
τ = E_u[ Y_SDR(u) − Y_control(u) ]
```

— an ordinary interventional causal estimand *within a fully specified
computational model*, identified by construction because we choose the
policy.

Identifiability, checked rather than assumed:

| Assumption | Status in V4 |
|---|---|
| Consistency | Satisfied by construction — the intervention IS the rule we set; there is no ambiguity about "version of treatment" |
| Positivity | Satisfied — every seed can receive any arm; assignment is by design, never data-dependent |
| Exchangeability | Satisfied by construction — arms share bit-identical initial `(M₀, W₀, ψ₀)` and independent seed streams (§3); there are no unmeasured confounders in a fully specified simulation |
| SUTVA (unit-level) | Satisfied — units are independent runs (whole trajectories), not nodes; there is no cross-unit interference to violate. Within-run node interaction is the mechanism, not a threat to inference. |

**Consequence, and this is the point of doing the gate honestly:** if
`Δ_specific` exceeds MCID, the phrasing *"state-driven regrowth causes
more organization than the distance-conditioned control, within this
simulator"* **is licensed** — unlike Phase 11–12, where causal phrasing
was forbidden. This is a stronger epistemic position, earned by a
cleaner design, not by relaxing standards.

**Hard scope limit, stated explicitly so it cannot drift during
implementation:** every causal statement V4 can license is of the form
*"in this simulation model, replacing the control regrowth policy with
the state-driven one changes Y."* **Never** *"in the physical universe,
state-driven regrowth causally creates geometry."* External validity
(does this computational causal claim say anything about physical
reality) is a separate, harder question this spec does not attempt to
answer, and no result from V4 closes it.

**Still forbidden regardless of outcome** (`CLAUDE.md` scientific
boundary, unchanged): claims about physical spacetime, Lorentz
invariance, quantum gravity, or BILUH confirmation. The
`docs/falsification_gates.md` grep canary applies.

---

## 2. Decision Gate — the three questions, answered before proceeding

The user-proposed gate for whether V4 deserves a campaign at all. All
three must be "yes".

### Q1. Is there a genuinely new mechanism, not just a harsher threshold?

**Yes, and `[A47]` proves it.** `[A47]` established that `W = 1` is an
**absorbing upper barrier**: for `HebbianAdaptation`, no weight can ever
exceed its initial value, under any budget, any initial state, any noise.
The rule can differentiate edges only by *decay*.

V3/V3b changed *when* an edge is deleted — still a pure function of `W`,
still inside the regime `[A47]` bounds. **V4 introduces edge
CREATION**, which is not a `W`-growth event at all: it is a change of the
*support* of `W`, mathematically outside `[A47]`'s scope. The theorem
that explains why every prior variant failed **does not apply** to this
mechanism.

This is AOG-5 compliant: the motivation is a proven structural property
of the apparatus, established without reference to whether the hypothesis
is true — not "the last four things failed, try a fifth".

### Q2. Is there an observable that separates specific structural learning from generic pruning/rewiring?

**Yes — by design, not by hope.** The primary estimand is a contrast at
**matched edge budget** (§3): arms A3 and A4 delete the same edges at the
same rate and add the same *number* of edges, using the identical
selection algorithm applied to the identical `C_ij` value multiset — the
only difference is *which specific pair*, among pairs at the same graph
distance, gets connected. A difference between them cannot be
attributed to edge-count change, density change, distance structure, or
pruning per se (§5).

### Q3. Can a kill criterion be stated in advance, without parameter rescue?

**Yes — four of them, §7**, including one cheap gate (§7, K1) that can
kill V4 before the main campaign runs.

**Decision Gate verdict: PASS.** V4 is a legitimate new programme.

---

## 3. Estimand (EstimandOps L1)

| Field | Value |
|---|---|
| **Population** | Connected Erdős–Rényi graphs, N = 512, mean degree 6 (`n_edges = 3N`, `[A7]`), generated by `generate_erdos_renyi` with the `[A38]` retry discipline |
| **Intervention** | A3: prune lowest-weight edges at rate ρ per adaptation window, regrow the same number by highest time-averaged correlation `C_ij` among non-adjacent pairs (deterministic Top-K, §12) |
| **Comparator (primary)** | A4: identical pruning, regrow the same number by Top-K on a **distance-stratified shuffle** of the same `C_ij` values (§5) — isolates pair-specific information from distance structure |
| **Comparator (secondary/diagnostic)** | A2: identical pruning, regrow the same number by Top-K on **uniformly-drawn** values, ignoring distance entirely — `Δ_naive`, §3 |
| **Endpoint** | Structural excess of Forman-Ricci curvature under the §6 null models (primary); G1 plateau, conductance, ARI partition stability (secondary) |
| **Summary measure** | Difference in means across independent seeds (absolute difference — never a ratio, per the noncollapsibility rule) |
| **MCID** | `\|Cohen's d\| ≥ 0.8` **AND** non-overlapping 95% CIs — both required, unchanged from `docs/estimand.md` |

**Primary estimand (Revision 1 — promoted from what was previously the
secondary "confound isolation" contrast, because it is the sharper of
the two, §5 explains why):**

```
Δ_specific = Y(A3) − Y(A4)        [matched edge budget, matched distance-vs-correlation dependence]
```

**Secondary estimand (diagnostic — how much of the total effect is just
"any correlation-based regrowth beats naive-uniform regrowth", including
the trivial distance confound §5 names):**

```
Δ_naive = Y(A3) − Y(A2)           [matched edge budget only]
```

**Natural-language statement, written before any results exist:**

> We estimate the difference in mean curvature structural excess for
> connected ER(512, 1536) graphs, comparing correlation-driven edge
> regrowth against a distance-stratified shuffle of the same correlation
> values (same Top-K rule, same event count, same distance-dependence of
> the correlation magnitude — differing only in which specific pair at
> a given distance is connected), at matched edge budget, handling
> disconnection events by the `while-active` strategy (run truncated and
> flagged, never silently repaired).

**Independent seed streams (Revision 1 — six, not one).** "Same seed" is
insufficient once arms consume the RNG a different number of times (A3's
Top-K tie-break, A4's within-stratum shuffle, and A2's uniform draw are
different operations); reusing one seed naively lets streams drift apart
after the first extra draw despite nominally matching. Per `[A11]`'s
`SeedSequence.spawn` discipline (already used throughout this project),
six independent streams, spawned once per unit from a single top-level
seed:

```
graph_seed              -- initial G0 (generate_erdos_renyi, [A38])
initial_state_seed      -- psi0
carrier_noise_seed      -- PhenomenologicalOpenBackend's noise, if sigma>0
adaptation_seed         -- HebbianAdaptation (deterministic; reserved for a future stochastic rule)
topology_tiebreak_seed  -- deterministic Top-K's tie-break only (exact C_ij ties)
control_regrowth_seed   -- A4's within-stratum shuffle; A2's uniform draw
```

**Intercurrent events (ICE) and their strategies:**

| ICE | Strategy |
|---|---|
| Pruning disconnects the graph | **while-active** — truncate the run at that window, flag it, report the rate. Never silently reconnect (that would be an undeclared intervention). Rate > 20% of runs ⇒ ρ is too aggressive, the whole grid is invalid and must be re-pre-registered, not patched. |
| A weight hits exactly 0 (`[A42]`'s clamp) | **composite** — folded into the prune rule; a zero-weight edge is by definition among the lowest-weight edges, so it is pruned by the rate rule rather than by a separate mechanism |
| Regrow candidate set is empty (graph near-complete) | Cannot occur at mean degree 6, N=512 (density ≈ 1.2%). Asserted as an invariant, not assumed. |

---

## 4. Arms

All arms share bit-identical initial `(M₀, W₀, ψ₀)` and seed streams
(the shared-initialization rule from `mathematical_contract.md` §4).
Fast dynamics, adaptation rule (`HebbianAdaptation`), and budget are
identical across arms — **only the `TopologyUpdateRule` differs**.

| Arm | Prune | Regrow | `\|E\|` over time | Role |
|---|---|---|---|---|
| **A0** | none | none | constant | Baseline = Phase 11–12's exact configuration |
| **A1** | rate ρ, lowest-`W` | none | decreasing | Isolates the effect of pruning alone |
| **A2** | rate ρ, lowest-`W` | uniform random among non-edges | **constant** | Secondary/diagnostic comparator — naive baseline, §3's `Δ_naive` |
| **A3** | rate ρ, lowest-`W` | deterministic Top-K on `C_ij` among non-edges (§12) | **constant** | **Intervention** |
| **A4** | rate ρ, lowest-`W` | deterministic Top-K on a **distance-stratified shuffle** of `C_ij` (§5) | **constant** | **Primary comparator** — `Δ_specific`'s control arm |

**All four regrowth-capable arms use the identical deterministic Top-K
selection rule** (§12) — arms differ only in what values that rule sorts
on, never in the selection algorithm itself. This is what makes `A3` vs
`A4` a clean contrast of *information content*, not of *algorithm*.

**Rate-based, not threshold-based — this is the specific fix for V3/V3b's
`UNDEREXPOSED` verdict.** `[A51]`/`[A52]` failed to test anything because
a threshold rule almost never fired (1 edge in 7680; the weight
distribution had no mass in the targeted gap). A *rate* rule fires
exactly ρ·|E| times per window **by construction** — the mechanism is
guaranteed to be exercised, which is precisely what V3/V3b lacked.

**Frozen parameters (pre-registered, not to be tuned after seeing
results):**

- `ρ = 0.01` (1% of edges per window) → ~15 edges/window at N=512,
  cumulative turnover ≈ 40% over 50 windows.
- Regrowth uses **signed** `C_ij` (highest positive), matching Hebbian
  logic that positive correlation warrants connection.
- **Persistence requirement:** an edge is eligible for pruning only if it
  has been in the lowest-ρ set for `m = 3` consecutive windows. This
  prevents thrashing on transient fluctuations and makes deletion a
  statement about *sustained* low utility, not a coin flip. `A_ij` thus
  carries genuine state — the defining feature of V4.

Exactly one nonzero ρ level. No sweep. Any later ρ change requires a new
dated pre-registration (`[A9]`'s report-the-landscape-never-chase-a-winner
discipline).

---

## 5. The confound that would fake a positive result — named and controlled

**The risk, stated plainly before running:** `ψ` spreads over the graph,
so nodes that are *close in graph distance* have correlated `ψ`. A rule
that grows edges where `C_ij` is highest may therefore simply connect
already-nearby nodes — producing a short-range-dominated topology that
*looks* lattice-like and would score well on curvature and G1, for
reasons having nothing to do with learning. Any diffusion process would
do the same.

**This is the single most likely way V4 produces a false positive**, and
it is why arm A4 exists as the PRIMARY comparator, not a secondary check.

**Control A4 (Revision 1 — redefined as a distance-stratified shuffle of
the real correlations, not a random draw matched to an assumed
distance-vs-probability functional form):**

1. Compute the graph distance `d_G(i,j)` for every non-adjacent
   candidate pair.
2. Bin candidates into distance strata (e.g. `d=2`, `d=3`, `d≥4`).
3. **Permute the real `C_ij` values only within each stratum** — a pair
   at distance 2 gets some other distance-2 pair's correlation value,
   never a distance-5 pair's.
4. Apply the **identical deterministic Top-K rule** to the permuted
   values.

Formally: `A4`'s selection statistic is `π_{d_G}(C_ij)`, a
distance-respecting random permutation of `A3`'s own `C_ij`.

**Why this is a strictly stronger null than the original "random draw
matched to A3's distance profile":** that version required assuming
*some* functional form for how selection probability depends on
distance (e.g. the previously-considered `∝ e^{-d}}`) — an unmotivated
modeling choice, not a fact about the mechanism. The stratified-shuffle
version needs no such assumption. It exactly preserves: the number of
regrowth events, the marginal distribution of `C_ij` values, and the
*empirical* dependence of correlation magnitude on distance (whatever
that dependence actually is in a given run — not assumed a priori). It
destroys exactly one thing: which specific pair, among pairs at the same
distance, gets connected. `Δ_specific = Y(A3) − Y(A4)` therefore
isolates **pair-specific state information, conditional on the
graph-distance structure** — a sharper question than "does
correlation-based regrowth beat regrowth that ignores distance
entirely" (which `Δ_naive`, §3, already answers and is expected to be
positive for the trivial reason named above).

**Reading the four possible outcomes** (§7b's `P3` makes this a frozen
prediction, not a post-hoc interpretation):

- `Δ_specific ≈ 0` (A3 ≈ A4) ⇒ **strong negative result**: state-specific
  correlations add nothing beyond what distance-conditioned generic
  regrowth already gives. The V4-specific learning claim is dead — kill
  (K2, §7).
- `Δ_specific > MCID`, but only on G1 and not on curvature/conductance
  jointly ⇒ suspected metric artifact, not confirmed structure.
- `Δ_specific > MCID` on curvature **and** conductance **and** G1
  jointly (or the substrate-gate-adjusted equivalent, §6) ⇒ the only
  outcome that actually supports the V4 claim: pair-specific state
  information causally matters, beyond distance structure, within this
  simulator.

**Second confound — carrier irrelevance.** If the effect is reproduced
with a *classical diffusion* carrier (`dp/dt = −Lp`, Arm CD's machinery,
`[A18]`) plus the same regrow rule, then the quantum dynamics contributes
nothing and the result is about diffusion on graphs, not about this
project's hypothesis. **Kill (K4)** if so.

---

## 6. Null models — rebuilt, because the old ones do not transfer

**`[A41]`/`[A44]`'s nulls permute weights among a FIXED edge set.** In V4
the edge set itself changes, so those nulls no longer isolate what they
were built to isolate. Using them unchanged would be a silent inheritance
error of exactly the kind `docs/final_knowledge_map.md` exists to prevent.

| Null | What it destroys | What it preserves |
|---|---|---|
| **N1 — degree-preserving rewire** (configuration model on the final graph) | which specific pairs are connected | degree sequence, edge count |
| **N2 — weight shuffle on final topology** (`[A41]`'s, still valid *within* the final edge set) | which weight sits on which edge | weight multiset, final topology |
| **N3 — strength-stratified shuffle** (`[A44]`'s, unchanged) | fine structure beyond node strengths | node strength profile |

Primary structural excess for V4 is measured against **N1**, which is the
null appropriate to a changing topology. N2/N3 are reported alongside for
continuity with Phase 12's recorded numbers.

**Substrate gate (FL Step 2a), mandatory before any verdict:** re-run
`[A40]`'s partition-stability check on V4's final graphs. `[A40]` found
the partition is *not a stable object* on near-random graphs (ARI ≈ 0.13
under 1% perturbation vs. 0.997 on a planted-community graph). If V4's
graphs become genuinely structured, ARI stability should **rise** — which
turns `[A40]`'s negative finding into a **positive diagnostic**. If ARI
stays ≈ 0.13, any modularity-based claim about V4 is inadmissible for the
same reason it was in Phase 12.

---

## 7. Kill criteria — pre-registered, in evaluation order

**K1 — the damaged-lattice restoration gate (cheap, runs FIRST;
Revision 1 — redefined around edge recovery, not spectral appearance).**
Take a periodic cubic lattice `G*` (N = 512, the `[A32]`/T7 positive
control), corrupt it by randomly rewiring 10% of its edges to get
`G_damaged`, and run V4's full machinery starting from `G_damaged`.

**Primary K1 endpoint — edge recovery fraction:**

```
R_edge = |E_recovered ∩ E*| / |E_damaged_out ∩ E*|
```

where `E_damaged_out` is the set of correct lattice edges that were
actually removed by the corruption, and `E_recovered` is the final
graph's edge set. `R_edge` answers precisely: *of the specific edges
that were actually broken, what fraction did V4 correctly restore?*
Report the wrong-edge-removal rate alongside it (correct edges V4
deletes that were never damaged).

**Why edge recovery, not spectral improvement, is primary:** distinct
graphs can have similar-looking spectra (`d_s`, `λ₂`, IPR, conductance)
without sharing the specific edges that make a lattice a lattice — a
spectral-only criterion could be satisfied by a rule that improves the
*appearance* of geometry without recovering the *actual* damaged
structure, which K1 exists specifically to rule out. `d_s`, `λ₂`, IPR,
and conductance remain **secondary** endpoints, reported alongside.

- **PASS** requires `R_edge(A3) > R_edge(A4)` (§4's distance-stratified
  control, not the naive `A2`) — V4 must recover more of the genuinely
  damaged edges than a rule that only knows the distance-vs-correlation
  dependence, not the specific pairs.
- If A3 does not beat A4 on `R_edge`, V4's rule cannot restore a
  *near-solution* using pair-specific information, so it certainly
  cannot create structure from a random graph using it. **Stop before
  the main campaign.**

This is a genuine positive control that Phase 11–12 never had, and — with
the edge-recovery endpoint — a harder one to satisfy by accident than a
purely spectral criterion would be.

**K2 — no specificity.** `Δ_specific = Y(A3) − Y(A4)` 95% CI contains 0
⇒ pair-specific information (beyond distance-conditioning) does not
matter ⇒ V4's central claim is dead. Report as a clean negative result
(§5's first bullet).

**K3 — distance already explains everything (redefined in terms of the
new primary/secondary pair).** `Δ_naive = Y(A3) − Y(A2)` (§3) is large
and MCID-passing, but `Δ_specific` (K2) is not ⇒ the entire apparent
effect over a naive baseline is attributable to distance-conditioning
alone, with no pair-specific contribution once distance is controlled
for. Not learning — the §5 short-edge artifact, now diagnosed directly
by the difference between the two estimands rather than a separate
distance metric.

**K4 — carrier-irrelevant.** Classical diffusion reproduces the effect
⇒ the quantum carrier is doing no work; downgrade to a
diffusion-on-graphs result and stop treating it as evidence for this
project's hypothesis.

**K5 — topology churn (Revision 1, new).** Define

```
χ = (# edges toggled repeatedly, e.g. pruned then re-added then re-pruned) / (# topology events)
```

and separately the pure 2-cycle rate (an edge removed then immediately
regrown next window). If any apparent organization signal is present
only when `χ → 1` (topology in constant oscillatory flux, never
settling), that is not stable emergent structure — it is the rate rule
thrashing. Cheap to compute from the same run, no extra simulation. Threshold:
flag if `χ > 0.3` on any arm; investigate before trusting that arm's
`Δ_specific`. `0.3` is a round, un-calibrated heuristic (`[WEAK]`
sourced, per `~/.claude/rules/evidence-markers.md`) chosen only to be
low enough to catch obvious thrashing — not derived from any data, and
should be revisited once `M1`'s implementation gives a real churn
distribution to calibrate against.

**Explicitly NOT a kill criterion:** G1 failing to converge. `[A36]`/
`[A39]` already established G1 does not converge for this project's
open-system graphs; that is a known property of the observable, not
evidence about V4.

---

## 7b. Frozen predictions (Revision 1, new) — checked against the data, not read off it

Stated before any V4 run exists, so the verdict is a comparison against
a pre-committed target rather than a post-hoc narrative.

**P1 — exposure.** `N_topology_events ≈ ρ·|E|·K` per arm (rounded to the
nearest integer per window), matching the rate rule's own definition. If
not satisfied, that is an **implementation bug**, not a scientific
finding — fix and re-verify before M4.

**P2 — K1 recovery.** `R_edge(A3) > R_edge(A4)` (§7's K1). If false:
`K1 FAIL ⇒ STOP` before the main campaign.

**P3 — main causal contrast.** `Δ_specific = Y(A3) − Y(A4) > MCID`
(§3, §5) — not merely `Y(A3) > Y(A0)`, which would not isolate anything
specific to pair-level information.

**P4 — scale stability.** As `N` increases (if a larger-N follow-up ever
runs), `Δ_specific` should not vanish. Not tested in the initial M4
campaign (N=512 only) — recorded here as the standard this project
already applies elsewhere (`[A39]`'s own finding that some effects are
N-dependent in ways that matter) so a future N-sweep has a frozen target
rather than an ad hoc one.

---

## 8. Milestones (each gates the next)

| # | Deliverable | Gate |
|---|---|---|
| **M0** | Dated addendum to `mathematical_contract.md` §3.3 defining `A_ij` as an independent state variable with memory; this spec committed | Contract must be revised before code, per `CLAUDE.md` |
| **M1** | `StatefulTopologyRule` infrastructure + TDD tests: edge-budget invariant (A2/A3/A4 have identical `\|E\|` at *every* window, not just the end), connectivity invariant, persistence counter, no-self-loop/symmetry invariants, six independent seed streams (§3) | All tests green before any science |
| **M2** | **K1 damaged-lattice restoration gate** (`R_edge(A3)` vs `R_edge(A4)`, §7) | **KILL GATE** — stop here if `P2` fails |
| **M3** | Null-model recalibration (N1 built and validated; `[A40]` ARI substrate gate re-run) | Substrate must be trustworthy before verdicts |
| **M4** | Main campaign: A0–A4, N = 512, ≥ 10 seeds (A4 is now core to computing the primary estimand, §3/§5 — not a separate confound-control run) | K2/K3 evaluated; churn (K5) checked on every arm |
| **M5** | Carrier-irrelevance control: classical diffusion + the same regrow rule | K4 evaluated |
| **M6** | Analysis freeze + verdict + `null_results/` entry if REJECT | — |

---

## 9. What carries over from Phase 11–12, and what does not

**Carries over (established, still true):**
- `[A47]`'s theorem — still bounds `W` growth; V4 works *around* it via
  topology, does not refute it.
- `[A42]` — the clamp still creates zero weights; folded into the prune
  rule as a composite ICE.
- `[A55]` — Forman-Ricci is scale-invariant (depends only on weight
  ratios). Still true, still means curvature is a ratio statistic.
- `[A36]`/`[A39]` — G1 needs N ≥ 512 and may not converge at all.
- `[A38]` — connectivity discipline for ER generation at large N.
- The MCID definition, seed discipline, provenance capture.

**Does NOT carry over (must be rebuilt or re-derived):**
- `[A41]`/`[A44]`'s null models — built for fixed topology (§6).
- `[A40]`'s partition-instability finding — was measured on *near-random*
  graphs; V4's graphs may differ, so it must be **re-measured**, and its
  result becomes a diagnostic rather than a fixed fact.
- Phase 11–12's descriptive L0 classification — V4 is causal (§1).
- Any intuition that "topology barely changes" — that was V3/V3b's
  `UNDEREXPOSED` regime, deliberately fixed by rate-based pruning (§4).

**Unresolved and untouched by V4:** `[A45]`'s anomaly (shuffled
correlations produce more curvature excess than real ones) remains open.
V4 does not test it and must not be read as bearing on it.

---

## 10. What a V4 result will NOT mean

Written before results, per EstimandOps requirement:

1. Does **not** establish emergent physical geometry, spacetime, or any
   BILUH claim.
2. Does **not** generalize beyond ρ = 0.01, m = 3, N = 512, or this
   adaptation rule.
3. A positive `Δ_specific` establishes that *correlation-driven regrowth
   differs from random regrowth* — **not** that the resulting structure
   is geometric. Geometry is a separate claim requiring the observables
   to actually converge, which `[A39]` gives no reason to expect.
4. Does **not** revive Phase 11–12's REJECT. That verdict stands on its
   own evidence regardless of V4's outcome.

---

## 11. Cost estimate

Based on this session's measured timings (~40 s per N=512 run of 50
windows; `[A39]`'s N=1024 measurement showed ≈ N² scaling in practice):

| Stage | Cost |
|---|---|
| M1 infrastructure + tests | ~half a day of implementation |
| M2 K1 gate (A3 + A4, 5 seeds) | ~10 min compute |
| M3 null recalibration | ~15 min compute |
| M4 main campaign (A0–A4, 5 arms × 10 seeds) | ~40 min compute |
| M5 carrier-irrelevance control (classical + regrow, 10 seeds) | ~15 min compute |

Added per-window cost of the regrow rule: `C_ij` over all non-adjacent
pairs is O(N²) ≈ 262 k values at N = 512 — negligible in NumPy relative
to the existing propagation step.

**Total: roughly one day of implementation, ~1.5 h of compute.**
Comparable to Phase 12, materially cheaper than Phase 11.

---

## 12. Regrowth selection rule — DECIDED (Revision 1; was an open question, now resolved before M1)

**Decision: deterministic Top-K, with a seeded tie-break used only on
exact numerical ties in `C_ij`.** Not stochastic, not a Boltzmann/softmax
rule over a temperature parameter, for this confirmatory run.

`Regrow(G, C) = argtop_m { C_ij : (i,j) ∉ E }` — every arm that regrows
edges (`A2`, `A3`, `A4`) uses this identical selection algorithm,
differing only in what values it is applied to (§4). This is what makes
`A3` vs `A4` a contrast of information content, not of algorithm.

**Why deterministic, decided now rather than left open:**

- **Minimises new degrees of freedom.** The budget already has one free
  parameter, `ρ`. A softmax rule adds a temperature `T_topo`, and a
  temperature all but inevitably invites a schedule `T_topo(τ)` and a
  cooling regime — turning one pre-registered parameter into an
  unbounded family `(ρ, T₀, schedule, ...)`. This project's whole
  anti-parameter-fishing discipline (`[A9]`, `null_results/2026...`'s
  Relaxation Map, `[A52]`'s explicit refusal to chase a threshold near
  the observed weight minimums) exists precisely to prevent this kind of
  drift.
- **Sharper falsifiability.** A deterministic rule cannot be rescued by
  "the temperature was wrong" if `A3` loses to `A4` — the K1/K2 verdicts
  are clean, not confounded by an unexplored hyperparameter.
- **No physical interpretation is claimed or needed.** A softmax over
  `C_ij/T` is a standard, well-understood sampling technique (Gibbs/
  softmax selection) — using it would not by itself be objectionable.
  What is explicitly rejected is treating `T_topo` as a *physical*
  temperature, or treating stochastic edge creation as *isomorphic to*
  quantum vacuum fluctuations. Neither claim is derived by anything in
  this spec, and no future revision should assert either without a
  separate, explicit argument — this is a guardrail against a plausible
  but unsupported drift in interpretation during implementation, not a
  comment on any specific external proposal.

**Stochastic regrowth is deferred, not abandoned.** If the deterministic
V4 survives K1 and shows `Δ_specific > MCID`, a stochastic robustness
extension (does the effect survive if selection is probabilistic rather
than a hard cutoff?) is a legitimate, separately pre-registered follow-up
— strictly *after* a positive deterministic result, never as the first
confirmatory test. Running the stochastic version first would mean V4
enters its own campaign already carrying an unexplored, unmotivated
extra parameter, which is exactly the failure mode this section exists
to prevent.
