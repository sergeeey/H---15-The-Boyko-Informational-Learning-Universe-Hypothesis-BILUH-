# Assumptions Register — BILUH / boyko-benchmark

Phase 0 artifact. Every unresolved scientific or engineering ambiguity in the
source planning document (`../../ТЗ.txt`) that this project must resolve
*before* code is written gets one entry here — never a silent choice buried
in implementation. Per project completion rule: "If an unresolved scientific
ambiguity prevents implementation, stop and record it here instead of
silently choosing an interpretation." Recording a default is allowed;
silence is not.

## Gate 1 — Artifact Identity (run 2026-08-11)

`ТЗ.txt` (the only file in the project folder) instructs, twice, to read
`boyko-minimal-experiment-v1.0.md` before making implementation decisions —
it frames itself as a set of six corrections *to* that document (Corrections
1–6 in ТЗ.txt §16), not as a self-contained spec.

**[VERIFIED]** `boyko-minimal-experiment-v1.0.md` does not exist anywhere
under `E:\Проверка Гипотез` (recursive `find` by name, 2026-08-11, 0 matches).
The user confirmed the file is not available: *"файла v1.0 у меня нет —
работаем от ТЗ"* (2026-08-11).

**Consequence:** this project is built from `ТЗ.txt` alone. `ТЗ.txt`
reproduces enough of v1.0's content in its "Correction N" sections to infer
what it disagreed with, but the underlying document's original formulation,
any passages it did *not* quote, and its own stated assumptions are
unrecoverable. Per the artifact-provenance-gates rule, no verdict or
parameter choice here transfers an implicit authority from "the Boyko
hypothesis" as a whole — this register only binds `boyko-benchmark` as
implemented from `ТЗ.txt`. If `v1.0` surfaces later, every entry below must
be diffed against it before being trusted as unchanged (see Resolution
Protocol at the end).

---

## Assumption Registry

Each entry: what's ambiguous in ТЗ.txt → the default chosen for
implementation → why → what breaks if the default is wrong.

### A1 — Functional form of H(W)

