# Mathematical Contract — BILUH / boyko-benchmark

Frozen Phase-0 artifact. This is the single source of truth for every
formula the implementation must satisfy. Every default here traces back to
an entry in `assumptions.md` (cited inline as `[A#]`) — this document states
the *what*, `assumptions.md` carries the *why* and the *what-if-wrong*.

Do not modify a formula here to make a failing test pass. If a test
contradicts this contract, either the test is wrong or this contract is —
resolve that explicitly (new dated addendum) before touching either.

---

## 0. Scope Lock

This contract specifies **Stage 1 only**: a `GEOMETRIC_PHASE_CANDIDATE`
screen. It does not specify, and no implementation built from this contract
may claim to establish, anything belonging to a `PHYSICAL_SPACETIME_
CANDIDATE` screen (Lorentz recovery, relativistic dispersion, causal
covariance, gauge structure, gravity). See `falsification_gates.md` for the
full terminology lock.

---

## 1. Graph Primitives

### 1.1 Topology and weights (kept as two separate objects, per Correction 3)

- Node set `V = {1, ..., N}`.
- **Topology mask** `M ∈ {0,1}^{N×N}`: symmetric, `M_ii = 0`. Defines which
  node pairs *may* carry weight. Changed only by an explicit
  `TopologyUpdateRule`; the Stage-1 default rule is the identity for every
  arm except the one-shot rewiring in Arm D `[A8, A14]`.
- **Weight matrix** `W ∈ ℝ^{N×N}_{≥0}`: symmetric, `W_ii = 0`,
  `W_ij > 0 ⟹ M_ij = 1`, `M_ij = 0 ⟹ W_ij = 0` (enforced invariant, not
  just convention — see `test_missing_edges_do_not_appear_without_
  topology_rule` in §13 of ТЗ.txt) `[A5]`.
- **Weighted graph** `G = (V, M, W)`.

### 1.2 Degree and Laplacians

- Weighted degree: `d_i = Σ_j W_ij`. `D = diag(d_1, ..., d_N)`.
- **Combinatorial (unnormalized) Laplacian:** `L = D - W`.
  Property: `L · 1 = 0` (row sums are zero by construction). This is the
  Laplacian the Milestone-1 test `L·1=0` targets — **not** the normalized
  form below, whose zero eigenvector is `D^{1/2}·1`, not `1` itself. Keep
  the two straight in tests.
