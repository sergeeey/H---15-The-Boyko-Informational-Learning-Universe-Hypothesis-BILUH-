# NULL RESULT — Open-System Geometrogenesis (Phases 11–12)

**Verdict: REJECT.** Recorded 2026-08-14 per
`~/.claude/rules/falsification-ladder.md`. Never delete; read this before
re-attempting anything in this space.

## The claim that was tested

That adding dissipation (`γ`) and/or stochastic noise (`σ`) to the
closed-system adaptive Hebbian network dynamics would produce geometric
or otherwise structured organization that the closed system did not —
detectable as a difference between the factorial cells
`C0 / Cγ / Cσ / Cγσ` on Gate-A observables.

Question type (EstimandOps L0): **descriptive** for Phase 12's analysis
layer; the underlying Phase 11 question was framed as descriptive
throughout. No causal claim was ever licensed.

## What was actually run

- Phase 11: full open-system backend (split-step SDE), T1–T10 regression
  suite, lattice positive control, 5-arm diagnostic package.
- Milestone 3/7 factorial grids: N=512 and N=1024, 10 seeds per cell,
  80 points total, all completed.
- Phase 12: partition-stability substrate gate, weight-shuffle null
  model, Forman-Ricci curvature, node-strength-stratified null,
  H1-vs-H0 correlation-specificity test.

## Why it was rejected — observable by observable

| observable | result | reference |
|---|---|---|
| G1 spectral dimension | never converged, 0/80 points, at N=512 and N=1024 | `[A39]` |
| Conductance | no MCID-passing separation at either N | `[A39]` |
| Modularity | large effect (d=7.7→13.9) but **structural excess ≡ 0** — fully reproduced by a null model that destroys all structure by construction | `[A41]` |
| Community partition | not a stable object on these graphs at all (ARI 0.13 under 1% perturbation vs 0.997 on planted communities); detector-independent, confirmed with Louvain | `[A40]` |
| Forman-Ricci curvature | real excess surviving node-strength control (d=7.47), **but shuffled correlations produce ~2× MORE of it than real ones** (d=−2.9, MCID met) | `[A43]`, `[A44]`, `[A45]` |

The decisive item is the last one: the only signal that survived every
null model turned out to be **anti-correlated with the hypothesis**.
Real dynamical correlations produce less structure than randomly
shuffled ones. That is not a null result in the weak sense ("we couldn't
tell"); it is a positive finding pointing the wrong way.

Magnitude context, which alone forbids an optimistic reading: the
surviving curvature excess is ~0.5% of the gap between a periodic cubic
lattice (F = −8.000 exactly) and a random graph (F ≈ −9.94), and it
moves `Cσ` *away* from the lattice value.

## What is NOT killed (do not over-read this document)

- **Every measurement stands.** Only interpretations collapsed. The
  numbers in `[A37]`/`[A39]`/`[A43]`/`[A44]` are correct and reproducible.
- **The infrastructure is sound and reusable**: open/closed dynamics
  backends, the T1–T10 suite, seed-space discipline, provenance capture,
  and — newly — a working null-model toolkit (global weight shuffle,
  strength-stratified shuffle, partition-similarity, curvature).
- **Other adaptation rules were never tested in open-system mode.**
  `AntiHebbianAdaptation` and `AlternativeObjective` exist in the
  codebase, unused here.
- **Only one `(γ̃,σ̃)` point was ever run** (0.05, 0.05), deliberately,
  per `[A35]`'s anti-parameter-fishing pre-registration.
- **No topology-updating arm was ever run.** `NoTopologyUpdate` forbids
  the one class of reorganization that would be most visible
  structurally.
- This says nothing about BILUH, spacetime, or physical geometry. It was
  never able to.

## Relaxation map — one assumption changed per variant

| variant | assumption changed | everything else held |
|---|---|---|
| V1 | adaptation rule (e.g. anti-Hebbian) | same `(γ̃,σ̃)`, same N, same budget |
| V1b | initial state (delocalized instead of localized `psi0`) | same rule, regime, N |
| V2 | `(γ̃,σ̃)` regime | same rule, pre-register the grid before running |
| V3 | `TopologyUpdateRule` active | same rule and regime |

**Addendum 2026-08-14 (later same day), `[A46]` — V1/V1b now satisfy
AOG-5 on independent grounds.** A measurement prompted by a parallel
session's catch that `D_W` is unsigned found that **no weight in any
cell ever rises above its initial value**: `Cσ`'s mean weight falls from
1.0 to 0.503 with a maximum of 0.807, i.e. its headline `D_W ≈ 0.51` is
a ~50% near-uniform *decay*. The implemented rule is net-decaying at
this budget, because a localized `psi0` leaves the correlation term
nearly inert while noise switches the decay term on globally.

This changes the standing of V1/V1b from *motivated relaxation* (banned
by AOG-5) to *independently motivated*: the reason to change the rule or
the initial state is now a measured mechanical property of the
apparatus, established without reference to whether the hypothesis is
true.

**Addendum 2 (same day), `[A47]` — the rationale above is CORRECTED.**
The net-decay in `[A46]` is not a budget property but a **theorem**:
`C_ij ≤ √(ρ_iρ_j) ≤ (ρ_i+ρ_j)/2` (Cauchy–Schwarz then AM–GM) forces
`Δ_ij ≤ η·dτ·(ρ_i+ρ_j)/2·(1−W_ij)`, so `W = 1` is an absorbing upper
barrier and, since all weights start at 1.0 (`[A19]`), no weight can
ever exceed it under any initial state, noise, or budget. **V1b
therefore cannot lift the ceiling, and "the rule is net-decaying" is the
wrong reason to run it.**

The correct rationale, which does survive: the rule's fixed point is
`W*_ij = C_ij/[(ρ_i+ρ_j)/2] ∈ [-1,1]`, the normalized endpoint
correlation — structured, but reachable only by differential *decay*. A
localized `psi0` leaves `ρ ≈ 0` across most of the graph, so both terms
vanish and `W*` is never approached except near the source; noise drives
`C_ij → 0` and hence `W* → 0`, pure decay. **The one untested regime is
delocalized initial state WITHOUT noise**, where `ρ > 0` everywhere and
`C` stays coherent, so `W*` carries real structure.

**Addendum 3 (same day), `[A48]` — V1b narrowed to a specific
delocalization, via the cheapest possible differentiating test.**
`W*` is computable from one closed trajectory with no adaptation loop —
computed it directly for three regimes across 3 graph seeds:

```
regime                     W* mean    W* std
localized (current)        +0.26       0.41
uniform delocalized        +0.95       0.07   <- WORSE: nearly no edge-to-edge spread
random-phase delocalized   +0.00       0.53   <- BEST: most spread, both signs
```

Uniform delocalization (all amplitudes equal magnitude AND phase) turns
out to be a *worse* V1b candidate than the status quo — its `W*` clusters
tightly near the ceiling, meaning almost no edge is differentiated from
any other. **V1b is narrowed to random-phase delocalized `psi0`**
(`γ=σ=0`), which showed the largest `W*` spread of any regime tested and
is therefore the one most likely to give the adaptation rule something
real to differentiate. Still one assumption changed from baseline.

**Hard rule (Minimal Relaxation):** one assumption per variant, new
experiment id, new pre-registration. Bundling two changes makes the
result uninterpretable against this baseline.

## Revival condition

A future attempt must state, before running, which single assumption in
the Relaxation Map it changes and why that change is motivated
independently of wanting to save the hypothesis (Anti-Overfitting Gate
AOG-5). Re-running the same rule at the same regime hoping for a
different outcome is explicitly not a revival condition.