**Ambiguity:** ТЗ.txt Correction 1 rejects the "ambiguous product `W_ij
H_ij`" and demands "a clean Hamiltonian operator `H = H(W)`," but never
gives the functional form. Milestone 2 only states the invariant
(`‖ψ(t)‖₂ = 1`) the dynamics must satisfy.

**Default:** `H(W) := L_norm(W)`, specifically the *normalized* Laplacian
`I - D^{-1/2} W D^{-1/2}` — the same operator §6 of ТЗ.txt already commits
to for the Laplacian-gap measurement, and the operator this contract uses
for every geometric observable (A1b below). Using the normalized form
(not the combinatorial `L = D - W`) is a refinement made explicit in
`mathematical_contract.md` §2, for two reasons: (a) its spectrum is bounded
in `[0, 2)` regardless of weight/degree magnitude, so fast-dynamics
timestep stability does not degrade as adaptive weights (A3) drift the
degree sequence; (b) reusing one operator for both the walk generator and
every geometric observable removes an entire class of "which Laplacian did
you mean here" bugs. This is the CTQW convention of using a graph Laplacian
as the walk generator (Farhi & Gutmann 1998; surveyed in Childs 2009),
specialized to the normalized variant. `L_norm` is real symmetric ⇒
Hermitian ⇒ `i dψ/dt = L_norm ψ` is unitary by construction, satisfying the
Milestone-2 invariant for free.

**Evidence:** [INFERRED] from CTQW literature convention + internal
consistency with §5 of ТЗ.txt (spectral-dimension estimator already commits
to `L`). Not confirmed against v1.0 (unavailable, Gate 1).

**If wrong:** every fast-dynamics test and every observable computed from
`ψ(t)` needs re-deriving under the correct `H(W)`. Isolate this choice
behind a single factory function (`hamiltonian.py: build_hamiltonian(W)`) so
a future correction is a one-file change, not a rewrite.

### A2 — Open-system dynamics: in or out of scope for this benchmark

**Ambiguity:** Milestone 2 gives a full SDE for an open-system mode
(`dψ = [-iH(W) - γI]ψ dτ + B dW_t`) and says it "must be a separate optional
model" — but the file tree (§2), the six Phases (§16), and the required
observables (§CLAUDE.md draft) never mention it again. No noise operator
`B`, no `γ` value, no phase/module is specified for it anywhere.

**Default:** open-system dynamics is **out of scope for Stage-1**. Define
the `Protocol`/interface only (so a later benchmark version can add it
without breaking `dynamics/fast.py`'s contract), but do not implement
stochastic integration, do not test it, do not report it as an observable
source. `dynamics/fast.py` implements only the closed-system unitary case.

**Evidence:** [INFERRED] from absence across every operational section of
ТЗ.txt (file tree, phases, quality-gate module list) despite presence in the
Milestone-2 prose.

**If wrong:** low cost — an unused interface stub is cheap to fill in later;
the risk this default avoids (silently blending damping/noise into what's
supposed to be a clean unitary baseline) is the more expensive failure mode.

### A3 — The adaptation rule has no defined objective functional

**Ambiguity:** ТЗ.txt is explicit and repeated: do not call the slow update
"learning" until `L(W,ψ)` is defined *and* `F_ij ≈ -∂L/∂W_ij` is
demonstrated. Yet Milestone 3 requires implementing `HebbianAdaptation`,
`AntiHebbianAdaptation`, `NoAdaptation` with no `L` ever written down. This
is the single largest scientific gap in the source document.

**Default:** implement the standard continuous Hebbian correlation rule as
a **heuristic update**, explicitly not claimed to be gradient descent on
anything:

```
dW_ij/dτ = η · Re(ψ_i* ψ_j)      (HebbianAdaptation)
dW_ij/dτ = -η · Re(ψ_i* ψ_j)     (AntiHebbianAdaptation)
```

with a hard floor/ceiling on `W_ij` to keep weights non-negative (Milestone
1 invariant) and a projection step that never touches entries where
`W_ij = 0` in the topology mask (A5 below) — weight dynamics must not
manufacture edges.

**Evidence:** [WEAK] — this is the textbook "fire together, wire together"
correlation rule (a single well-known convention, not cross-checked against
a second independent source here), chosen because it is the minimal rule
consistent with ТЗ's own naming ("Hebbian"), not because `F_ij ≈ -∂L/∂W_ij`
has been shown. **`docs/mathematical_contract.md` must carry this caveat
verbatim**: the rule is `adaptive Hebbian meta-dynamics`, not `learning`,
until a potential function is found for which this rule is the gradient —
and no such function is asserted to exist.

**If wrong:** this is the actual scientific core of the project; if this
default rule is not what makes the hypothesis interesting, every result is
a test of the wrong dynamics. Flag prominently in `falsification_gates.md`
that a NULL result under this specific rule falsifies *this rule*, not
"adaptive dynamics" in general — see Minimal Relaxation Rule (only this one
assumption may be swapped in a follow-up variant, not bundled with others).

### A4 — Alternative Objective arm: concrete rule required

**Ambiguity:** Arm F must use "a different adaptation objective" to test
whether results are specific to the chosen rule — but "different" from A3's
Hebbian rule is not itself a rule.

**Default:** anti-correlation-magnitude rule decoupled from sign structure:
`dW_ij/dτ = η · (|ψ_i|² + |ψ_j|²) / 2` (local-density-driven reinforcement,
ignores phase correlation entirely — orthogonal mechanism to A3, not simply
its negation, since AntiHebbian already covers the sign-flip case).

**Evidence:** [WEAK] — chosen for orthogonality to A3, not derived from any
source. Open to revision without touching A3.

### A5 — Weight vs. topology separation: what carries the sparsity mask

**Ambiguity:** ТЗ.txt insists "absent edges must not appear from Gaussian
noise" and that edges change only via an explicit `TopologyUpdateRule`, but
never states the data structure that enforces this.

**Default:** `WeightedGraph` carries two separate arrays: a boolean sparsity
mask `M` (topology) and a weight array `W` defined only where `M` is true.
`AdaptationRule.update` may only write into cells where `M[i,j] = True`;
this is enforced as an invariant check (`test_missing_edges_do_not_appear_
without_topology_rule`, already named in ТЗ.txt §13), not just a convention.

**Evidence:** [CODE-design], follows directly from ТЗ.txt's own stated
critical requirement — low ambiguity, included here mainly to pin the
enforcement mechanism (test, not docstring).

### A6 — Initial state ψ(0)

**Ambiguity:** never specified anywhere in ТЗ.txt.

**Default:** a single localized excitation, `ψ(0) = e_k` for a designated
node `k` (typically a lattice-center node for Fixed Flat Geometry, node 0
otherwise), matching the standard CTQW/propagation-front convention — the
propagation-front estimator (§8) is only meaningful for a localized initial
condition; a delocalized start would make `r_q(t)` measure something else
from `t=0`.

**Evidence:** [INFERRED] from internal consistency with the propagation
front definition in ТЗ.txt §8, which presumes a expanding front from a
point source.

### A7 — Initial topology generative model for Active/Frozen/AltObjective

**Ambiguity:** "same initial graph" is required across arms, but the
generative model for that shared initial graph is never named. Since Fixed
Flat Geometry (Arm E) is a periodic lattice used as *positive calibration*
— implying it already has the geometry the others are being tested for —
Active's initial graph must plausibly start disordered, or the experiment
has no dynamic range to detect.

**Default:** random geometric graph (RGG) in a bounded region, or
Erdős–Rényi `G(N, p)` matched in mean degree to the lattice-comparison arm
— **not yet chosen between these two**; both satisfy "disordered start,"
differ in whether there's an underlying embedding to leak into the
adaptation rule as a hidden target (RGG has an embedding, ER does not).

**Resolution before Phase 1:** default to **Erdős–Rényi**, specifically
*because* it has no spatial embedding at all to accidentally leak into
`AdaptationRule` as an implicit target geometry — this is the stronger
negative-control property and directly serves the anti-cheating rule
("never insert target dimension… into the adaptive objective"). RGG is
rejected for this reason, not revisited unless ER is shown insufficient.

**Evidence:** [INFERRED] — resolved by the project's own anti-cheating
constraint, which is unambiguous even though the generative-model choice
itself was not specified.

### A8 — Topology Scrambled arm: when is scrambling applied

**Ambiguity:** "derived from Active topology, degree sequence preserved,
randomly rewired" — derived at what point in time? A once-off transform of
the *final* Active graph, or a parallel run re-scrambling at every adaptive
step using Active's realized degree-sequence trajectory?

**Default:** scrambling is applied **once**, to Active's final topology
(after the full adaptive run completes), producing a static graph. Fast
dynamics and observables for Arm D are then measured on that single
scrambled graph — this is a negative control for "does the *specific
wiring* Active converged to matter, beyond its degree sequence," not a
second independent dynamical trajectory.

**Evidence:** [WEAK] — the "once-off transform" reading is simpler and
cheaper, and is the more common meaning of "scrambled control" in network
science, but the "parallel re-scrambled trajectory" reading is not ruled
out by the text. Flagged for skeptic review (Stage A, Task 8) before
committing to Phase 5.

### A9 — Fast/slow timescale separation ratio

**Ambiguity:** no numeric relationship between `dt` (fast dynamics) and
`dτ` (adaptive dynamics) is given — full adiabatic separation is implied by
using two different time symbols, but not quantified.

**Default:** adaptive update uses a time-averaged correlation
`⟨Re(ψ_i* ψ_j)⟩` over a fast-dynamics window of `K` steps (`K` a config
parameter, development default `K=50`) before applying one `dτ` update —
avoids reacting to instantaneous phase noise, consistent with treating
`dτ` as genuinely slow relative to `dt`.

**Evidence:** [WEAK] — `K=50` is an arbitrary starting point, not derived;
must be swept as a robustness/no-collapse check (Perelman-audit style)
before any Stage-1 verdict is trusted, not fixed once and forgotten.

### A10 — MCID / significance threshold for "meaningful separation" (G6)

**Ambiguity:** ТЗ.txt §10 Gate A requires "statistically meaningful
separation from negative controls" and §11 requires effect sizes to be
recorded — but no numeric threshold is given anywhere for what counts as
"meaningful." Per EstimandOps, an MCID must be fixed *before* data
collection, not chosen after seeing results.

**Default:** effect size threshold `|Cohen's d| ≥ 0.8` (conventional
"large effect" boundary) between Active and each of Frozen / Random /
Scrambled, on each Gate-A observable (G1–G5 metrics), with non-overlapping
95% CIs required in addition to the effect-size threshold — both conditions
must hold, not either alone.