- **Normalized Laplacian:** `L_norm = I - D^{-1/2} W D^{-1/2}`
  (equivalently `D^{-1/2} L D^{-1/2}`). Spectrum bounded in `[0, 2)` for
  any connected weighted graph with non-negative weights; the zero
  eigenvalue has multiplicity equal to the number of connected components.
  **`L_norm` is the operator for the fast-dynamics Hamiltonian and for the
  eigenstructure-based geometric observables (G1, G2, G4)** `[A1]` — see §2, §5.
  **Revised 2026-08-11** (2nd DDD skeptic pass, finding #1's follow-on):
  this is no longer "every geometric quantity" — G3 (§5.4) and the
  Operator-Independence Diagnostic (§5.6) deliberately use the
  *combinatorial* `L`, not `L_norm`, precisely because they exist to probe
  whether `L_norm`'s dual role (driving dynamics AND measuring geometry)
  is contaminating the result. Do not re-simplify this back to "one
  operator for everything" — that was the actual defect being fixed.
  §6, §7.
- Both `L` and `L_norm` must satisfy: symmetric (`W = Wᵀ` ⟹ both are
  symmetric), and weights are non-negative by construction (§1.1).
- Reproducibility: identical `(N, generative model, master seed)` must
  produce a bit-identical `(M, W)` — enforced via `[A11]`'s seed scheme.

---

## 2. Fast Dynamics (closed system, baseline)

```
i dψ/dt = H(W) ψ,      H(W) := L_norm(W)
```

- `ψ ∈ ℂ^N`, `‖ψ‖₂ = 1`.
- **Invariant (mandatory, tested every step in dev mode, spot-checked in
  production mode):** `‖ψ(t)‖₂ = 1` for all `t`, within numerical
  tolerance documented in the test itself (no undocumented tolerance
  values — Perelman-audit no-collapse discipline).
- No damping, no stochastic term, no non-unitary operator anywhere in this
  mode. This is the *entire* content of "fast dynamics" for Stage 1.
- Initial condition `ψ(0)`: single localized excitation at a designated
  node `[A6]` — `ψ(0) = e_k`, `k` fixed per-arm-pair for shared
  initialization (§5 below).

### 2.1 Open-system dynamics — interface only, not implemented (Stage 1)

Per `[A2]`, the open-system SDE from ТЗ.txt Milestone 2,

```
dψ = [-i H(W) - γI] ψ dτ + B dW_t
```

is represented **only** as an unused `Protocol`/interface placeholder in
`dynamics/`. No noise operator `B`, no `γ`, no stochastic integrator is
specified or implemented in Stage 1. Do not wire this into any arm, test,
or observable.

### 2.2 Classical diffusion carrier — Arm CD only (added 2026-08-11)

**Why this exists:** `novelty_check.md` finding d2 claims novelty for the
*coupling* of Hebbian adaptation to unitary (quantum) fast dynamics — but
DDD skeptic review (finding #7, `.claude/memory/decisions.md`) identified
that Jarman et al. 2017 already does Hebbian-style adaptive rewiring driven
by the *same normalized-Laplacian heat kernel*, using *classical* diffusion
instead. Whether BILUH's Gate-A signature is specific to the quantum
carrier, or would appear under any Laplacian-driven adaptive rule
regardless of carrier, is not decidable from a literature scan — only from
running both carriers under otherwise-identical conditions. The user
requested this as a 7th arm (2026-08-11) rather than leaving it as an open
question; see `§4` for the arm definition.

**Corrected 2026-08-11, self-caught during drafting (before any skeptic
saw it — recorded per the project's own no-silent-error discipline, not
deleted):** the first draft of this section used `L_norm(W)` as the
classical generator, `dp/dt = -L_norm(W)p`, claiming it conserves `Σp_i(t)`.
That claim is **false** for any non-regular graph. Conservation requires
the generator's columns to sum to zero (`1ᵀA = 0` in `dp/dt = -Ap`); the
*combinatorial* Laplacian satisfies this by construction (`L·1=0`, and `L`
symmetric ⟹ `1ᵀL=0` too), but `L_norm`'s zero eigenvector is `D^{1/2}·1`,
**not** `1` — `1ᵀL_norm = 0` only holds for constant-degree (regular)
graphs, which Erdős–Rényi (`[A7]`) is not. Using `L_norm` here would have
silently leaked probability mass in a way that scales with degree
heterogeneity, undetected until a conservation test failed at
implementation time — worth catching on paper instead.

Classical fast dynamics therefore uses the **combinatorial** Laplacian:

```
dp/dt = -L(W) p,      p ∈ ℝ^N_{≥0}
```

- **Invariant:** `Σ_i p_i(t) = 1` for all `t` (probability conservation) —
  now correctly guaranteed: `d(1ᵀp)/dt = -1ᵀLp = -(L1)ᵀp = 0` for symmetric
  `L` with `L·1=0` (§1.2). This is a **weaker** invariant than the quantum
  carrier's `‖ψ(t)‖₂ = 1` — `p(t)` genuinely dissipates toward the
  stationary (uniform) distribution as `t → ∞` (heat death on the graph),
  whereas `ψ(t)` merely rotates in Hilbert space and never loses "spread."
  This qualitative difference is the entire point of the comparison, not a
  bug to reconcile away.
- **Consequence for the comparison design:** Arm CD no longer differs from
  Active in *only* the carrier — it also uses `L` where Active uses
  `L_norm` (§2, `[A1]`), because `L_norm` cannot support a
  probability-conserving diffusion on an irregular graph. A direct
  Active-vs-Arm-CD comparison therefore conflates two changed variables
  (carrier *and* operator), not one. **This is resolved, not just
  disclosed, by reusing the Operator-Independence Diagnostic (§5.6) as the
  bridge:** that diagnostic already runs a second quantum trajectory under
  `H := L` (same operator Arm CD uses, same quantum carrier Active uses).
  This gives a clean 2-factor decomposition instead of one confounded
  comparison:

  ```
  Active (quantum, L_norm)  vs  OI-rerun (quantum, L)   -> isolates the OPERATOR effect
  OI-rerun (quantum, L)     vs  Arm CD (classical, L)    -> isolates the CARRIER effect
  Active (quantum, L_norm)  vs  Arm CD (classical, L)    -> confounded; report but do not use alone for carrier-specificity claims
  ```

  Report all three, but `novelty_check.md` finding d2's carrier-specificity
  question is answered by the *second* row, not the third. **This clean
  isolation requires matched measurement operators, not just matched
  dynamics** — both legs of the comparison must measure G1/G2/G4 with the
  same operator that drove their own dynamics (the Operator-Matching Rule,
  §5, corrected 2026-08-11 after the 3rd skeptic pass caught an earlier
  draft that silently measured Arm CD with `L_norm` while its dynamics ran
  under `L`, which would have reintroduced exactly this confound).
- Initial condition `p(0)`: same source-node convention as `ψ(0)` — a
  real, non-negative point mass at the same set of averaged source nodes
  used for the quantum carrier (`[A17]`), for a paired comparison at each
  seed.
- No adaptation-rule change to `L` itself — Arm CD's "geometry" (G1, G2,
  G4, all defined purely in terms of the current `W(τ)`, §5) is computed
  identically to every other arm; G3 already uses `L` for every arm
  (§5.4), so no special-casing is needed there either. Only the *carrier*
  generating the correlation signal that drives weight adaptation (§3.2)
  and the propagation-front trajectory (§5.5) differs.

**Self-identified caveat (equilibration, distinct from the conservation
correction above):** `ker(L) = span{1}` for a connected graph, so
`p(t) → (1/N)·1` as `t → ∞` under `dp/dt = -Lp` — the classical carrier
genuinely dissipates to a *structureless uniform* stationary state
("heat death"), unlike the quantum carrier, which merely rotates in
Hilbert space and never settles. Consequently `⟨p_i · p_j⟩ → 1/N²` for
*every* pair as `t → ∞`, regardless of graph structure — the
`ClassicalHebbianAdaptation` correlation signal (§3.2) is most informative
early in the diffusion and becomes structurally uninformative once `p`
nears equilibrium. The relevant timescale is set by `L`'s own spectral gap
(the classical analogue of G2, evaluated on the *initial* `W(0)`, before
adaptation has changed anything). **This means `[A9]`'s `K`-window default
(`K=50`, chosen without reference to any equilibration timescale) cannot
be assumed to transfer from the quantum carrier to Arm CD without
checking** — if `K` fast-dynamics steps span a duration comparable to or
longer than `L`'s mixing time, Arm CD's adaptation would be shaped mostly
by near-uniform, uninformative correlations. **Sharper statement (added
2026-08-11, 3rd skeptic pass):** it is not merely that the signal becomes
noisy — the Oja fixed point itself degenerates to a specific, structurally
trivial value. Solving `⟨p_ip_j⟩ = W_ij·(p_i+p_j)/2` at equilibrium
(`p → (1/N)·1`) gives `W_ij* → 1/N` **uniformly on every edge in `M(0)`**,
independent of the original graph structure — post-equilibration Arm CD
doesn't converge to a noisy version of some geometric structure, it
converges to a flat, structureless weighting of the initial topology. This
is the concrete failure mode the `[A9]` sweep must be able to detect (a
run whose final `W` is near-constant across edges), not just generically
"low signal." Flagged for the `[A9]` robustness sweep (already required
before any Stage-1 verdict is trusted) to explicitly include an
Arm-CD-specific check: report the diffusion mixing time alongside the
sweep, and confirm `K` stays well inside it.

**Carrier-agnostic notation, used throughout §5:** let `ρ_i(t)` denote the
node-occupation quantity at time `t` — `ρ_i(t) := |ψ_i(t)|²` for the
quantum carrier (Active and every arm except CD, whether driven by `L_norm`
or, for the Operator-Independence rerun, by `L`), `ρ_i(t) := p_i(t)` for
the classical carrier (Arm CD only). `Σ_i ρ_i(t) = 1` in all cases, by
their respective invariants above — this is what licenses reusing one set
of observable definitions across every carrier/operator combination
instead of duplicating §5.

---

## 3. Adaptive Meta-Dynamics (weight evolution — not "learning")

**Terminology lock:** call this `adaptive Hebbian meta-dynamics`. Never
`learning` or `self-learning Universe` anywhere in code, comments, docs, or
output — no objective functional `L(W, ψ)` is defined or proven to be what
this rule descends, per Correction 2 and `[A3]`.

### 3.1 Interface

```python
class AdaptationRule(Protocol):
    def update(
        self,
        graph: WeightedGraph,
        trajectory: StateTrajectory,
        dtau: float,
    ) -> WeightedGraph:
        ...
```

`update` may only modify `W` where `M_ij = 1` (§1.1 invariant) — it never
touches `M`. Enforced as a hard invariant check, not a docstring promise.

### 3.2 Rules (Milestone 3 minimum set)

Let `⟨Re(ψ_i* ψ_j)⟩_K` denote the time-averaged real part of the pairwise
correlation over the most recent `K` fast-dynamics steps `[A9]`
(`K` a config parameter; development default `K = 50`, swept as a
robustness check before any Stage-1 verdict is trusted — this default is
not assumed correct, it is a starting point for a no-collapse test).

**Revised 2026-08-11 following DDD skeptic review (finding #3)** — see
`.claude/memory/decisions.md`. A pure `dW/dτ = +η·⟨corr⟩` rule with only a
non-negativity floor has no depression term: growth is bounded (correlation
is in `[-1,1]`) so it will not blow up numerically, but it has no mechanism
to prevent weight mass concentrating monotonically on whichever edges
started with slightly higher correlation — the "fixed point" such a rule
converges to is the trivial fixed point of unconstrained Hebbian growth,
not necessarily anything worth calling geometric. `HebbianAdaptation` is
therefore **Oja-normalized** — a symmetrized, graph-local form of the
standard single-neuron Oja rule (`dw/dt = η(xy − y²w)`), which couples the
decay term to the current weight itself, giving the ODE a genuine non-zero
fixed point instead of a monotonic drift:

```
HebbianAdaptation:         dW_ij/dτ = η · ( ⟨Re(ψ_i* ψ_j)⟩_K − W_ij·(|ψ_i|² + |ψ_j|²)/2 )   [A3, revised]
AntiHebbianAdaptation:     dW_ij/dτ = -η · ⟨Re(ψ_i* ψ_j)⟩_K                                   [A3]
NoAdaptation:              dW_ij/dτ = 0                            (= Frozen arm)
AlternativeObjective:      dW_ij/dτ = η · (|ψ_i|² + |ψ_j|²) / 2   [A4]
ClassicalHebbianAdaptation: dW_ij/dτ = η · ( ⟨p_i·p_j⟩_K − W_ij·(p_i + p_j)/2 )              [A18, Arm CD only]
```

`ClassicalHebbianAdaptation` (added 2026-08-11, Arm CD — §2.2, §4) is the
Oja-normalized rule's classical-carrier counterpart: identical structure,
`p` (real, non-negative, from §2.2's diffusion carrier) substituted for
`ψ`. **This substitution is not cosmetic — it changes what "correlation"
means.** `Re(ψ_i* ψ_j)` can be negative (destructive quantum interference
between i and j actively suppresses that edge's reinforcement); `p_i · p_j
≥ 0` always (classical co-occupation never actively suppresses an edge,
only fails to reinforce it as strongly). This asymmetry is *exactly* the
quantity `[A18]` exists to make visible, not an inconsistency to paper
over — if Active (quantum-driven) and Arm CD (classical-driven) produce
qualitatively different geometric signatures, the interference term is a
candidate explanation, testable in a follow-up variant per the Minimal
Relaxation Rule.

`AntiHebbianAdaptation` is deliberately **not** given the same Oja term —
its own degenerate fixed point (decay toward the non-negativity floor,
i.e. the weight mass draining toward zero) is a qualitatively different,
already-bounded pathology (bounded below by the floor itself), and
"fixing" it by adding growth-restoring normalization would blur the
sign-contrast AntiHebbian exists to provide. Instead, monitor it
explicitly: **flag any replicate where `mean(W) < 0.1 · mean(W(0))`** —
this is a data-quality/degenerate-run flag, reported alongside results,
not silently absorbed into the statistics.

- `W_ij` is projected to `≥ 0` after every update (Milestone-1 invariant);
  projection never changes `M` (§1.1).
- `η > 0` is a config parameter, held fixed across arms being compared in a
  single experiment (Active vs. AlternativeObjective must use the same
  adaptation *budget*, i.e. same `η` and same number of `dτ` steps, per
  ТЗ.txt Arm F description — this is what makes it a fair comparison, not
  just "a different rule ran for a different amount of time").

### 3.3 Topology dynamics — separate class, default identity

```python
class TopologyUpdateRule(Protocol):
    def update(self, graph: WeightedGraph, dtau: float) -> WeightedGraph:
        ...
```

`NoTopologyUpdate` (identity on `M`) is the Stage-1 default for every arm
except Arm D's one-shot rewiring `[A8, A14]`. No rule in Stage 1 may add an
edge (`M_ij: 0 → 1`) as a side effect of weight adaptation or noise —
tested explicitly (`test_missing_edges_do_not_appear_without_topology_
rule`).

**Addendum 2026-08-14 (`[A42]`, `[A50]`, `null_results/20260814-open-
system-geometrogenesis.md` V3) — one additional exploratory rule,
outside the Stage-1 arm table above:** `[A42]` found that
`HebbianAdaptation`'s non-negativity clamp can drive a weight to exactly
`0.0` under noise, which is already an EFFECTIVE topology change even
though `NoTopologyUpdate` leaves `M` formally untouched. `PruneZeroWeight
TopologyUpdate` (`dynamics/topology.py`) makes this explicit: after each
adaptation window, any edge with `W_ij == 0.0` is removed from `M`
(`M_ij: 1 → 0`). It is used **only** in the `null_results/2026...`
Relaxation Map's V3 pilot, never as a replacement for any Stage-1 arm's
`NoTopologyUpdate`, and it strictly obeys this section's no-edge-addition
invariant — it only ever removes, matching `[A42]`'s own finding that
edges are lost, never gained, by the existing clamp.

---

## 4. Required Experimental Arms

| Arm | Initial (graph, weights, state) | Fast dynamics | Weight adaptation | Topology |
|---|---|---|---|---|
| A — Active | shared with B, F `[§5]` | on | `HebbianAdaptation` (or configured rule) | `NoTopologyUpdate` |
| B — Frozen | shared with A, F | on | `NoAdaptation` | `NoTopologyUpdate` |
| C — Parameter-Matched Random | independent `[A7]`: Erdős–Rényi, mean degree matched to A's initial graph | on | `NoAdaptation` | `NoTopologyUpdate` |
| D — Topology Scrambled | derived from A's *final* graph `[A8]` | on (post-scramble) | `NoAdaptation` | one-shot degree-preserving rewire, then `NoTopologyUpdate` |
| E — Fixed Flat Geometry | periodic regular lattice (positive calibration; never an optimization target) | on | `NoAdaptation` | `NoTopologyUpdate` |
| F — Alternative Objective | shared with A, B | on | `AlternativeObjective`, same budget as A | `NoTopologyUpdate` |
| CD — Classical Diffusion Control | shared graph/weights with A, B, F `[M(0),W(0)]`; `p(0)` classical analogue of `ψ(0)` `[A17]` | **classical** (§2.2, `dp/dt=-L p`) | `ClassicalHebbianAdaptation`, same budget as A `[A18]` | `NoTopologyUpdate` |

**Shared-initialization rule (hard constraint, Correction-consistent):**
Active, Frozen, and Alternative Objective **must** receive bit-identical
initial `(M(0), W(0), ψ(0))` and the same random-seed stream up to the
point their dynamics diverge (Frozen never adapts; Active and Alternative
Objective apply different `AdaptationRule`s from step 1 onward). This is
what makes the three-way comparison meaningful — verified by
`test_frozen_arm_never_updates_weights` and an explicit
bit-identical-initialization test.

**Arm CD (added 2026-08-11, user-requested — see
`.claude/memory/decisions.md`)** extends this to a fourth shared-init
member: it receives the *same* `(M(0), W(0))` as A/B/F, and its own state
`p(0)` is the classical analogue of `ψ(0)` at the same averaged source
nodes (`[A17]`). Arm CD is **not** a Gate-A negative control (parallel to
F, not to B/C/D — see `falsification_gates.md`) — its purpose is to test
whether Active's geometric signature is specific to the unitary/quantum
carrier or arises under any Laplacian-driven adaptive rule (directly
testing `novelty_check.md` finding d2 after DDD skeptic review flagged
Jarman et al. 2017 as adjacent prior art for the classical-carrier case).

---

## 5. Observables

**Revised 2026-08-11** — not all geometric observables share one operator.
G1 (spectral dimension, §5.1), G2 (Laplacian gap, §5.2), and G4 (IPR,
§5.3) use `L_norm` (§1.2), matching the fast-dynamics Hamiltonian `[A1]`.
G3 (§5.4, effective resistance) and the mandatory Operator-Independence
Diagnostic (§5.6) deliberately use the *combinatorial* `L` instead —
reusing `L_norm` for those too would silently reintroduce the exact
self-reference risk §5.6 exists to catch. The fixed-topology hop-distance
metric `[A15]` is used only as the coordinate system for the
propagation-front radius (§5.5), well-defined because `M` is static within
a run, per `[A14]`.

**Operator-matching rule for L-driven trajectories (corrected 2026-08-11,
3rd skeptic pass — this paragraph previously claimed G1–G4 need "no
modification" for Arm CD, which was wrong and silently reintroduced the
exact measurement confound §5.6 exists to prevent):** G1, G2, and G4 are
defined purely in terms of the current `W(τ)` (no reference to `ψ` or `p`
themselves), **but their formulas do specify an operator** — `L_norm` by
default (§5.1–§5.3). That default applies to every `L_norm`-driven
trajectory (Active, Frozen, C, D, E, F). **Any trajectory whose *dynamics*
were driven by `L` instead — the Operator-Independence Diagnostic's rerun
(§5.6) and Arm CD (§2.2) — computes G1/G2/G4 using `L` on its own `W(τ)`
too, for internal consistency with its own generator**, exactly as §5.6
already specifies for its rerun. Without this rule, comparing an
`L`-driven trajectory's dynamics against an `L_norm`-measured geometry
would silently mix two different operators in one "result," breaking the
3-way factorial decomposition §2.2 relies on (`Active vs OI-rerun`
isolates the operator; `OI-rerun vs Arm CD` isolates the carrier — both
legs require matched measurement operators, not just matched dynamics).
G3 already uses `L` unconditionally for every arm (§5.4), so this rule
only changes G1/G2/G4. G5 (§5.5) uses the carrier-agnostic `ρ_i(t)`
notation to remain well-defined regardless of which operator or carrier
produced it.

### 5.1 Heat-kernel spectral dimension (Correction 4)

```
K(t)        = exp(-t L_norm)
P_return(t) = (1/N) Tr K(t)
d_s(t)      = -2 · d(ln P_return(t)) / d(ln t)
```

`I - L_norm` (equivalently `D^{-1/2} W D^{-1/2}`) must **never** be treated
as a standard random-walk transition matrix in this codebase — that
substitution is the specific mistake Correction 4 forbids.

For large `N`, `Tr K(t)` is estimated via a reproducible stochastic trace
estimator (Hutchinson-type; exact method and sample count deferred to
Phase 6, `[A13]`) rather than a dense `exp(-tL_norm)` computation.

**Calibration target (not a hard-coded definition):** a 3D periodic
lattice must show `d_s(t) ≈ 3` over an intermediate diffusion-time window,
within a documented finite-size tolerance (§13 of ТЗ.txt,
`test_cubic_lattice_has_ds_near_3`). A 1D ring targets `d_s ≈ 1`, a 2D
lattice `d_s ≈ 2` — same estimator, different calibration geometry.

### 5.2 Normalized Laplacian gap

```
λ_1 = first non-zero eigenvalue of L_norm
```

Scaling ansatz: `λ_1(N) ~ N^{-γ}`. `γ` is **estimated from data via
regression across the FSS grid (§7)**, never hard-coded — in particular,
`γ = 2/3` is explicitly not assumed (Correction/§6 of ТЗ.txt).

**Calibration target:** a random-regular expander-like graph must *not*
reproduce lattice-like gap closure (`test_expander_gap_does_not_close_
like_lattice`) — expanders have `λ_1` bounded away from 0 as `N → ∞`
(spectral graph theory, Chung 1997), i.e. `γ ≈ 0`, in contrast to a
`d`-dimensional lattice's `γ = 2/d` (standard result, also not hard-coded
into the estimator — only used as the calibration-test expectation).

### 5.3 Low-mode inverse participation ratio

```
IPR(φ_k) = Σ_i |φ_{k,i}|^4,     φ_k normalized: Σ_i |φ_{k,i}|² = 1
```

for `φ_k` a low-eigenvalue eigenvector of `L_norm` (the "geometric" / smooth
modes). Scaling ansatz `IPR(N) ~ N^{-η}`; extended modes calibration target
`η ≈ 1` (§7 of ТЗ.txt) — a calibration target for the estimator, not a
required definition of "geometric."

### 5.4 Diameter and average shortest-path length

**Revised 2026-08-11 following DDD skeptic review `[A16]`** — see
`.claude/memory/decisions.md`. The original hop-count-only definition is
kept for one purpose but is **not** the G3 gate observable, for a reason
worth stating precisely: under `[A14]` every arm except D shares a *fixed*
topology `M(0)`, so an unweighted hop-count diameter computed on `M(0)`
is **identical between Active and Frozen by construction** — not
approximately equal, exactly equal, since it never sees `W` at all. A gate
built on it would be unfalsifiable in the wrong direction (guaranteed
Cohen's d = 0 vs. Frozen regardless of what the adaptive dynamics does).

Two distinct distance notions are used, for two distinct purposes:

**(i) Unweighted hop-distance on `M(0)` `[A15]`** — used only as an
arm-agnostic *descriptive* statistic of the shared initial topology itself
(reported, not gated), and as the coordinate system for the
propagation-front radius `r_q(t)` in §5.5 (there it is fine precisely
*because* the front's time-evolution is driven by `ψ(t)`, which does
depend on `W` — only the ruler is topological, not the measured quantity).

**(ii) Effective-resistance distance** — the actual **G3 gate observable**,
because it is sensitive to `W` even when `M` is fixed:

```
R_eff(i,j) = L⁺_ii + L⁺_jj − 2 L⁺_ij
```

where `L⁺` is the Moore–Penrose pseudoinverse of the *combinatorial*
Laplacian `L = D − W` (§1.2) — standard graph-theoretic effective
resistance (electrical-network interpretation: treat each edge as a
conductance `W_ij`). Define:

```
resistance_diameter(G) = max_{i,j} R_eff(i,j)
mean_effective_resistance(G) = average over all pairs (i,j)
```

**Scaling ansatz for G3:** `resistance_diameter(N) ~ N^{δ}`, `δ` estimated
from the FSS grid, never hard-coded — same discipline as `γ`, `η`.

**Calibration target:** a random-regular graph shows small-world-like
resistance-diameter scaling (bounded/slow growth); a `d`-dimensional
lattice shows polynomial resistance-diameter growth consistent with its
known hop-diameter scaling `N^{1/d}` (the two notions agree in scaling
*exponent* on a lattice with near-uniform weights — they diverge precisely
when weights become non-uniform, which is exactly the adaptive-dynamics
case G3 needs to detect). Test name:
`test_random_regular_resistance_diameter_is_small_world_like`.

### 5.5 Operational finite-propagation front (Correction 5)

Explicitly **not** a Lieb–Robinson bound. Call it "operational
finite-propagation front" everywhere — in code, tests, plots, and any
report.

```
r_q(t) = min { r : Σ_{i : dist(source, i) ≤ r} ρ_i(t) ≥ q }
```

using the carrier-agnostic `ρ_i(t)` defined in §2.2 (`= |ψ_i(t)|²` for the
quantum carrier used by every arm except CD, `= p_i(t)` for Arm CD's
classical carrier — this is why §2.2 introduced `ρ` instead of letting
this section keep a `p_i(t) := |ψ_i(t)|²` definition of its own: that
symbol now means the classical carrier's own state in §2.2, and reusing it
here for a different quantity would collide). `dist` is the hop-distance
on `M(0)` `[A15]`; `source` is the node `k` from `ψ(0) = e_k` `[A6]` (or
`p(0) = e_k` for Arm CD); `q` a config parameter, default `q = 0.9`.

Fit, over the unsaturated (pre-plateau) regime only:

```
r_q(t) = v_eff · t + b
```

**Must record, every run:** `v_eff`, 95% confidence interval on `v_eff`,
fit `R²`, the fit time-window used, and the saturation radius (where
`r_q(t)` plateaus — typically near `diameter(M(0))`).

**Revised 2026-08-11 (skeptic finding #8) `[A17]`:** the source node `k` in
`ψ(0) = e_k` is not topologically canonical on a disordered generative
model — on Erdős–Rényi (`[A7]`), a single fixed node index has
seed-dependent local degree/clustering, which confounds "effect of the
dynamics" with "effect of which node happened to be node 0." `r_q(t)` is
therefore computed as an **average over 5 source nodes per (arm, N, seed)
replicate**, the 5 nodes drawn from the replicate's own seed stream
(`[A11]`, not chosen by degree — a degree-based rule would introduce a new
deterministic bias instead of removing a nuisance one). Report the
per-source spread alongside the mean, don't discard it.

### 5.6 Operator-Independence Diagnostic (required, mandatory report)

**Added 2026-08-11 following DDD skeptic review (finding #2), upgraded
2026-08-11 after a 2nd skeptic pass found the first version tested the
wrong thing** — see `.claude/memory/decisions.md` for both rounds.
`H(W) := L_norm(W)` (§2) is *the same operator* used to compute the
eigenstructure-based geometric observables (G1, G2, G4). This reuse is
efficient (§`[A1]`) but creates a structural risk worth naming precisely:
the Hebbian correlation rule (§3.2) reinforces weights on the support of
`L_norm`'s own low-lying eigenmodes (those dominate `⟨Re(ψᵢ*ψⱼ)⟩` for a
state that has spread under `L_norm`-driven unitary evolution), which then
further concentrates those same modes — a feedback loop internal to one
operator, baked into `W` by the dynamics itself, not just visible at
readout time.

**First version of this diagnostic (superseded — the mistake is documented,
not deleted, so it isn't silently rediscovered):** recompute G1/G2/G4 under
`L` instead of `L_norm` on the same, already-evolved `ψ(t)` and
already-adapted `W(τ)` — i.e. swap only the *measurement* operator, leave
the *dynamics* operator (which shaped `W` in the first place) untouched.
The 2nd skeptic pass showed this doesn't test the actual concern: because
`L = D^{1/2} L_norm D^{1/2}` on the same `W`, whatever low-mode support
`L_norm`-driven evolution installed into `W` mostly survives a
readout-only operator swap — the diagnostic would stay quiet almost
always, giving false reassurance precisely in the case it exists to catch.

**Corrected diagnostic — a full parallel dynamics rerun, not a readout
swap.** For each `(N, seed)` in Active's run, execute a second, independent
trajectory from the same `(M(0), W(0), ψ(0))` and seed stream, using
`H := L` (combinatorial, §1.2) as the fast-dynamics generator in place of
`L_norm` — i.e. `i dψ'/dt = L ψ'` drives both the propagation and the
Hebbian weight-shaping (§3.2, `⟨Re(ψ'ᵢ*ψ'ⱼ)⟩_K` computed on `ψ'`, not `ψ`)
for the full adaptation budget, producing an independently-shaped `W'(τ)`.
Then compute G1/G2/G4 (using `L` for internal consistency with this run's
own generator, per the Operator-Matching Rule, §5) on `W'(τ)` and compare
its FSS behavior to Active's.

**Timescale caveat (added 2026-08-11, 3rd skeptic pass — mirrors §2.2's
equilibration caveat for the classical carrier):** `spec(L)` is unbounded
(scales with the largest weighted degree) while `spec(L_norm) ⊂ [0,2)` —
using the *same* `dt` and `K` (`[A9]`) for both the `L_norm`-driven Active
run and the `L`-driven OI-rerun means the `K`-step averaging window covers
a different amount of phase rotation in each. Before trusting an "operator
effect" conclusion from `Active vs OI-rerun`, confirm `K` corresponds to a
comparable fraction of each operator's own characteristic timescale (e.g.
`1/λ_max` of the respective operator) — or explicitly rescale `dt` for the
OI-rerun (`dt' = dt · spec(L_norm)/spec(L)`, order-of-magnitude) so the two
runs are compared on like terms. Left as a required check alongside the
`[A9]` sweep, not resolved analytically here — no production data exists
yet to calibrate it against.

```
L_norm-driven run AND L-driven run agree qualitatively (same FSS signature)
    -> geometric signal survives an operator swap in the dynamics itself, not just at readout
L_norm-driven run shows the signature, L-driven run does not
    -> flag [SUSPECT-OPERATOR-ARTIFACT] -- the shaping, not just the measurement, is operator-dependent
```

This is real additional compute (doubles the cost of every Active
`(N, seed)` cell, since it's a second full trajectory, not a cheap
re-diagonalization) — it is **not** a 7th competing scientific hypothesis
about geometry emergence (unlike Arm CD, §2.2/§4), it is a validity check
on whether Active's own result depends on an implementation choice. Keep
it out of the experimental arms in §4; it lives here, as apparatus-trust
infrastructure, alongside the Oracle Adequacy checks in
`falsification_gates.md`.

**Interpretation rule, mandatory in `phase_verdict.json`:** same two-line
rule as before, now correctly attached to the dynamics-level rerun. A
`[SUSPECT-OPERATOR-ARTIFACT]` flag does not itself override a G1–G6
verdict, but it is a **mandatory caveat** attached to any `SURVIVES`
verdict, carried into every downstream report, and is disqualifying for
any Submission-Gate-level external claim until resolved.

---

## 6. Finite-Size Scaling (§9 of ТЗ.txt)

- Development grid: `N ∈ {64, 125, 216, 343, 512}` (`N = L³`, cubic-lattice
  friendly, `L ∈ {4,5,6,7,8}`).
- Production minimum: `≥ 5` distinct `N`, `≥ 20` independent seeds per
  `(arm, N)` pair; `30–50` seeds where budget allows.
- A geometric-phase claim (Gate A, `falsification_gates.md`) is **never**
  inferred from a single `N`. Every reported scaling exponent (`γ, η, δ`)
  is a regression fit across the full FSS grid, with its own confidence
  interval.

---

## 7. Statistics (§11 of ТЗ.txt)

For every metric, every `(arm, N)` cell:

```
mean, standard deviation, median, 95% CI, effect size (Cohen's d vs. each
negative-control arm), seed count, raw per-seed samples (persisted, not
just aggregates)
```

**Independence rule (hard constraint):** comparisons are across
independent runs (different seeds), never across time points within one
run. A single run's `d_s(t)` trajectory at ten different `t` is not ten
independent observations of anything.

MCID / significance gate: `|Cohen's d| ≥ 0.8` **and** non-overlapping 95%
CIs, both required, between Active and each negative-control arm, on each
Gate-A observable `[A10]` — fixed here, before any production run, per
EstimandOps discipline (a threshold chosen after seeing borderline results
is invalid).

---

## 8. Cross-References

- Assumption provenance for every `[A#]` tag above: `assumptions.md`.
- Pass/fail machinery built on these definitions: `falsification_gates.md`.
- Population/intervention/comparator/endpoint/MCID as a formal estimand:
  `estimand.md`.