**Evidence:** [WEAK] — Cohen's `d=0.8` is a generic convention, not derived
from this system's noise characteristics; must be written into
`estimand.md` and frozen before any production run, per the Anti-Overfitting
Gate (a threshold chosen after seeing borderline results is invalid).

### A11 — Seed derivation scheme

**Ambiguity:** `seed_manager.py` and `seeds.csv` are named but the
derivation method (single master seed → per-arm/per-replicate child seeds)
is unspecified.

**Default:** NumPy `SeedSequence.spawn()` (PCG64 bit generator) — a
standard, auditable, collision-resistant splittable-seed scheme; master
seed logged in `config.json`, every spawned child seed logged in
`seeds.csv` alongside the arm/replicate/size it was used for.

**Evidence:** [DOCS] — `numpy.random.SeedSequence.spawn` is documented
NumPy API behavior for exactly this purpose.

---

### A14 — Default topology update rule is the identity (no spontaneous change)

**Ambiguity:** Milestone 3's critical requirement ("absent edges must not
appear from Gaussian noise") plus "if topology should change, this is done
only by an explicit `TopologyUpdateRule`" implies topology CAN be static by
default, but no arm description says which arms actually invoke a
non-identity `TopologyUpdateRule` during their run.

**Default:** every arm except Topology Scrambled (Arm D) uses
`TopologyUpdateRule = NoTopologyUpdate` (identity) for the full Stage-1
benchmark — the sparsity mask `M` is fixed at `M(0)` for the entire run in
Active, Frozen, Parameter-Matched Random, Fixed Flat Geometry, and
Alternative Objective. Only *weights* evolve (A3); topology never does,
except the one-shot rewiring that defines Arm D itself (A8). This is the
simplest reading consistent with the critical requirement, and it resolves
A8 and A15 simultaneously: if `M` never changes mid-run, graph distance is
well-defined for the whole trajectory without tracking a time-varying
topology.

**Evidence:** [INFERRED] from the absence of any arm description invoking
dynamic topology change during a run, plus consistency with A8's "scramble
once" resolution.

**If wrong:** if a later phase decides Active *should* dynamically rewire
during the run (a genuine `TopologyUpdateRule` beyond identity), A15's
graph-distance metric and the propagation-front definition in
`mathematical_contract.md` §6 need to be re-derived against a time-varying
`M(t)` — flag this as the highest-leverage single assumption to revisit if
Stage-1 results are ambiguous, since it changes what "geometry" even means
mid-run.

### A15 — Graph-distance metric for diameter / propagation front

**Ambiguity:** "graph radius," "graph diameter," and "average shortest-path
length" are not pinned to a specific distance — hop count on the topology
mask `M`, or weighted shortest path using `1/W_ij` as edge length.

**Default:** unweighted hop count on the fixed mask `M(0)` (justified by
A14: `M` does not change mid-run for any arm except the one-shot Arm D
rewiring). This keeps "geometry" (graph-distance structure) cleanly
separated from "dynamics" (how weights evolve within that fixed structure)
— the propagation front then measures how fast probability mass moves
through a *fixed* graph under *adaptively-weighted* dynamics, which is
exactly the quantity Correction 5 / §8 wants to characterize.

**Evidence:** [INFERRED] from A14 plus the general project principle
(ТЗ.txt Correction 3) of keeping weight dynamics and topology strictly
separate — extending that separation to the distance metric used by
observables is the consistent choice, not an independent one.

### A16 — G3 distance metric revised to effective resistance (skeptic finding #1)

**Ambiguity/defect found:** A15 (hop-count on `M(0)`) combined with A14
(fixed topology for every arm but D) makes the diameter/avg-shortest-path
observable **identical between Active and Frozen by construction** — it
never depends on `W` at all. G6's MCID comparison on this observable
would have Cohen's d = 0 guaranteed, making the Gate-A `SURVIVES` verdict
unachievable by construction, discovered by DDD skeptic review
2026-08-11 (`.claude/memory/decisions.md`, finding #1).

**Default:** the G3 gate observable is redefined to **effective-resistance
distance** (`R_eff(i,j) = L⁺_ii + L⁺_jj − 2L⁺_ij`, pseudoinverse of the
combinatorial Laplacian) — genuinely sensitive to `W` even when `M` is
fixed, because it is an electrical-network distance where `W_ij` are
conductances. Hop-count on `M(0)` (A15) is kept, but scoped down to (i) a
descriptive statistic of the shared initial topology and (ii) the
coordinate system for the propagation front (§5.5), where it is not the
measured quantity itself. See `mathematical_contract.md` §5.4.

**Evidence:** [INFERRED] — standard graph-theoretic effective resistance
(Chung 1997 lineage; electrical-network graph theory), chosen specifically
because it is provably weight-sensitive under a fixed topology, which is
exactly the property the original hop-count choice lacked.

**If wrong:** if effective resistance turns out to correlate too tightly
with the spectral-gap observable (G2) — both derive from the Laplacian
spectrum — G3 could become a redundant restatement of G2 rather than an
independent criterion. Worth an explicit correlation check between G2 and
G3 outputs once Phase 6 produces real data, before trusting them as six
independent criteria.

### A17 — Propagation-front source node averaged, not fixed (skeptic finding #8)

**Ambiguity/defect found:** A6 fixed `ψ(0) = e_k` at a single node index
(typically `k=0`). On Erdős–Rényi (A7), a fixed node index has
seed-dependent local degree and clustering — the propagation-front radius
`r_q(t)` (§5.5) then confounds "effect of the adaptive dynamics" with
"effect of which node happened to be node 0 in this particular draw."
Found by DDD skeptic review 2026-08-11, finding #8.

**Default:** `r_q(t)` is computed as an average over **5 source nodes per
`(arm, N, seed)` replicate**, drawn from the replicate's own seed stream
(`[A11]`) — not chosen by degree or any other topological rule, since a
degree-based selection rule would trade one deterministic bias
(seed-dependent node-0 structure) for a different deterministic bias
(always the best-connected node, which may itself interact differently
with each arm's degree distribution). Report the per-source spread
alongside the mean.

**Evidence:** [WEAK] — 5 is an arbitrary starting count, not derived; if
per-source variance turns out to dominate the propagation-front CI, this
count should be swept upward as its own robustness check, similar in
spirit to A9's `(K, η)` sweep requirement.

**If wrong:** G5 (propagation front) CIs will be inflated by source-node
nuisance variance rather than reflecting genuine seed-to-seed variability
in the dynamics — a symptom to watch for in the first production run,
not something resolvable analytically in advance.

### A18 — Arm CD: classical diffusion carrier and correlation signal (user-requested 2026-08-11)

**Context, not an ambiguity in ТЗ.txt itself:** ТЗ.txt specifies six arms;
this is a user-requested seventh, added to directly test `novelty_check.md`
finding d2 after DDD skeptic review (finding #7) identified Jarman et al.
2017 as adjacent prior art for Laplacian-driven adaptive rewiring under a
*classical* carrier. Two design choices had no ТЗ.txt precedent to draw on:

**Choice 1 — carrier equation.** **Self-corrected during drafting, before
any skeptic review** (recorded, not silently fixed): the first draft used
`dp/dt = -L_norm(W) p`, claiming `Σp_i(t)=1` conservation. That claim is
false for any non-regular graph — conservation needs the generator's
columns to sum to zero, which the combinatorial `L` satisfies by
construction (`L·1=0`, symmetric) but `L_norm` does not (`L_norm`'s zero
eigenvector is `D^{1/2}·1`, not `1`). Default is now: `dp/dt = -L(W) p`
(combinatorial Laplacian, §1.2), the standard graph heat equation, correct
by construction for any weighted graph. Evidence: [VERIFIED] — the
conservation proof is a two-line algebraic identity, not an inference.

**Consequence:** this means Arm CD no longer differs from Active in
*only* the carrier (it also uses `L` where Active uses `L_norm`) — a
direct Active-vs-Arm-CD comparison confounds carrier and operator. This is
resolved via the Operator-Independence Diagnostic (§5.6 of the contract),
which already runs a second quantum trajectory under `L` — that rerun,
not Active directly, is the correct carrier-isolating baseline for Arm CD
(same operator `L`, only the carrier — quantum vs. classical — differs).
See `mathematical_contract.md` §2.2 for the full 3-comparison breakdown.

**Choice 2 — correlation signal for `ClassicalHebbianAdaptation`.**
Default: `⟨p_i · p_j⟩_K` (raw co-occupation product) in place of
`⟨Re(ψ_i* ψ_j)⟩_K`. Evidence: [WEAK] — the simplest real-valued analogue,
chosen deliberately to preserve the sign asymmetry (classical co-occupation
is never negative, unlike quantum correlation) rather than to construct an
artificially signed classical analogue that would hide the very difference
Arm CD exists to expose. `mathematical_contract.md` §3.2 documents this
asymmetry as a feature of the comparison, not a modeling gap to close.

**If wrong:** if Active vs. Arm CD differ mainly because of *this specific*
correlation-signal choice rather than because of the quantum/classical
carrier distinction per se, that confound would need a second classical
correlation-signal variant (e.g. a centered/signed version) to disentangle
— per the Minimal Relaxation Rule, a new experiment ID, not a retrofit of
this one.

### A19 — Initial edge weight value (found during Phase 1 implementation)

**Ambiguity:** the contract fixes topology generation (`[A7]`: Erdős–Rényi)
but never states what numeric weight a newly generated edge starts with —
`W(0)` needs *some* value to bootstrap fast dynamics and propagation, and
"weights ≥ 0" alone doesn't pin one.

**Default:** uniform initial weight `1.0` on every generated edge. Simplest
possible choice, keeps `W(0)` structurally uninformative (no edge starts
"stronger" than another — any structure Active later develops comes from
the adaptation rule acting on `ψ`/`p` dynamics, not from a biased initial
condition).

**Evidence:** [WEAK] — arbitrary but deliberately neutral; not derived
from any source.

**If wrong:** if `η` (adaptation rate, `[A3]`) turns out to interact with
the absolute scale of `W(0)` in a way that matters (e.g. Oja fixed points
scale with initial weight magnitude), this default and `η`'s default both
need revisiting together — flag for the `[A9]` sweep.

### A20 — K-window averaging convention (found during Phase 3 implementation)

**Ambiguity:** `⟨Re(ψ_i* ψ_j)⟩_K` (§3.2) names a time-average over "the
most recent K fast-dynamics steps" but never states whether the `t=0`
snapshot is included in that average, and never states whether the Oja
decay term's `|ψ_i|²`/`|ψ_j|²` uses the same K-window average or the
single final-snapshot density.

**Default:** average over all `K+1` recorded snapshots (`t = 0, dt, ...,
K·dt`), including `t=0` — simplest defensible choice, no principled
reason to privilege excluding the initial point. The Oja decay term uses
`⟨|ψ_i|²⟩_K` (the **same** K-window average), not the final-snapshot
density alone — for internal consistency with the growth term's own
averaging, and because it falls out for free: `⟨Re(ψ_i* ψ_i)⟩_K =
⟨|ψ_i|²⟩_K` exactly, so the diagonal of the already-computed correlation
matrix *is* the time-averaged density, no separate computation needed.

**Evidence:** [WEAK] — reasonable defaults, not derived from the contract
text, which is silent on both points.

**If wrong:** if `K` is swept per `[A9]`'s required robustness check and
results are sensitive to whether `t=0` is included, that sensitivity
itself is diagnostic (it would mean the average is dominated by one
snapshot, i.e. `K` is too small relative to the dynamics' own timescale)
— report it rather than silently changing this convention post hoc.

### A21 — Arm D rewired-edge weights and swap count (found during Phase 4 implementation)

**Ambiguity:** "one-shot degree-preserving rewire" (§4, `[A8]`) fixes the
*topology* Arm D inherits from Active's final graph, but not (a) what
weight value the *rewired* edges get — Active's final weights are tied to
specific `(i,j)` pairs that may not exist after rewiring, so there's no
natural "carry-over" — nor (b) how many double-edge-swap operations
constitute adequate randomization.

**Default (a):** rewired edges get the uniform `INITIAL_EDGE_WEIGHT`
(`[A19]`), same convention as any other arm's starting weights — keeps
topology and weight-value questions cleanly separated, consistent with
the contract's own "topology and weights are separate objects" design.

**Default (b):** `n_swaps` is a **required** parameter, no built-in
default. A fixed constant would not scale correctly across the FSS grid
(`N` from 8 to 512 in the configs) — larger graphs need proportionally
more swaps for the same degree of randomization. The caller (experiment
runner, Phase 8+) must choose and record this per config, not inherit an
unexamined default from this module.

**Evidence:** [WEAK] for (a) (arbitrary but consistent); (b) is a
structural guard against silently under-randomizing, not itself a derived
number.

**If wrong:** (a) — if weight-value inheritance turns out to matter for
Gate-A interpretation, this needs revisiting alongside A8's own scope. (b)
— an inadequate `n_swaps` choice would leave Arm D suspiciously similar
to Active's topology, weakening it as a negative control; this should be
checked empirically (e.g. clustering-coefficient convergence) before
production runs, not assumed correct from a formula.

**Implementation note (Phase 8 Cycle 19):** `config.py`'s Phase-1 schema
never actually gained a field for this — a real gap, not a design
decision, only surfaced when the orchestrator needed a concrete value.
Fixed via `TopologyScrambledSection.n_swaps_per_edge` — a per-edge
**multiplier**, not the raw `n_swaps` count itself, so it scales
automatically across the FSS grid exactly as (b) above requires (actual
`n_swaps = n_swaps_per_edge * n_edges(N)`, computed per-size). Because the
multiplier is scale-invariant by construction, it — unlike the raw count
— can safely carry a default (10, standard configuration-model
randomization heuristic) without reintroducing (b)'s original concern;
every real config (`configs/*.yaml`) still sets it explicitly.

### A23 — G3 power-law-vs-logarithmic model comparison threshold (found during Phase 7 implementation)

**Ambiguity:** `falsification_gates.md`'s G3 row requires the power-law fit
to the resistance-diameter/N data be "significantly better" than a
logarithmic (small-world) alternative model, with `R² ≥ 0.9` — but gives
no numeric criterion for what "significantly better" means beyond that
single-model floor. Comparing two non-nested regression models needs an
explicit decision rule, not an implied one.

**Default:** power-law preferred over logarithmic iff **both**: (a) the
power-law fit's own `R² ≥ 0.9` (the contract's stated floor, unconditional),
and (b) the power-law fit's `R²` strictly exceeds the logarithmic fit's `R²`
on the same `(N, resistance_diameter)` data. A simple `R²`-comparison, not
a formal nested-model test (e.g. AIC/BIC) — the two models have the same
number of free parameters (slope, intercept) so `R²` comparison is not
penalizing complexity asymmetrically, which would have been a real problem
with e.g. AIC if the models differed in parameter count.

**Evidence:** [WEAK] — a defensible, simple operational reading of
"significantly better fit," not derived from a formal model-selection
theory citation. Written into `finite_size_scaling.py`'s
`power_law_beats_logarithmic`.

**If wrong:** if `R²`-comparison alone proves too permissive in practice
(e.g. both models fit similarly well but power-law "wins" by a negligible
margin), revisit with a formal comparison (e.g. an F-test on the residual
sum of squares, since both models are linear-in-parameters after their
respective transforms) before trusting a borderline G3 verdict.

### A24 — adaptation step size dτ (found during Phase 8 implementation)

**Ambiguity:** `AdaptationRule.update(graph, trajectory, dtau)` takes a
`dtau: float` step-size parameter (§3.2's formulas are all written as
`dW_ij/dτ = ...`, a rate, requiring a step size to become an actual
update: `ΔW_ij = rate · dτ`), but no numeric value for `dτ` itself is
given anywhere in the contract — only `K` (fast-steps per adaptation
window, `[A9]`) and `dtau_steps` (number of adaptation windows, a config
field) are specified.

**Default:** `dτ = 1.0` per adaptation window, a fixed constant, not a
config parameter. Reasoning: every update rule's formula is
`ΔW_ij = η · dτ · (...)` — only the PRODUCT `η · dτ` has any effect on the
dynamics; `dτ` and `η` are perfectly degenerate free parameters in the
current formulation (scaling one and inverse-scaling the other leaves
every trajectory identical). Since `η` is already the swept, config-level
free parameter (`[A9]`'s sensitivity sweep), introducing a second,
independent `dτ` config knob would add a parameter with no additional
degree of freedom — it would only ever appear multiplied by `η`. Fixing
`dτ = 1.0` removes the redundant knob without losing any expressiveness:
any experiment that would have used a different `dτ` is exactly
reproduced by a rescaled `η`.

**Evidence:** [INFERRED] from the formulas' own structure (§3.2) — every
adaptation rule is linear in `η · dτ` with no other `dτ`-dependence
anywhere in the contract, so the degeneracy is a direct algebraic
consequence, not a guess.

**If wrong:** if a future revision introduces per-window-varying
adaptation dynamics (e.g. `dτ` itself changing over the run, or a term
that depends on `dτ` other than through the `η·dτ` product), this
degeneracy breaks and `dτ` needs to become a real, independently-swept
config parameter. Nothing here would need to change for `TopologyUpdateRule`
either, which takes the same `dtau: float` argument (`mathematical_
contract.md` §3.3) — same reasoning applies unless a topology rule is
added whose update is not linear in `dτ`.

### A25 — Arm E (Fixed Flat Geometry) source-node convention: single center node, not [A17]'s 5-source average (found during Phase 8 implementation)

**Ambiguity:** `[A17]` revised ψ(0)'s source node from a single fixed node
to a 5-source average for G5 (propagation front), specifically because a
single fixed node index on Erdős–Rényi (`[A7]`) has seed-dependent local
degree/clustering — confounding "effect of the dynamics" with "effect of
which node happened to be node 0." Arm E's topology is a periodic regular
lattice, not Erdős–Rényi. Does `[A17]`'s fix still apply to Arm E?

**Default:** No — Arm E keeps `[A6]`'s original single-lattice-center-node
convention, not `[A17]`'s 5-source average. Reasoning: every node in a
periodic regular lattice has *identical* degree and *identical* local
structure by construction (translation symmetry) — the seed-dependent
degree confound `[A17]` was built to remove does not exist here, because
there is no seed-dependent variation across node choice to average away.
Averaging over 5 lattice nodes would add noise (from the propagation
front's own genuine directional/geometric structure on a periodic lattice)
without removing any bias, since there is no bias to remove.

**Evidence:** [INFERRED] directly from `[A17]`'s own stated motivation
(seed-dependent degree confound) — Arm E's generative model structurally
lacks the property that motivated the fix, so the fix's justification does
not transfer. Not re-verified empirically (would require running both
conventions and comparing propagation-front variance across seeds).

**If wrong:** if Arm E's propagation front turns out to be direction-
dependent in a way that a single source node biases (e.g. faster along a
lattice axis than a diagonal), a future revision might average over
several lattice-symmetric source positions instead of literal random
draws — a different fix than `[A17]`'s, motivated by a different (genuinely
present) confound, not a blanket reapplication of the ER-specific one.

### A26 — G6 reference size across the FSS grid (found during Phase 10 implementation)

**Ambiguity:** `falsification_gates.md` states every Gate-A criterion,
including G6, is "evaluated per arm, aggregated across the full FSS grid —
never from a single N." For G2/G3/G4 this is unambiguous: they are
regression EXPONENTS fit jointly across all sizes, a single number per
arm for the whole grid by construction. G6 is different — it compares
Active's per-seed observable SAMPLES against each negative control's via
Cohen's d and CI overlap. The document never says how samples from
DIFFERENT sizes should combine into one G6 comparison: pooling raw
observable values across sizes into one sample array, or evaluating G6 at
one reference size, or something else entirely.

**Default:** evaluate G6 at the LARGEST configured size in the FSS grid
only (`max(config.sizes)`), not pooled across sizes. Reasoning: G1-G5's
own raw values are generally N-dependent by design (that dependence IS
what G2/G3/G4's exponents measure) — pooling e.g. IPR values from N=64
and N=512 into one sample array for a t-test-like comparison would
conflate genuine finite-size scaling with the arm-vs-arm separation G6 is
actually trying to detect, inflating variance for reasons unrelated to
whether Active differs from its negative controls. The largest available
N is the most asymptotically representative single size, and is also
where finite-size corrections (the thing FSS is measuring in the first
place) are smallest.

**Evidence:** [INFERRED] from the structural mismatch between G6's
per-seed-sample comparison and G2/G3/G4's per-grid regression — pooling
across sizes would need a size-covariate-aware statistical model this
project doesn't otherwise build, so picking a fixed reference size is the
simplest choice consistent with not silently conflating two different
sources of variance.

**If wrong:** if G6's verdict turns out to be highly sensitive to WHICH
size is chosen as the reference (e.g. flips STRONG/PARTIAL/FAIL between
N=343 and N=512), that sensitivity is itself worth reporting, and this
default should be revisited — e.g. by reporting G6 at every size in the
grid and requiring consistency, not just evaluating it once. Not resolved
here because no production data exists yet to know whether this
sensitivity is a real problem.

### A27 — G5 multi-source measurement uses the final graph, not a full evolving-history replay (found post-Phase-10, closing the deferred [A17] gap)

**Ambiguity:** `[A17]` requires `r_q(t)` averaged over 5 source nodes per
replicate. `gate_a_observables.py` (Phase 9 Cycle 21) only ever used
`source_nodes[0]`, deferring the other 4 with an explicit note ("needs
additional dynamics reruns from fresh source nodes, not just an array
reduction"). Closing that gap raises a real design question: should the
other 4 sources' pulses propagate through the SAME evolving-during-
adaptation sequence of Hamiltonians that source 0's own trajectory
produced (full-history replay), or through the FINAL adapted graph held
fixed (a fresh, independent probe)?

**Default:** the FINAL graph, fixed. A full-history replay is technically
possible in principle — the per-window Hamiltonian sequence is fully
determined by the initial graph, the adaptation rule, and source 0's own
trajectory, independent of what psi(0) the other sources would use — but
doing it requires capturing every intermediate per-window graph, a piece
of state nothing else in this codebase needs (`AdaptiveRunResult` only
ever kept `final_graph` + the state trajectories, not the graph at each
window boundary). Probing the FINAL graph instead answers a simpler,
well-defined question ("how does a fresh pulse spread through the final
geometry, averaged over independent starting points") that still
satisfies `[A17]`'s own original goal — removing single-node degree bias
from a disordered generative model — without needing that extra state.

**Evidence:** [INFERRED] from the structural cost of a full-history
replay (a genuinely new piece of persisted state) versus the final-graph
probe (reuses machinery already built: `dynamics/fast.py`,
`dynamics/classical.py`, `observables/propagation_front.py`'s own
`average_over_sources`, previously built but unused before this).

**If wrong:** if the final-graph-only measurement gives a materially
different G5 signature than a full-history replay would (plausible if
the geometry changes substantially over the adaptation run, not just at
the end), a future revision should add per-window graph capture to
`AdaptiveRunResult` and implement the replay version — a strictly larger
addition, not a redesign of what exists.

## Explicitly Not Resolved Here (deferred, not silently dropped)

- **A12 — degree-matching precision for Arm C (Parameter-Matched Random):**
  "matched edge count or degree constraints" — exact match vs. distributional
  match not chosen. Deferred to Phase 5 (arm implementation); default to
  exact edge-count match, revisit if that under-constrains the comparison.
- **A13 — stochastic trace estimator method for large-N spectral dimension**
  (§5 "for large N: stochastic trace estimator"): Hutchinson estimator is
  the standard choice but variance/sample-count tradeoff is not pinned here;
  deferred to Phase 6 (`observables/spectral_dimension.py`) design.
- **A22 — `StateTrajectory` doesn't type-distinguish quantum vs. classical
  carriers** (found during Phase 4 implementation, self-caught bug on
  `ClassicalHebbianAdaptation` first draft — `.claude/memory/decisions.md`).
  Both carriers share one dataclass (`states: NDArray[complexfloating]`),
  relying on convention (quantum rules fed `psi`, `ClassicalHebbianAdaptation`
  fed `p`) rather than the type system to prevent misuse. The actual bug
  this produced (density-via-correlation-diagonal being wrong for a real
  `p` trajectory) is fixed in `ClassicalHebbianAdaptation` itself, but
  nothing stops a *future* caller from feeding a classical trajectory to
  `HebbianAdaptation`/`AntiHebbianAdaptation`/`AlternativeObjective`
  (quantum-only rules) and getting a silently wrong result the same way.
  Not fixed now — a full type-level split (e.g. separate
  `QuantumStateTrajectory`/`ClassicalStateTrajectory` types) is a larger
  refactor than current time budget allows, and no code today actually
  misuses it (only Arm CD's future construction code, Phase 5+, would ever
  create a classical trajectory). Revisit before Phase 5 wires real arms
  together, when the actual call sites first exist.

## Resolution Protocol

If `boyko-minimal-experiment-v1.0.md` becomes available at any point:

1. Diff every entry above against v1.0's actual text.
2. Any entry v1.0 resolves differently → new dated addendum here, do not
   silently overwrite (Checkpoint Fidelity: superseded items keep the
   reason for the version change visible).
3. Re-run Gate 1 in `../../artifact-provenance-gates.md` terms: this whole
   register was built without the primary source; once the primary source
   exists, this register itself becomes the object under audit, not the
   authority.
