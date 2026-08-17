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

**Sweep grid, frozen 2026-08-13 (before any sweep data exists, per
EstimandOps "threshold chosen after seeing results is invalid" and this
project's own Falsification Ladder anti-fishing discipline):**

```
K   ∈ {10, 25, 50, 100, 200}
eta ∈ {0.02, 0.05, 0.1, 0.2, 0.4}
```

25 combinations, log-ish spaced around the `development.yaml` default
`(K=50, η=0.1)` — half/double steps in each direction, covering roughly
a 20x range in each parameter. Not derived from a timescale-separation
calculation (no closed-form relationship between `K`/`η` and `dt`/
`dτ_steps` exists in `mathematical_contract.md` to derive one from) — an
empirically reasonable bracket around the un-derived default, chosen
before seeing any sweep output.

**Cost constraint (found 2026-08-13):** `development.yaml`'s single
`(K=50, η=0.1)` point took 4292s (~71.5 min) at full scale (5 sizes × 5
seeds × 7 arms). Running this 25-point grid at that same scale would cost
~30 hours — infeasible as a single session's work and not necessary for
a robustness/no-collapse check, which only needs Active's own G1-G5
stability across `(K, η)`, not full G6 cross-arm MCID comparison.

**`configs/kappa_eta_sweep.yaml`** (added 2026-08-13): 2 smallest sizes
(`[64, 125]` — `run_phase`'s G1 convergence check requires ≥2 distinct
sizes, found empirically when a 1-size version raised `ValueError`), 3
seeds, and the 4 arms `run_phase` actually needs (Active + all three G6
comparators — `g6_wiring.build_g6_samples` raises `KeyError` if Frozen/
Parameter-Matched-Random/Topology-Scrambled are absent, so this is the
true minimum, not an arbitrary trim; Fixed Flat Geometry, Alternative
Objective, Classical Diffusion Control dropped). `dtau_steps=50`
(vs. development's 200).

**MEASURED cost** (not estimated) at this config's own default point:
**215.04s**. A pure N³-dynamics-cost extrapolation from `development.
yaml`'s 4292s predicted <1 minute for this config — the real number is
~3.6× that, because fixed per-replicate overhead (BFS hop distances,
G1-G4 eigendecompositions, orchestration) doesn't shrink with N³ the way
the dynamics integration does; noted here so a future estimate from this
project starts from a measured multiplier, not a re-derived guess. 25
grid points at this measured cost: **~90 minutes total** — feasible in
one sitting, and the config itself is committed
(`configs/kappa_eta_sweep.yaml`); only the surviving stable region, if
any, needs a subsequent full-arm confirmation at `development.yaml`
scale.

**Decision rule (frozen, not to be relaxed after seeing results):** the
sweep looks for a broad plateau of `(K, η)` where G1-G5 raw values are
stable (low seed-to-seed variance, no divergence/NaN) — not for the
single point that maximizes any gate's pass rate. A single "lucky pixel"
surrounded by unstable neighbors is evidence AGAINST robustness, not a
result to select.

**Sweep executed 2026-08-13, all 25 points, `results/kappa_eta_sweep/
raw.jsonl`.** Per the frozen decision rule above: reporting the stability
landscape, not a winning point.

- **`any_nonfinite` count: 0/25.** No divergence, no NaN, anywhere in the
  tested `(K, η)` range.
- **G1-G4 broad stability plateau**: `d_s_hat`, `γ`, `resistance_diameter`,
  IPR `η` all vary only in the 3rd-4th significant figure across the
  entire grid, at both sizes (N=64, N=125) — no visible dependence on
  `(K, η)` in this range. Consistent with `[A9]`'s hoped-for outcome.
- **G1 `g1_converged_fraction`: deterministically 1.0 at N=64, 0.0 at
  N=125, in ALL 25 points** — independent of `(K, η)` entirely. This is
  NOT a K/η-sensitivity finding; it is a separate, reproducible defect in
  `[A30]`'s `detect_plateau` calibration at N=125 with the current
  `t_values` grid/`slope_tolerance`, exposed BY this sweep rather than
  answering the question the sweep was run for. Needs its own
  investigation before trusting G1 at N≥125.
- **G5 `v_eff` — real bug found and fixed mid-sweep, not just a result:**
  the first full run of this sweep returned `v_eff=0.0` (std=0.0) at
  every one of the 25 points regardless of `K`/`η`, including points
  where `n_steps = dtau_steps·K` differed by 20× — an impossible
  coincidence for real dynamics, correctly treated as a measurement
  artifact rather than a finding (Substrate Gate discipline: "the
  measurement couldn't see the effect" ≠ "there is no effect"). Root
  cause: `detect_unsaturated_window` (`observables/propagation_front.py`)
  only ever scanned a growth run starting at index 0, so a real front's
  initial flat "quiet period" (radius stays 0 for several steps before
  the pulse spreads past the source node) was mistaken for immediate
  saturation. Fixed to scan the WHOLE array for its longest contiguous
  increasing run, not just from index 0 (regression test:
  `check_unsaturated_window.py::test_detect_unsaturated_window_skips_a_
  flat_lead_in_before_growth_starts`). The buggy run is archived, not
  discarded, at `results/kappa_eta_sweep/raw_g5-window-bug_2026-08-13.
  jsonl` — re-run after the fix gives `v_eff≈20.0` (finite, non-degenerate)
  at every point.
- **G5 `v_eff` after the fix was ALSO uniform (~20.0) across all 25
  points — investigated 2026-08-13, resolved into two separate findings,
  not one:**
  1. **Second real algorithmic bug, fixed:** `detect_unsaturated_window`'s
     "longest strictly-increasing run" degenerates to exactly 2 points on
     real hop-count-quantized data, which is a STAIRCASE (each integer
     radius held for many steps before the next jump) — no run of more
     than 2 points is ever strictly increasing in a staircase. Confirmed:
     transition indices `[16, 42, 73]` were bit-identical for K=10 and
     K=200 (a 20x adaptation-budget difference), because both picked the
     same single first jump mechanically (`v_eff = 1/dt = 20.0` always),
     not because the real dynamics were identical. Fixed: trim only the
     flat lead-in and flat trail, keep everything in between (every
     intermediate plateau's timing) — `tests/unit/check_unsaturated_
     window.py::test_detect_unsaturated_window_spans_a_whole_staircase_
     not_just_one_jump`. Re-run on real data: `v_eff` changes from `20.0`
     to `0.573` (a genuine average velocity across the full 59-point
     rise, not a single hop) — 201/201 tests (was 200), all 5 prior
     `detect_unsaturated_window` tests unchanged and still passing.
  2. **After that fix, `v_eff` is STILL bit-identical (`0.572764`) for
     K∈{10,25,50,100,200} at fixed η=0.1 — this time confirmed NOT a
     window-detection artifact.** Directly compared the two arms' final
     adapted graph WEIGHTS (not just G5's derived radius): K=10 vs K=200
     final weights genuinely DIFFER (max abs diff 0.271, means 0.922 vs
     0.925) — adaptation IS sensitive to K at the weight level. G5's
     integer-hop-count/`q=0.9`-threshold measurement is simply too
     COARSE a diagnostic to detect that real difference: a ~20-30% edge-
     weight perturbation isn't enough to shift which discrete radius
     crosses the density threshold at the tested `n_steps`. This is a
     genuine RESOLUTION LIMITATION of G5 as currently defined, not a bug
     to silently patch — a design question (e.g. a continuous/interpolated
     front-crossing time instead of an integer hop threshold, or a
     higher-resolution `q`) for whoever next revisits G5, out of scope
     for this sweep.

**Cost, actual (not the pre-run estimate):** 25 points took 1609.7s
(~27 min) on the first (buggy) run and 1882.2s (~31 min) on the corrected
re-run — both well inside the ~90-minute estimate, since per-process
warmup cost amortizes across all 25 points run in one Python process
(the ~215s single-run measurement that produced the 90-minute estimate
paid a one-time cold-start cost the batch runner doesn't repeat).

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

### A28 — `normalized_laplacian` on a zero-degree (isolated) node (found 2026-08-13, first `development.yaml` full-grid run)

**Ambiguity:** `HebbianAdaptation`'s Oja-normalized decay term (`[A3]`)
can drive all of a node's incident weights to exactly zero over a long
enough adaptation budget — a legal state under `[A5]`'s non-negativity
floor (the mask/topology is untouched, only weights decay; `NoTopologyUpdate`
governs Active). `mathematical_contract.md` §1.2 defines
`normalized_laplacian` as `I - D^-1/2 W D^-1/2` but never specifies what
`D^-1/2` means for a node with `degree=0` — the formula is undefined
there (`1/sqrt(0)`), not just numerically unstable.

**Default:** `d_inv_sqrt[i] = 0` for any node `i` with `degree(i) = 0`
(`graphs/weights.py::normalized_laplacian`). Consequence: row/column `i`
of the scaled-weight term is all-zero, so `L_norm`'s diagonal entry for
node `i` stays `1` and it couples to no neighbor in the dynamics operator
— an isolated node behaves as its own disconnected 1-node component for
the purposes of the fast-dynamics Hamiltonian, consistent with the
standard graph-Laplacian convention for isolated vertices (e.g. Chung
1997's treatment of `L_norm` on graphs with isolated vertices).

**Evidence:** [VERIFIED-pytest] `tests/unit/check_normalized_laplacian_
isolated_node.py` — a hand-constructed 3-node path graph with all weights
decayed to `0.0` previously produced `NaN` throughout `L_norm` (confirmed
via the actual `development.yaml` crash traceback:
`ValueError: weights must be symmetric`, itself a downstream symptom —
`NaN` is never `np.allclose`-equal to `NaN`, so the real defect surfaced
as a spurious symmetry violation several call frames away from its cause).
With the `d_inv_sqrt=0` guard, the same input produces a finite, symmetric
`L_norm` (both regression tests pass).

**If wrong:** if isolated-node behavior should instead mean something
else physically (e.g. the node should be excluded from G1-G5 entirely
for that replicate, or its emergence should itself be flagged as a
Gate-A-relevant event — a node losing all weight IS a form of geometric
degeneration, arguably interesting rather than a nuisance to suppress),
this convention should be revisited once production runs show how often
isolated nodes actually occur and whether their rate correlates with
Active vs. negative-control arms. Not resolved here because no
production-scale frequency data exists yet.

### A29 — `generate_erdos_renyi` connectivity is enforced by rejection sampling, changing the realized population (found 2026-08-13, second `development.yaml` full-grid run; red-team addendum same day)

**Ambiguity:** `nx.gnm_random_graph`'s exact edge-count draw has no
connectivity guarantee. At `N=64`, mean degree 6 (`[A7]`, `n_edges=192`),
a disconnected draw is empirically reachable (witness:
`numpy.random.default_rng(18)` — brute-force search, not cherry-picked
from the actual failing `development.yaml` seed, which was never
captured). `estimand.md`'s Population field (§L1) and its ICE section
*already* declared the intended design correctly — "restricted by design
to connected graphs only (disconnected draws are rejection-sampled, not
analyzed)" — before this fix existed. This entry closes a documentation-
vs-implementation gap, not a documentation gap: `graphs/generators.py`
did not yet implement what `estimand.md` already specified.
`hop_distances_from_source` (`observables/propagation_front.py`)
correctly refused to proceed on an unreachable node, which is how the
gap first surfaced (`ValueError: hop_distances contains unreachable (-1)
nodes`).

**Default:** `generate_erdos_renyi` retries with a fresh `networkx` seed
(same `n_nodes`/`n_edges`) up to 20 times if a draw is disconnected,
raising `nx.NetworkXAlgorithmError` only if all 20 attempts fail — the
same bounded-retry pattern `graphs/rewiring.py::scramble_preserving_
degree_sequence` already uses for its own stochastic-failure case
(`[A21]`'s `_MAX_RETRY_ATTEMPTS`).

**Evidence:** [VERIFIED-pytest] `tests/unit/check_erdos_renyi_
connectivity.py` — `numpy_seed=18` deterministically produced a
disconnected graph before this fix, connected after; edge count is
preserved exactly across retries (both regression tests pass).

**Why this matters beyond the crash (red-team point, 2026-08-13):**
rejecting disconnected draws and resampling is **selection on the
outcome**, not a cosmetic bug fix. The realized population is
`G ~ ER(N, n_edges) | G is connected`, not the unconditional
`G ~ ER(N, n_edges)`. Conditioning on connectivity can shift the degree
distribution, low-Laplacian-eigenvalue structure, effective resistance,
mixing time, and spectral dimension relative to the unconditional
ensemble — precisely the quantities G1-G5 measure. This is not
necessarily wrong (several observables, e.g. `resistance_diameter`, are
undefined on a disconnected graph in the first place, so *some* form of
connectivity conditioning is required for the benchmark to be well-posed
at all) — `estimand.md` already made exactly this choice explicitly
(§L1 Population, ICE section) before this fix existed. What was missing
was only the implementation, now closed. Both the Active-lineage arms
and Arm C (Parameter-Matched Random) already apply the identical
connectivity rule by construction — `arms/shared_initialization.py` calls
the same `generate_erdos_renyi` for both (line 38 for Active's shared
init, line 52 for Arm C's independent draw) — so there was never a risk
of the "matched" in "Parameter-Matched Random" silently diverging between
arms; fixing the one function fixed both call sites identically.

**If wrong (numerical residual):** if some `(N, mean_degree)` combination
in the FSS grid has a much higher disconnection rate than the `N=64`
witness (sparser large-N configurations are more at risk), 20 retries may
not be enough and the `NetworkXAlgorithmError` would surface as a
production-run failure rather than a silent bias — treated as a fail-loud
outcome, not swept under a higher retry count without first checking
whether that `(N, mean_degree)` pair is even a sound design choice.

### A30 — G1 plateau-detection algorithm and thresholds (found 2026-08-13, after external red-team review of `development-v0`)

**Ambiguity:** `mathematical_contract.md` §5.1 requires `d_s(t) ≈ const`
"over an intermediate diffusion-time window" but does not specify how to
locate that window algorithmically — no threshold, no minimum point
count, no tiebreak rule for multiple candidate windows. The pre-2026-08-13
implementation (`d_s(t_last)`) was a placeholder, self-disclosed as such
in `cell_aggregation.py`'s own docstring and `activeContext.md`.

**Default:** `observables/spectral_dimension.py::detect_plateau` scans
every contiguous window of `t_values`/`d_s(t)` with `>= min_points=3`
points; a window qualifies if `|slope of d_s vs log(t)| <= slope_
tolerance=0.1` (linear regression). Among qualifying windows, prefer (1)
most points, (2) widest log-t span as tiebreak. If no window qualifies,
`converged=False` is returned along with a `d_s(t_last)` fallback value
— callers must check `converged` before trusting the estimate
(`cell_aggregation.CellObservableStatistics.g1_converged_fraction`
surfaces this per-cell, across seeds).

**Deliberately NOT used:** an R²-of-the-flat-fit threshold (proposed in
the same external review). For a genuinely flat window, `R²` of a linear
fit is close to meaningless — near-zero true slope makes `scipy.stats.
linregress`'s `rvalue` numerically unstable (small denominators), so a
"require high R²" gate would sometimes reject perfectly flat data purely
from floating-point noise. `|slope| <= tolerance` tests the property that
actually matters ("is `d_s` roughly constant here"); `R²` is still
reported in `PlateauResult` as a secondary diagnostic, not used as a gate.

**`t_values` grid:** widened from the previous 3-point `[0.5, 1.0, 2.0]`
(hardcoded in `scripts/run_smoke.py`) to a 12-point log-spaced grid over
`[0.1, 10.0]` (`np.geomspace`) — 3 points cannot support plateau
detection at all (`min_points=3` forces the entire array into one
window, with no ability to exclude a short-time rise or a finite-size
tail). Still provisional: neither the `[0.1, 10.0]` range, the 12-point
density, nor `slope_tolerance=0.1` have been calibrated against real
Active-arm `d_s(t)` curves — no production run exists yet to calibrate
against, and calibration should use the existing ring/lattice calibration
tests (`test_cubic_lattice_has_ds_near_3` etc.) as a sanity floor before
trusting it on Active's actual (non-lattice) geometry.

**Evidence:** [VERIFIED-pytest] `tests/unit/check_spectral_dimension_
plateau.py` — 5 hand-derived synthetic cases (flat middle region,
no-plateau monotonic data, all-constant data, point-count tiebreak,
below-minimum-points), all numerically cross-checked via a Bash prototype
against `scipy.stats.linregress` before the assertions were written (same
discipline as every other observable in this project).

**If wrong:** if `slope_tolerance=0.1` proves too loose (accepts a
window that is not really flat, e.g. a slow monotonic drift across the
whole grid) or too tight (never converges on real, noisier dynamics
data), this should surface as a low `g1_converged_fraction` across many
cells in `development-v2` — treated as a signal to recalibrate the
threshold against real curves, not as evidence against the Stage-1 claim
itself. Not resolved further here because no real Active-arm `d_s(t)`
data exists yet to calibrate against.

**Correction, found 2026-08-13 investigating the `[A9]` sweep's own
100%-converged-at-N=64/0%-converged-at-N=125 asymmetry:** that asymmetry
was itself a false-positive artifact, not a real N-dependent effect.
Real Active-arm `d_s(t)` curves rise toward a peak (around
`t≈4.3` in the tested `[0.1,10]` grid) then DECLINE at larger `t` — not a
plateau at all. A rise-then-fall window can have a near-zero AGGREGATE
linear-regression slope purely because the rise and fall cancel out
(witness, N=64: window `[1.97, 2.60, 3.14, 3.27, 2.61, 2.03]`, slope
`-0.032` — within tolerance — but `R²=0.002`, i.e. almost certainly NOT
actually flat; range 1.3). Slope alone cannot distinguish "flat" from
"symmetric hump," and this specific curve shape happened to fool the
slope-only gate at N=64 but not at N=125 (different numbers, same
underlying non-plateau shape) — that coincidence, not N-dependence,
produced the 100%/0% split.

**Fix:** added a second, independent gate: a qualifying window must also
have `max(d_s in window) - min(d_s in window) <= range_tolerance=0.3`.
Range directly tests the property slope-alone missed. Re-running the
same N=64/N=125 comparison after the fix: **both now correctly report
`converged=False`** — the asymmetry is gone, and the honest reading is
that NEITHER size shows a genuine plateau within this pilot config's
`t_values=[0.1,10]` grid and `dtau_steps=50` adaptation budget. This is
not a regression — a false "yes" is worse than an honest "not enough
data," per this project's own Substrate/Oracle Adequacy discipline. The
real open question this surfaces: does `d_s(t)` ever genuinely plateau
for Active within a longer/differently-ranged `t_values` grid, or does
production's `dtau_steps=200`+ budget change the curve's shape entirely?
Neither is answered here — needs a `t_values` grid extended well past
`t=10` (or a longer adaptation budget) before G1 can be trusted on real
Active data, separate from `[A9]`'s own `(K,η)` question.

**Evidence (correction):** [VERIFIED-pytest]
`check_spectral_dimension_plateau.py::test_detect_plateau_rejects_a_
rise_then_fall_hump_with_near_zero_net_slope` — hand-derived hump
(`[0.5,1.8,3.5,4.5,5.0,3.5,1.5]`), cross-checked via Bash prototype:
without the range gate, a 6-point window `[1.8,3.5,4.5,5.0,3.5,1.5]`
(slope=-0.035, range=3.5) would be accepted; with it, correctly rejected,
`converged=False` for the whole array. All 5 prior tests unchanged and
still passing (200/200 total, was 199).

**Second correction, found 2026-08-13 investigating whether widening
`t_values` (past `[0.1,10]`) would reveal a real plateau for the N=64/
N=125 curves the first correction above left unresolved.**

Computed `d_s(t)` on a much wider/denser grid (`t ∈ [0.01, 1000]`, 30
log-spaced points) for the SAME Active-arm graph at N=64, N=125, AND
N=512 (the largest `development.yaml` size) to settle the question with
real data instead of guessing:

```
N=64:  peak d_s≈3.32 near t≈3.9,  then falls to ~0 by t≈40
N=125: peak d_s≈3.82 near t≈5.7,  then falls to ~0 by t≈60
N=512: peak d_s≈5.00 near t≈8.5,  then falls to ~0 by t≈90
```

**Conclusion: this is NOT a `t_values`-range problem to tune away.**
Every size shows the identical qualitative shape — a single peak, no
flat region anywhere — and the peak VALUE grows with `N` (3.3→3.8→5.0)
instead of converging to a fixed value as `N` grows, which is the
opposite of what a genuine geometric dimension should do (a real
geometric graph's calibration tests, e.g. cubic lattice, show `d_s≈3`
regardless of `N`). This pattern (fast initial return-probability decay,
peak height growing with `N`, no stable intermediate regime) is the
textbook signature of an expander/small-world graph, not a graph with
genuine low-dimensional geometric structure. At `dtau_steps=50` (this
pilot config's budget), Active's mean edge weight is still `0.92-0.93`
(initial weight was `1.0`) — the graph has barely adapted away from its
Erdős–Rényi starting point, so what G1 is measuring here is essentially
"what does an unadapted ER expander's `d_s(t)` look like," not yet
evidence about whether Hebbian adaptation ever produces a genuine
geometric-phase plateau. **The open question this leaves is whether a
longer adaptation budget (`development.yaml`'s own `dtau_steps=200`, 4x
this pilot's `50`) changes this shape — not resolved here, and not
answerable by adjusting `t_values` alone.**

**Third fix (found investigating the wide-range data above):** the
range+slope gates alone are ALSO fooled by the trivial long-time tail —
`P_return(t) → 1/N` (a constant) as `t → ∞` on any finite connected
graph, so `d_s(t) → 0` for large enough `t` on every curve, universally,
regardless of geometry. That decayed tail is genuinely flat (small
slope, small range) and was accepted as a false-positive `d_s_hat≈0.003-
0.03` "plateau" — not a real near-zero-dimensional finding, just the
universal asymptote. Added `min_d_s_hat=0.5` (provisional, same
uncalibrated status as the other two thresholds; chosen well under every
real calibration target — ring~1, square~2, cubic~3 — but well above the
observed decay-noise range).

**Evidence (second correction):** [VERIFIED-pytest]
`test_detect_plateau_rejects_a_trivially_decayed_zero_tail` — hand-
derived decay tail, reproduces the exact false-positive
(`d_s_hat=0.0297, converged=True` before the fix); rejected after. Full
re-run of the wide-range N=64/125/512 investigation after the fix: ALL
THREE now correctly report `converged=False` — consistent with the "no
real plateau at this budget" conclusion above, not contradicting it.
202/202 tests (was 201), all 6 prior `detect_plateau` tests unchanged
and still passing.

**`development-v1` (2026-08-13, full `development.yaml` scale,
`dtau_steps=200` — the config's own default, no override needed):
CONFIRMS the expander-not-geometry finding above at the full adaptation
budget, not just the cheap pilot's `dtau_steps=50`.**

```
N=64:  d_s_hat=2.03  (0% seeds converged)
N=125: d_s_hat=3.18  (0% seeds converged)
N=216: d_s_hat=4.13  (100% seeds converged — see caveat below)
N=343: d_s_hat=4.79  (0% seeds converged)
N=512: d_s_hat=5.26  (0% seeds converged)
```

`d_s_hat` climbs monotonically with `N` — the same qualitative pattern
found investigating `t_values` at the smaller pilot scale, now confirmed
at 4x the adaptation budget. A real geometric dimension converges to a
fixed value as `N` grows (calibration: cubic lattice always `d_s≈3`
regardless of `N`); a value that keeps climbing is expander/small-world
behavior, not genuine geometric structure. Full `PROVENANCE.md`:
`results/development-v1/` (gitignored, on disk only).

**N=216's "100% converged" investigated 2026-08-14 — confirmed a fluke,
not a real plateau, consistent with (not an exception to) the expander
pattern above.**

All 5 seeds' `d_s(t)` on the `[0.1,10]` grid are near-identical (not
noise-driven): rise steadily to `≈4.1-4.24` near `t=4.3-6.6`, then dip
slightly by `t=10` (`≈4.09-4.11`) — those last 3 points happen to clear
`[A30]`'s 3 gates (`slope≈0.02-0.09`, `range≈0.15-0.2`, `mean≈4.1`) by
coincidence of where the truncated `[0.1,10]` grid happens to end,
relative to where this size's broader peak sits.

Re-ran a single seed on a WIDER grid (`t ∈ [0.1,100]`, 20 points) to
check whether the curve keeps declining past `t=10` the same way every
other size's did: **it does** — `d_s(t)` continues `4.31 (peak) → 4.03 →
2.68 → 1.06 → 0.22 → 0.023 → 0.001 → 0`, the identical expander-hump
shape as N=64/125/343/512, just with a slightly broader/flatter peak
region that the narrower `[0.1,10]` grid happened to catch inside
tolerance. On the wider grid, `detect_plateau` correctly returns
`converged=False` here too (rejected by `min_d_s_hat` once the tail
decays, same as every other size).

**Conclusion: N=216 is not an exception — it CONFIRMS the pattern.**
Every tested size in `development-v1`'s FSS grid shows the same
qualitative shape; N=216's apparent convergence was a grid-truncation
artifact, not evidence of a real geometric-phase signal at that specific
size.

Full verdict at this scale: `FAILS_GEOMETRIC_PHASE_SCREEN`
(G1/G2/G3/G5/G6 FAIL, G4 PASS) — still only `seeds_per_arm_size=5`,
below the production floor (≥20), so not a final Stage-1 falsification,
but the expander-pattern finding is now supported at both tested
adaptation budgets, not just the shorter one.

### A31 — Correlation Shuffle secondary control (proposed 2026-08-13, external red-team review)

**Ambiguity:** none of the seven primary arms isolate the specific
question "does it matter WHICH pair of nodes correlated, or does any
reinforcement with the same correlation-magnitude distribution produce
similar geometric organization?" Arm F (Alternative Objective) tests a
different adaptation RULE; this tests the same rule with the
correlation-to-edge ASSIGNMENT scrambled — a different, complementary
axis (mechanism-of-organization vs. choice-of-rule).

**Default:** `dynamics/adaptive.py::CorrelationShuffleAdaptation` — same
Oja-normalized update as `HebbianAdaptation`, but the off-diagonal
correlation values are permuted across the graph's existing edges each
`update()` call (`_shuffle_edge_correlations`, fresh permutation per call
from the injected `rng`, not fixed once at construction). `H1`:
Active ≫ Frozen AND Active ≫ CorrelationShuffle → which specific pair
correlated is causally load-bearing. `H0`: Active ≫ Frozen BUT
Active ≈ CorrelationShuffle → adaptation matters, but the structured
assignment of correlations to edges does not — a materially weaker
causal story than the current framing implicitly assumes.

**Scope cut (deliberate, matching `[A26]`'s own pattern):** implemented
as a usable `AdaptationRule` only. NOT wired into `config.py`'s `Arm`
enum, `arms_runner.py`, or the G1-G6 primary verdict — the external
review's own caution against moving goalposts mid-flight applies here:
this is registered as a secondary mechanism diagnostic to run AFTER
`[A9]`'s sweep and G1 recalibration, not folded into the current 7-arm
G6 MCID comparison. Full wiring (an 8th arm value, a runner function
analogous to `run_arm_active`, a place in `mathematical_contract.md` §4,
and a decision on whether it counts toward G6's 15-cell matrix or stays
a separate report) is the documented next step, not done here.

**Evidence:** [VERIFIED-pytest] `tests/unit/check_correlation_shuffle.py`
— 5 hand-derived cases (multiset preservation, exact permutation match
against a Bash-prototype-verified `rng.permutation` call, non-edge/
diagonal zeroing, divergence from `HebbianAdaptation` on identical input,
graph-invariant preservation), all passing.

**If wrong:** if `CorrelationShuffleAdaptation`'s per-call fresh
permutation (rather than one fixed permutation for the whole run) turns
out to average out any structural effect entirely by construction
(shuffling every step could behave like uncorrelated noise regardless of
whether H0 or H1 is true, making the control uninformative rather than a
fair test) — this should be checked against a variant using ONE fixed
permutation for the full adaptation run before trusting either verdict.
Not resolved here because no run of either variant exists yet.

### A32 — Cheapest differentiating test: does HebbianAdaptation destroy geometry that already exists? (2026-08-14, pre-registered before any open-system/dissipative-dynamics implementation work)

**Question this answers:** the expander-not-geometry finding (`[A30]`) was
found starting from a DISORDERED Erdős–Rényi graph under a CLOSED unitary
system. Before investing in an open/dissipative-dynamics reimplementation
(a real red-team-review-motivated next step, `boyko-minimal-experiment-
v1.0.md`'s actual spec — provenance unconfirmed, see `decisions.md`), the
cheapest possible test that could rule out one branch of explanation: is
`HebbianAdaptation` itself anti-geometric (destroys structure wherever it
finds it), or does it merely fail to CREATE structure from disorder
(leaving already-existing geometry alone)? These predict opposite things
about whether adding dissipation is worth trying.

**Method:** applied the SAME `HebbianAdaptation` (not `NoAdaptation`, which
is what Arm E / Fixed Flat Geometry actually uses per `mathematical_
contract.md` §4 — "positive geometric calibration only, never an
optimization target") to a periodic cubic lattice (N=64, side=4) instead
of a disordered ER graph. Same pilot budget as `[A9]`'s sweep: K=50,
η=0.1, `dtau_steps=50`.

**Result:** `d_s(t)` before and after adaptation are near-identical:

```
before: [..., 3.107, 3.173, 2.537, 2.027]  (t=2.85..10)
after:  [..., 3.105, 3.169, 2.534, 2.025]
```

Weights after adaptation: mean 0.933, std 0.109, range [0.51, 0.97] —
mildly perturbed, not collapsed toward uniformity or driven to extremes.
Wide-range check (`t∈[0.1,100]`) confirms the same peak-then-decay shape
seen for Active, peak ≈3.25 near t≈6.6 — critically, the peak stays near
the lattice's TRUE dimension (3), does NOT grow with adaptation the way
Active's peak grows with N.

**Interpretation:** `HebbianAdaptation` does NOT measurably destroy
pre-existing geometric structure at this budget. This favors the
"cannot create order from disorder under closed dynamics" explanation
over "the rule is inherently anti-geometric" — meaningfully improves the
prior for open/dissipative dynamics being worth trying, since a
dissipative system's actual relaxation-to-equilibrium behavior (which a
closed unitary system structurally lacks) is exactly the kind of thing
that could complete the "create order from disorder" step this closed-
system test shows doesn't happen on its own.

**Caveats (explicit, not to be silently promoted past this evidence
level):** n=1 seed, 1 `(K,η,dtau_steps)` point, N=64 only. Even the
UNADAPTED raw lattice fails `[A30]`'s 3-gate `detect_plateau` on the
standard `[0.1,10]` grid (`converged=False`) — the same grid-truncation
sensitivity found investigating N=216 (`[A30]`) affects genuine geometry
too, not just Active's expander-like curves; `detect_plateau`'s
provisional thresholds are not yet calibrated on confirmed-geometric
cases at small N, a real gap for whoever tightens `[A30]` next.

**If wrong:** if a broader sweep (more seeds, more `(K,η)`, larger N)
shows the lattice's peak DOES drift with more adaptation budget or
different parameters, this conclusion reverses — not resolved here, this
is a single cheap pilot point, not a swept confirmation.

### A33 — ω_ref for dimensionless (γ, σ) parameterization, Phase 11 (open-system pilot ТЗ §9)

**Ambiguity:** the Phase 11 ТЗ requires dissipation/noise be parameterized
dimensionlessly relative to "a characteristic dynamical frequency
`ω_ref`, e.g. via spectral scale of the used Hamiltonian" — but doesn't
name the exact quantity. Several candidates exist: the current graph's
actual spectral radius (precise but graph-/time-dependent, drifts as
Active adapts), the mean nonzero eigenvalue, or the operator's a priori
bound.

**Default: `ω_ref = 2`** — the FIXED upper bound on `L_norm`'s spectrum,
already established and proven in this project (`mathematical_
contract.md` §2 / `[A1]`: "spectrum bounded in `[0, 2)` regardless of
weight/degree magnitude"). `γ̃ = γ/ω_ref`, `σ̃` normalized the same way
relative to state-vector scale (§9).

**Why this default, not a graph-dependent one:** (1) it is already a
PROVEN property of `H(W) = L_norm(W)`, not a new empirical estimate to
justify or recompute; (2) it is graph- and adaptation-time-independent,
so `(γ̃, σ̃)` mean the same physical thing at every point in the FSS grid
and at every adaptation step — critical for the Phase 11 pilot's factorial
design (§10) and `D_OC` open-vs-closed trajectory comparison (§12.2),
both of which require a stable, comparable reference across cells; (3) it
costs nothing to compute (no eigendecomposition needed just to fix the
scale).

**Evidence:** [VERIFIED] `L_norm`'s `[0,2)` bound is a standard spectral
graph theory result for the normalized Laplacian (Chung 1997), already
cited and relied upon elsewhere in this project (`mathematical_
contract.md` §2, `[A1]`).

**If wrong:** if `ω_ref=2` proves too coarse (e.g. most graphs in the FSS
grid have real spectral radius well under 2, making `γ̃=1` correspond to
wildly different ACTUAL damping strength relative to the graph's real
dynamics), a graph-dependent `ω_ref` (e.g. `λ_max(L_norm)` recomputed per
replicate at `τ=0`, held fixed for that replicate's whole run — not
recomputed every adaptation step, to preserve within-replicate
comparability) should be substituted. Not resolved further here — Phase
11 Milestone 1's T1/T2/T8 regression tests do not depend on which
`ω_ref` is chosen, so this can be revisited without invalidating them.

### A34 — Noise model for PhenomenologicalOpenBackend (Phase 11 ТЗ §7 step C)

**Ambiguity:** ТЗ §7/§8 requires "complex Gaussian/Rademacher noise
according to a fixed model" but doesn't pick one.

**Default:** complex standard normal — independent real and imaginary
parts, each `N(0, 0.5)`, giving `E[|ζ|²]=1`. Standard convention for
complex white noise (matches the `⟨ξ_i(t)ξ_j*(t')⟩` correlator form the
`[UNKNOWN provenance]` v1.0-like document itself uses, §2.1).

**Evidence:** [WEAK] — a conventional choice, not derived from this
project's own contract (which doesn't specify a fast-dynamics noise term
at all outside Phase 11).

**If wrong:** T3 (Ornstein–Uhlenbeck variance convergence test, ТЗ §22)
will directly catch a wrong normalization — the empirical variance won't
match the analytic OU prediction if `E[|ζ|²]` is off by a constant factor.

### A35 — T7 / Milestone 2 result: open dynamics does not destroy lattice geometry, but γ=0.1 (γ̃=0.05) nearly freezes Hebbian weight movement (2026-08-14)

**Question this answers:** ТЗ §22/§31's Milestone 2 gate — does at least
one nonzero `(γ,σ)` regime leave `[A32]`'s lattice positive control
intact? Repeated `[A32]`'s exact setup (N=64 lattice, K=50, η=0.1,
`dtau_steps=50`) at all 4 factorial pilot cells (ТЗ §10) using
`PhenomenologicalOpenBackend` via the new `experiment/open_pilot.py`.

**Result — all 4 cells pass, none destroy the lattice signature:**

```
BEFORE (unadapted):        peak d_s ≈ 3.173
C0    (γ=0,   σ=0):        peak d_s ≈ 3.169, weights std=0.109
Cγ    (γ=0.1, σ=0):        peak d_s ≈ 3.173, weights std=0.007
Cσ    (γ=0,   σ̃=0.05):     peak d_s ≈ 3.074, weights std=0.173
Cγσ   (γ=0.1, σ̃=0.05):     peak d_s ≈ 3.173, weights std=0.010
```

(`γ̃=0.05` → `γ=γ̃·ω_ref=0.1` per `[A33]`.)

**Mechanistic caveat — worth surfacing now, not silently absorbed by
"the test passed":** `Cγ`'s weight std (0.007) is over an order of
magnitude smaller than `C0`'s (0.109) — dissipation at this strength
appears to nearly FREEZE Hebbian weight movement at this `K`/`dt`/
`dtau_steps` budget, not merely protect existing geometry from
disruption. `Cγσ` (both nonzero) looks dominated by the same freezing
(std=0.010, close to `Cγ`'s), suggesting `γ=0.1` may already be strong
enough to suppress noise's own effect too, at least at this scale.

**Why this matters for Milestone 3 (not resolved here):** if `γ=0.1`
freezes weight movement on a LATTICE (which already has the target
structure, nothing to reorganize), it plausibly also freezes movement on
Active's DISORDERED starting graph — meaning this specific `γ` value
might trivially pass "doesn't destroy geometry" for a reason that has
nothing to do with geometry: it may prevent the correlation-driven
Hebbian signal from accumulating fast enough to move weights much at
all, regardless of starting structure. `D_W` (ТЗ §12.1, weight
trajectory magnitude) directly measures this and should be checked on
Active BEFORE trusting any Milestone 3 factorial-pilot verdict at this
`γ` value — a near-zero `D_W` on Active at the same `γ` would mean the
pilot cell tests "does frozen-in-place count as geometric," not "does
open dynamics enable organization."

**Evidence:** [VERIFIED-pytest] `check_open_pilot.py::test_t7_open_
dynamics_does_not_destroy_lattice_geometry` — numbers cross-checked via
a background investigation script before writing the assertion
(`peak_after` within `±1.0` of `peak_before` for all 4 cells; exact
weight-std numbers recorded above are from that same run, not re-derived
in the test assertion itself, which only checks the geometry-non-
destruction gate).

**If wrong:** if a wider `(K,η,dtau_steps)` grid shows `γ=0.1` does NOT
freeze Active's weight movement (i.e. this freezing is lattice-specific,
not a general property of this `γ`), the caveat above does not apply —
not resolved here, needs the actual Milestone 3 Active-arm run to check.

**CONFIRMED on Active 2026-08-14, `observables/trajectory_divergence.py`
(`D_W`, `D_OC`, ТЗ §12.1-12.2), same pilot budget (N=64, K=50, η=0.1,
`dtau_steps=50`):**

```
C0    (closed):            D_W = 0.079,   weight std = 0.0278
Cγ    (γ=0.1):              D_W = 0.0067,  weight std = 0.0061   <- ~12x smaller than C0
Cσ    (σ̃=0.05):             D_W = 0.500,   weight std = 0.1149
Cγσ   (γ=0.1, σ̃=0.05):       D_W = 0.064,   weight std = 0.0120
D_OC (Cγ vs C0):            0.081
```

**This is not a lattice-only artifact — γ=0.1 freezes Active's weight
movement too, by roughly the same order of magnitude (~12x less D_W than
closed baseline).** `[A35]`'s risk is realized, not hypothetical.
**Consequence for Milestone 3, flagged rather than silently acted on:**
`γ=0.1` is very likely the WRONG value to test "does dissipation enable
organization" — at this `K`/`dt`/`dtau_steps` budget it mostly just
suppresses adaptation itself. Per this project's own anti-parameter-
fishing discipline (ТЗ §9: "no more than 2-3 nonzero levels... forbidden
wide parameter fishing"; ТЗ §31: "no new parameters after viewing
confirmatory data"), the fix is NOT to quietly pick a new `γ` and
re-run — that would itself be exactly the kind of reactive parameter
selection the ТЗ's stop rules exist to prevent. **This is instead a
pre-registration decision the user should make explicitly before
Milestone 3 starts**: either (a) choose a smaller `γ̃` pilot grid a
priori (e.g. `γ̃∈{0.005,0.01,0.02}` instead of `{0.05}`, reasoned from
this `D_W` evidence, frozen BEFORE running), or (b) increase `dtau_steps`
so the same `γ` has more adaptation windows to accumulate movement in,
or (c) proceed with `γ=0.1` anyway and treat `OPEN_DYNAMICS_NO_EFFECT`
at this value as itself informative (ТЗ §16's own valid verdict). Noted
here as a blocking decision point, not resolved unilaterally.

**Csigma's `D_W=0.50`** (vs `C0`'s `0.079`) confirms noise alone moves
weights substantially MORE than the closed baseline's own natural
drift — worth keeping in mind for Milestone 3's interpretation: some of
`Cσ`'s effect on any Gate-A observable could be pure noise-driven
homogenization (ТЗ's own H5 hypothesis, §3) rather than structured
reorganization, and needs the modularity/conductance observables (§12.6-
12.7, not yet implemented) to distinguish.

**RESOLVED 2026-08-14 — user chose option (c) explicitly.** Milestone 3's
factorial pilot proceeds with `γ̃=0.05` (γ=0.1) AS IS, treating a
near-zero `D_W` at this level as itself an informative result
(`OPEN_DYNAMICS_NO_EFFECT`, ТЗ §16) rather than as a reason to
re-parameterize. This is a pre-registered choice, made BEFORE running
Milestone 3 and before seeing any Active-arm Gate-A outcome (only the
already-recorded `D_W`/lattice evidence above informed it) — consistent
with ТЗ §9/§31's stop rules. **Consequence for interpreting Milestone 3:**
if the factorial cells show no separation from `C0`, the correct reading
is "γ=0.1 suppresses adaptation enough that openness had no chance to
act," NOT "openness cannot create geometric organization" — those are
different claims, and `[A35]`'s own D_W evidence is why. The user also
chose N=512 for the pilot (per `[A36]`, the only scale where G1 actually
resolves geometric from non-geometric); `configs/open_pilot.yaml`
updated to `sizes: [512]` accordingly (was `[64, 512]`, kept both only
while the scale was undecided).

### A35 addendum (2026-08-14, later same day) — `d_s_hat` confirms `OPEN_DYNAMICS_NO_EFFECT` at the chosen `γ̃=0.05`; `Cσ`-alone shows a real, separate `d_s_hat` shift

**Question this answers:** with Milestone 3's factorial pilot now complete
(N=512, 5 seeds/cell, `results/open_pilot/raw.jsonl`), does the actual
Gate-A geometric observable (`d_s_hat`), not just `D_W`, confirm the
`OPEN_DYNAMICS_NO_EFFECT` reading `[A35]`'s option (c) pre-registered?

**Computed (mean ± SD across 5 seeds, N=512):**

```
C0           (γ=0,   σ=0):    d_s_hat = 5.2226 ± 0.0429   D_W = 0.0107
Cγ           (γ=0.1, σ=0):    d_s_hat = 5.2230 ± 0.0429   D_W = 0.00252
Cσ           (γ=0,   σ=0.05): d_s_hat = 5.1456 ± 0.0550   D_W = 0.5057
Cγσ          (γ=0.1, σ=0.05): d_s_hat = 5.2222 ± 0.0433   D_W = 0.0603
```

**Cohen's d (d_s_hat, vs C0):** `Cγ` ≈ 0.01, `Cγσ` ≈ 0.01 (95% CIs fully
overlapping); `Cσ` ≈ 1.56 (95% CIs `[5.097,5.194]` vs `[5.185,5.260]`,
nearly non-overlapping).

**Reading:** `Cγσ` — the cell Milestone 3 actually runs on Active per
`[A35]`'s resolved choice — shows **no measurable separation on
`d_s_hat`** from closed, despite `D_W` differing 5.6x. This empirically
confirms the concern `[A35]` itself pre-registered: at `γ̃=0.05`,
adaptation is suppressed enough that openness produces no measurable
geometric change. `OPEN_DYNAMICS_NO_EFFECT` (ТЗ §16) is the correct
reading for this cell, not a Gate-A failure of the underlying hypothesis.

**New, not previously computed:** `Cσ` alone (noise, no damping) shows a
real, moderate-large `d_s_hat` REDUCTION vs closed (d≈1.56) — consistent
with `[A35]`'s own already-named H5 (noise-driven homogenization)
concern, now given a number. Direction is a DECREASE in estimated
spectral dimension, not an increase — worth keeping in mind if a future
pilot revisits nonzero `σ` without matching `γ`.

**Caveat, stated plainly, not hidden:** `n=5` seeds is pilot-scale, not
CLAUDE.md's own production standard (`≥20` seeds, `30-50` where budget
allows) for a load-bearing MCID verdict. These Cohen's d values are
indicative of direction and rough magnitude, not a certified G6 gate
result. This is also NOT a full Gate-A arms comparison (Active vs
Frozen/Random/Scrambled) — only the `[A35]` open-dynamics calibration
pilot on Active alone, as designed.

**Evidence:** [VERIFIED] computed directly from
`results/open_pilot/raw.jsonl` (20 rows, 4 cells × 5 seeds, N=512),
read and aggregated in-session — not re-derived from the doc's own prose,
independently pulled from the raw JSONL rows.

**If wrong:** if a future, properly-powered (`≥20`-seed) rerun of `Cγσ`
shows a `d_s_hat` separation this 5-seed pilot missed (Type II error from
small n), this addendum's `OPEN_DYNAMICS_NO_EFFECT` reading should be
revised — not silently, via a new dated addendum citing the rerun.

### A36 — G1's resolving power is N-dependent: cannot distinguish 3D geometry from a random graph at N=64, but cleanly resolves it at N=512 (2026-08-14, Phase 11 ТЗ §13 calibration)

**Question this answers:** ТЗ §13 requires recalibrating `detect_plateau`
on 9 reference curves before trusting G1 in any open-system verdict —
"the detector must pass known geometry and reject obvious false
plateaus." Ran this calibration for real (not assumed) against actual
computed `d_s(t)` for 1D ring, 2D square lattice, 3D cubic lattice, and
an Erdős–Rényi random graph, at both N=64 (this project's cheap pilot
scale) and N=512 (its largest tested size).

**Result at N=64 — a genuine gap, not a detector bug:**

```
1D ring:   converged=True,  d_s_hat=1.10  (target 1)  -- OK
2D square: converged=True,  d_s_hat=2.25  (target 2)  -- OK
3D cubic:  converged=False                            -- FAILS to converge
ER (N=64): converged=False                            -- ALSO fails
```

The 3D cubic lattice's raw `d_s(t)` curve at N=64 is numerically almost
IDENTICAL to an Erdős–Rényi random graph's own curve at the same N and
mean degree (both `[0.243, 0.304, ..., 3.107-3.27 peak, ..., 2.03-2.06]`,
matching to 2-3 significant figures at every `t`). No threshold tuning
of `detect_plateau` can make the lattice "pass" without also making the
random graph "pass" — **the observable itself (G1, heat-kernel spectral
dimension) has not yet separated geometric from non-geometric structure
at N=64.** This is not a calibration failure to fix with better
thresholds; the underlying signal doesn't exist yet at this scale.

**Result at N=512 — the SAME comparison resolves cleanly:**

```
3D cubic (N=512): converged=True,  d_s_hat=3.53, R²=0.75  (target 3, real plateau)
ER (N=512):        converged=False -- d_s(t) still CLIMBING at t=10
                    (2.70 -> 3.49 -> 4.32 -> 5.01 -> 5.27, no peak reached)
```

At N=512, the lattice shows a genuine 3-point plateau (`t≈4.3-10`,
`R²=0.75` — a real fit, not a near-zero-slope coincidence) near its true
dimension, while the random graph shows the same "expander peak still
growing with N, no plateau within range" signature already documented
for Active (`[A30]`) — this time observed directly on a KNOWN non-
geometric control, confirming that signature's interpretation.

**Practical consequence — this reframes every earlier finding in this
file, not silently:** the "expander-not-geometry" conclusion for Active
(`[A30]`, `development-v0`/`development-v1`) rested heavily on pilot-
scale (N≤125) and even the full FSS grid's smaller sizes, where G1 may
not have resolving power AT ALL, independent of whether Active is
geometric or not. **G1 verdicts at N<512 should be treated as
uninformative-by-construction, not merely statistically weak** — this is
stronger than the previously-recorded "below production seed floor"
caveat, and applies even with production-floor seed counts. `[A30]`'s
own N=512 result (`d_s_hat=5.26`, still no plateau, climbing) is
therefore the ONE genuinely informative G1 data point collected so far
across this whole project — and it already showed the expander
signature at the one scale where G1 can actually tell the difference.

**Evidence:** [VERIFIED-pytest] `check_detect_plateau_calibration.py` —
4 tests: 1D/2D convergence near true dimension at N=64, 3D-vs-ER mutual
non-convergence at N=64 (documents the gap, doesn't hide it), 3D-vs-ER
clean resolution at N=512. All green; `detect_plateau`'s thresholds
(`slope_tolerance=0.1`, `range_tolerance=0.3`, `min_d_s_hat=0.5`)
unchanged from `[A30]`/`[A32]` — this calibration exercise did NOT
require retuning them, it revealed an N-dependent property of the
observable itself.

**If wrong:** if a systematic sweep at intermediate N (216, 343, already
in the FSS grid) shows resolving power emerges gradually rather than
this sharply, the "G1 uninformative below N=512" framing should be
softened to a specific N threshold — not resolved here, would need
running this same lattice-vs-ER comparison at every FSS grid size.

### A37 — Milestone 3 factorial pilot on Active (N=512, 5 seeds) run; Milestone 4 mechanistic read of Cσ against H5 (2026-08-14)

**Milestone 3 result (raw, `scripts/run_open_pilot.py --run`, `configs/
open_pilot.yaml`, N=512, `seeds_per_cell=5`, `[A35]` option (c) i.e.
γ̃=0.05 accepted as-is):**

```
cell          d_s_hat (mean±std)   D_W (mean±std)      conductance         modularity
C0            5.223±0.038          0.0107±0.0002        0.562±0.050         0.389±0.004
Cgamma        5.223±0.038          0.0024±0.0002        0.565±0.051         0.389±0.002
Csigma        5.146±0.049          0.5075±0.0094        0.541±0.047         0.422±0.004
Cgammasigma   5.222±0.039          0.0603±0.0008         0.564±0.051         0.390±0.002
```

`converged=False` for all 20 points — same non-converging expander-like
`d_s_hat` signature as closed-system Active at N=512 (`[A30]`). G1 itself
does not separate any cell from any other; `d_s_hat` differences above
have overlapping 95% CIs (`|d|=1.56` for Csigma vs C0, but CI overlap
means MCID's own AND-rule, `docs/estimand.md`, is not met).

`Cgamma` reproduces `[A35]`'s prediction exactly: `D_W` collapses toward
`C0`'s own value (not to zero, but an order of magnitude below `Csigma`'s),
confirming `γ=0.1` suppresses adaptation rather than creating structure —
`OPEN_DYNAMICS_NO_EFFECT` at this γ, as pre-registered, not a new finding.

**Milestone 4 — mechanistic read of `Cσ` against H5 (noise-induced
homogenization, ТЗ §3):** H5 predicts noise WASHES OUT community
structure — conductance should rise (more expander-like, no bottleneck),
modularity should fall, as σ randomizes weights. Tested this directly,
with MCID's own rule (`|Cohen's d| ≥ 0.8` AND non-overlapping 95% CIs,
both required):

```
metric        Cσ vs C0: d      CI overlap    MCID met?
conductance   -0.383           yes           NO — no reliable separation
modularity    +6.874           no            YES — large, reliable increase
```

**`Cσ`'s modularity increase is the OPPOSITE of H5's prediction** — noise
is associated with MORE community structure passing MCID, not less, and
conductance shows no reliable shift at all. Naive H5 (pure homogenization)
is not what's observed.

**No-collapse test before trusting this** (Perelman audit protocol,
`rules/perelman-audit.md`): greedy-modularity detection is known to find
spurious "communities" in random graphs from pure finite-size fluctuations
(Guimerà, Sales-Pardo & Amaral 2004) — a modularity difference could be an
artifact of the metric itself, not a real signal. Computed the floor:
modularity of 10 freshly-generated ER(N=512, 1536 edges) graphs with
**zero dynamics run on them at all**:

```
floor (fresh ER, no dynamics):  mean=0.3852, CI=(0.3818, 0.3886)
C0    (closed dynamics):        mean=0.3890, CI=(0.3830, 0.3949)   d(C0 vs floor)=0.79, CI overlap -> NOT MCID-significant
Csigma (σ̃=0.05):                 mean=0.4216, CI=(0.4157, 0.4274)   d(Cσ vs floor)=7.73, CI non-overlap -> MCID-significant
```

`C0`'s modularity is statistically indistinguishable from the raw
untouched-graph floor (consistent with `[A30]`'s own "closed Active shows
no real geometric organization" finding — closed dynamics doesn't even
clear the random-graph modularity floor). `Csigma`'s modularity clears
that floor by a large, MCID-passing margin. **This is not spurious-
modularity-of-a-random-graph** — the effect survives the negative
control.

**What this does NOT establish (per this project's own scientific
boundary, CLAUDE.md):** not evidence of physical geometry, not evidence
against H5's underlying MECHANISM (noise-driven correlation changes could
still be the cause of the modularity shift — H5 as originally framed
predicted the wrong DIRECTION of the effect, not that noise is causally
irrelevant). The genuinely open question this raises: is the modularity
increase driven by the Hebbian correlation structure itself (a real
signal about how noisy quantum dynamics correlates node pairs), or would
ANY noise-following adaptation rule — regardless of whether it tracks
real dynamical correlations — produce the same shift? That is exactly
what Milestone 5's H0 control (`CorrelationShuffleAdaptation`, `[A31]`)
is designed to answer, and per the ТЗ's own gate ("Milestone 5 only if
Milestone 3-4 show a signal") this modularity finding is that signal —
Milestone 5 proceeds.

**Evidence:** [VERIFIED-pytest/bash] `results/open_pilot/raw.jsonl` (20
points, gitignored, not committed — raw output only); statistics computed
via `statistics/cell_statistics.py::compute_cell_statistics`/`cohens_d`
(reused, not reimplemented) in an ad hoc analysis script, output shown in
this session's transcript, not re-derived as a pytest assertion (this is
a one-off scientific analysis of pilot data, not a regression test).

**If wrong:** if Milestone 5's shuffle-correlation control shows the SAME
modularity increase under `Cσ` with shuffled (non-real) correlations, the
"Hebbian correlation structure" reading above is wrong — the effect would
be a generic property of any noise-following weight update, not evidence
about what the dynamics actually correlates.

**Milestone 5 result (2026-08-14, same day) — the "if wrong" condition
above is exactly what happened.** Ran `scripts/run_milestone5_h0_control.py`:
`CorrelationShuffleAdaptation` (`[A31]`'s H0 control — identical
Oja-normalized update, but the off-diagonal correlation term is shuffled
across existing edges before being applied) at the identical `Cσ` budget
(N=512, K=50, `dtau_steps=50`, `σ̃=0.05`, `γ=0`, same 5 graph seeds):

```
              modularity (mean±CI)              conductance (mean±CI)
H0 (shuffled): 0.4179 (0.4117, 0.4242)            0.5871 (0.5693, 0.6050)
H1 (real):     0.4216 (0.4155, 0.4277)            0.5412 (0.4763, 0.6061)
d(H0 vs H1):   -0.735, CI overlap -> NOT MCID-significant
d(H0 vs H1) conductance: 1.199, CI overlap -> NOT MCID-significant (wide H1 CI)
```

**Kill Analysis (required for this result, `rules/falsification-ladder.md`
Anti-Overfitting Gate — stated explicitly, not left implicit):**

- **What this KILLS:** H1 as originally framed — "`Cσ`'s modularity
  increase reflects the REAL correlation structure the noisy quantum
  dynamics builds, specifically WHICH node pairs correlate." The shuffled
  control, which discards exactly that information while preserving the
  correlation-MAGNITUDE distribution, is statistically indistinguishable
  from the real run on both modularity and conductance. If the real
  correlation structure mattered, shuffling it should have visibly
  degraded whatever structure the real run built — it did not.
- **What this does NOT kill:** `[A37]`'s own negative-control finding
  (`Cσ`'s modularity clears the raw-ER-graph floor, `d=7.73` vs the
  untouched-graph baseline) — that comparison used a DIFFERENT control
  (no dynamics at all vs. dynamics run) and is untouched by this result.
  The modularity SHIFT away from the random-graph floor is real and
  reproducible; what is now shown NOT to be established is that the
  SPECIFIC Hebbian correlation pattern (rather than merely "some
  reinforcement with this magnitude distribution, applied to some
  arbitrary subset of edges") is what causes it.
- **Combined verdict:** the noise-driven weight reinforcement itself
  (structured or not) moves modularity off the random floor — but WHICH
  edges get reinforced does not appear to matter at this budget. This is
  closer to H5's original homogenization framing than `[A37]`'s
  provisional "opposite of H5" reading suggested, though not identical to
  H5 either (H5 predicted LOWER modularity from washing out structure;
  what's observed is a modularity RISE regardless of correlation
  specificity — "any sufficiently strong reinforcement noise raises
  modularity above the random floor" is a third, more precise hypothesis
  neither H1 nor plain H5 stated, and is not itself tested here).

**Evidence:** [VERIFIED-bash] `scripts/run_milestone5_h0_control.py`
output, this session's transcript; script committed for reproducibility.

**If wrong:** a larger seed count or a wider `σ̃` sweep could still reveal
a real-vs-shuffled separation this 5-seed pilot lacked power to detect
(`d=-0.735` is close to the `0.8` MCID threshold, not decisively below
it) — not resolved here, would need a dedicated power analysis before
concluding the null result is final rather than underpowered.

### A38 — Milestone 7's N=1024 grid failed: mean degree 6 is below Erdős–Rényi's connectivity threshold at N=1024, not a random unlucky draw (2026-08-14)

**Question this answers:** why did `scripts/run_open_pilot.py`'s
Milestone 7 run (user-approved: N=512 AND N=1024, `seeds_per_cell=10`)
crash with `NetworkXAlgorithmError` at `size=1024 seed=6` after 64/80
points already completed cleanly?

**Root cause, verified with a prototype before touching code:** `[A7]`'s
mean degree 6 (`n_edges=3*n_nodes`) is fixed across every N this project
uses, for FSS comparability. Erdős–Rényi connectivity requires mean
degree above `ln(N)`. `ln(512)≈6.24 > 6` (mean degree 6 was already
slightly below threshold at N=512 — `[A29]`'s original 20-retry cap
absorbed this) but `ln(1024)≈6.93`, further above 6, so the gap is
worse: expected isolated-vertex count `N·e⁻⁶≈2.5`, and a direct
prototype run (`numpy.random.default_rng(7024)`, the EXACT seed
`run_open_pilot.py` used for `size=1024/seed_index=6` — graph_seed
formula `1000*seed_index+size`) found only 18/200 draws connected
(~9%). With `p≈0.09`, `P(20 consecutive failures)≈0.19` — a real,
expected failure mode at this budget, not bad luck; the first success in
that same 200-draw run only appeared at attempt 24, past the old cap.

**Fix:** raised `_MAX_CONNECTIVITY_RETRY_ATTEMPTS` from 20 to 150
(`graphs/generators.py`) — `P(all 150 fail)≈(0.91)¹⁵⁰≈6e-7`, a safety
margin appropriate for a Full-Ladder run. **Mean degree was NOT
changed** — doing so would break `[A7]`'s fixed-mean-degree-across-N
convention and invalidate exact comparability with the 40 N≤512 points
already computed under the old cap (mean degree is part of what "same
Active topology generator" means across this project's FSS grid).

**Why this is not a parameter-fishing violation:** the retry cap governs
*generation feasibility* (how many draws until a valid population member
is found), not the *scientific* parameter (mean degree) that defines the
population itself — raising it changes nothing about which graphs are
scientifically eligible, only how hard the code tries to find one.

**Evidence:** [VERIFIED-pytest] `tests/unit/check_erdos_renyi_connectivity.py::
test_generate_erdos_renyi_connects_at_n1024_mean_degree_6_despite_low_success_rate`
— reproduces the exact failing seed (not a brute-force search like the
existing N=64 regression test), fails RED against the old cap, passes
GREEN after the fix. 245/245 tests, ruff/mypy clean.

**If wrong:** if N=1024 is not the largest N this project ever uses, the
same threshold-crossing will recur at some larger N with an even lower
per-draw success probability — the retry cap is not scale-free. Not
fixed here (no larger N is in scope yet); a future N large enough to
need more than 150 attempts should trigger revisiting this as a formula
(e.g. attempts scaling with the connectivity gap) rather than another
one-off constant bump.

### A39 — Milestone 7 (extended FSS: N=512 AND N=1024, seeds_per_cell=10) result — the Cσ modularity effect replicates and strengthens with N; G1 still uninformative at both scales (2026-08-14)

**Question this answers:** does `[A37]`'s modularity finding (found at
N=512, 5 seeds) survive more seeds and a larger N, or was it a
finite-size/underpowered artifact? User-approved scope: N=512 AND
N=1024, `seeds_per_cell=10` (80 points total, `configs/open_pilot.yaml`).

**Result (full 80-point grid, `results/open_pilot/raw.jsonl`,
gitignored raw output):**

```
N=512   C0            d_s_hat=5.233±0.042 conv=0/10  D_W=0.0107±0.0002  cond=0.526±0.091  mod=0.387±0.005
N=512   Cgamma        d_s_hat=5.233±0.042 conv=0/10  D_W=0.0025±0.0002  cond=0.549±0.047  mod=0.388±0.003
N=512   Csigma        d_s_hat=5.160±0.052 conv=0/10  D_W=0.5068±0.0107  cond=0.548±0.038  mod=0.421±0.004
N=512   Cgammasigma   d_s_hat=5.233±0.042 conv=0/10  D_W=0.0601±0.0008  cond=0.550±0.045  mod=0.388±0.003
N=1024  C0            d_s_hat=5.832±0.025 conv=0/10  D_W=0.0064±0.0019  cond=0.579±0.023  mod=0.390±0.001
N=1024  Cgamma        d_s_hat=5.832±0.025 conv=0/10  D_W=0.0018±0.0002  cond=0.579±0.023  mod=0.388±0.004
N=1024  Csigma        d_s_hat=5.715±0.036 conv=0/10  D_W=0.5034±0.0078  cond=0.587±0.051  mod=0.427±0.004
N=1024  Cgammasigma   d_s_hat=5.832±0.026 conv=0/10  D_W=0.0597±0.0007  cond=0.580±0.024  mod=0.393±0.005
```

**G1 remains fully uninformative at both scales** — `converged=False`
for all 80 points; the expander-peak signature simply climbs with N
(`d_s_hat`≈5.2 at N=512 → ≈5.8 at N=1024, same direction as `[A30]`'s
closed-system trend), never plateauing. Larger N did not give G1
resolving power for open-system Active.

**`Cσ`'s modularity effect (`[A37]`) replicates AND strengthens** — MCID
check (`|d|≥0.8` AND non-overlapping 95% CI, `docs/estimand.md`):

```
metric        N=512 d(Cσ vs C0)   MCID    N=1024 d(Cσ vs C0)   MCID
modularity    7.658               YES     13.897               YES
conductance   0.308               no      0.190                no
d_s_hat       -1.550              YES     -3.825               YES
```

Re-ran `[A37]`'s negative control at N=1024 too: `C0`'s modularity vs 10
fresh untouched-ER(1024,3072) graphs, `d=-0.29`, CI overlap — same
"closed dynamics doesn't clear the random floor" pattern as N=512. The
effect size growing with N (not shrinking) argues against a finite-size
artifact explanation.

**New wrinkle, not in `[A37]`'s 5-seed data:** with 10 seeds, `d_s_hat`'s
`Cσ` vs `C0` separation now ALSO passes MCID at both N (it did not at 5
seeds — CI overlapped). **This is not a meaningful geometric-dimension
claim** — `converged=False` for every point in the comparison, so
`d_s_hat` is a raw non-plateaued value, not a dimension estimate;
"MCID-significant difference between two uninterpretable numbers" is
noted for completeness, not promoted as a finding.

**What Milestone 7 did NOT do:** re-run Milestone 5's H0
(`CorrelationShuffleAdaptation`) control at the larger seed count/N —
the user's approved scope was the factorial grid only. The correlation-
specificity question `[A37]`'s Milestone 5 left open (`d=-0.735`, CI
overlap at 5 seeds, "if wrong: a larger seed count... could still reveal
a real-vs-shuffled separation") is STILL open — this run added power to
the `Cσ`-vs-`C0` comparison, not to the H0-vs-H1 comparison, which is a
different pair of arms entirely.

**Evidence:** [VERIFIED-bash] `results/open_pilot/raw.jsonl` (80 points);
statistics via `statistics/cell_statistics.py` (reused), ad hoc analysis
script output in this session's transcript.

**If wrong:** a still-larger N, or the H0 control repeated at N=1024/10
seeds, could change either conclusion — not resolved here.

### A40 — Phase 12 Stage 0: the community PARTITION is not a well-defined object on this project's graphs; the detector is sound, the graphs are degenerate (2026-08-14)

**Question this answers:** Phase 12's substrate gate (`docs/
phase12_spec.md` Stage 0) — before comparing partitions between cells,
is the partition itself a stable property of a graph? Every Phase 12
Stage-2 comparison is confounded if it is not.

**Measure used (documented deviation from the spec):** `phase12_spec.md`
named Adjusted Mutual Information; implemented Adjusted Rand Index
(Hubert & Arabie 1985) instead, to avoid adding scikit-learn as a
dependency for one function. Same essential chance-correction property.
`observables/partition_similarity.py`, hand-derived test cases
(the `[0,0,1,1]` vs `[0,1,0,1]` → exactly `-0.5` case pins the
chance-correction term).

**Result — the detector is NOT broken, and the discriminator proves it:**

```
graph type                          Q       ARI after perturbing 1% of edge weights by ±10%
SBM (4 planted communities)         0.615   0.997   <- STABLE
Erdos-Renyi (this project's Active) 0.389   0.132   <- chaotic
periodic cubic lattice N=512        0.583   0.248   <- chaotic
ER, floor (independent graphs)      --      0.000   (measured, 10 pairs)
```

Perturbing only 0.1% of edges gives the same ER result (0.132) — the
instability is not a dose effect, the partition simply is not determined.

`greedy_modularity_communities` recovers planted structure essentially
perfectly when it exists. On near-random graphs it does not, because
there is nothing stable to recover: the classic **degenerate modularity
landscape** (Good, de Montjoye & Clauset 2010) — exponentially many
partitions with near-identical Q, so the argmax is arbitrary.

**Substrate Gate verdict: PASSED, not BLOCKED.** This is important for
correct bookkeeping under FL Step 2a. The apparatus works (proven by the
SBM positive control); what the gate revealed is a property of the
OBJECT, not a defect of the instrument. Therefore this result IS
admissible evidence about the claim — it is not a "test could not run"
outcome.

**Consequence for `phase12_spec.md`:** Stage 2 (2a/2b/2c — "which
communities formed", "do real and shuffled correlations produce the same
communities", "is the partition reproducible across noise") is
**unanswerable as specified**, because the quantity those stages would
measure does not exist as a stable object on ER-like graphs. Not a
failure of the plan — the gate did exactly its job, before compute was
spent on three stages whose output would have been uninterpretable.

**Consequence for `[A37]`/`[A39]`:** the modularity NUMBER stands
(replicated, MCID-passing, effect grows with N). Its *interpretation* as
community organization does not follow, and Q≈0.39 on an ER graph should
never have been read as "communities exist" — `[A37]` already cited
Guimerà et al. 2004 for exactly this hazard and then partially reasoned
past it. The decisive follow-up (weight-shuffle null model) is `[A41]`.

**Evidence:** [VERIFIED-pytest] `tests/unit/check_partition_similarity.py`
(6 tests incl. a permanent determinism regression test);
[VERIFIED-bash] discriminator output in this session's transcript.

**If wrong:** if some other community detector proved stable on these
same ER graphs, the "degenerate landscape" reading would be wrong and
this would instead be a greedy-specific artifact.

**This falsification condition was TESTED the same day, and did not
falsify:** repeated the identical perturbation experiment with
**Louvain** (`nx.algorithms.community.louvain_communities`, a different
algorithm, fixed algorithm seed so its own randomness is not the
variable):

```
detector   ER(512,1536)          SBM (planted communities)
greedy     ARI = 0.132           ARI = 0.997
Louvain    ARI = 0.138           ARI = 1.000
```

Two independent algorithms agree to within 0.006 on the ER graphs and
both recover planted structure essentially perfectly. The degeneracy is
detector-independent — a property of the graphs, as claimed.

### A41 — Phase 12 decisive test: the Cσ modularity increase is ENTIRELY distributional, with zero structural content (2026-08-14)

**Question this answers:** given `[A40]` (the partition is not a stable
object on these graphs), does the `[A37]`/`[A39]` modularity increase
carry ANY structural information at all?

**Method — weight-shuffle null model** (`scripts/run_phase12_weight_
shuffle_null.py`): take each final graph and randomly permute its edge
weights across the existing edges. This destroys every structural
relationship by construction (which weight sits on which edge) while
preserving the exact weight multiset and the topology. Define
`structural excess := Q_real − Q_shuffled`. If Q encodes organization,
the excess must be positive; if Q is a function of the weight
distribution alone, the excess is zero.

This is a strictly stronger control than Milestone 5's H0
(`[A37]`): that one shuffled the correlation term *inside* the update
rule and compared scalar Q between two dynamics runs (yielding an
ambiguous `d=−0.735`); this one shuffles the *final structure itself*
and asks whether the metric can detect the difference at all.

**Result (N=512, 10 seeds, 3 shuffles averaged per point):**

```
structural excess (Q_real − Q_shuffled):
  C0     mean = −0.00005   CI95 = (−0.00477, +0.00466)   contains 0: YES
  Csigma mean = +0.00117   CI95 = (−0.00255, +0.00489)   contains 0: YES

Cohen's d, Csigma vs C0:
  raw Q                 =  7.658    <- [A37]/[A39]'s headline effect
  weight std            = 40.751    <- the distributional change
  STRUCTURAL EXCESS     =  0.207    <- what survives the null model (below MCID 0.8)
```

**Both cells have zero structural excess** — the confidence interval
contains zero for `C0` AND for `Cσ`. The entire, large, MCID-passing,
N-scaling modularity difference between the cells is reproduced by a
null model that has no structure in it by construction.

**Interpretation, stated plainly:** noise (`σ̃=0.05`) makes edge weights
~24× more heterogeneous (`w_std` 0.0046 → 0.105, `d=40.8`). A graph with
heterogeneous weights admits a higher-modularity *arbitrary* partition
than one with near-uniform weights, purely as an accounting property of
Q. That is the whole effect. **No organization, no communities, no
structure — a distributional artifact.**

**What this KILLS (Kill Analysis, required for a negative result):**
- "`Cσ` produces community structure" — dead. Not weakened, dead: the
  effect is fully reproduced with all structure destroyed.
- `[A37]`'s surviving claim ("noise-driven reinforcement moves modularity
  off the random floor") — the *number* still moves, but the phrase
  "moves modularity off the floor" was carrying an implied structural
  reading that is now removed. The honest restatement is: *noise widens
  the weight distribution, and Q is sensitive to weight-distribution
  width on graphs with a degenerate modularity landscape.*
- `[A39]`'s "the effect strengthens with N" — reduces to "weight
  heterogeneity grows with N under noise", no longer independently
  interesting.

**What this does NOT kill:**
- The measurements themselves. Every Q, `D_W`, and effect size recorded
  in `[A37]`/`[A39]` is correct as a number and reproducible; only the
  interpretation collapses.
- Any claim about *geometry* — modularity was never a geometry probe.
  G1's non-convergence (`[A39]`) and the untested curvature route
  (`phase12_spec.md` Stage 3) are untouched by this result.
- The open-system machinery itself, which is validated by T1–T10.

**Evidence:** [VERIFIED-bash] `scripts/run_phase12_weight_shuffle_null.py`
output, 10 seeds, this session's transcript; script committed for
reproducibility. Statistics via `statistics/cell_statistics.py` (reused).

**If wrong:** the null model permutes weights across existing edges only,
so it preserves topology exactly. If the organization were *topological*
rather than weight-borne it would be invisible to this test — but the
Stage-1 arms use `NoTopologyUpdate` (`[A8]`/`[A14]`), so topology cannot
change during a run and there is no topological organization available
to miss. This caveat would matter only for a future arm with an active
`TopologyUpdateRule`.

**CORRECTION, same day, see `[A42]`:** the sentence above ("topology
cannot change during a run") is **not strictly true** and is corrected
here rather than silently edited. The non-negativity clamp can drive an
edge weight to exactly zero, which is an *effective* topology change —
the mask still records the edge but it carries no coupling. Observed
rate is very low (1 edge of 1536, on 1 of 5 seeds, `Cσ` only), so
`[A41]`'s conclusion is unaffected in practice: the weight-shuffle null
preserves the number of zeroed edges (it permutes the multiset, zeros
included), and a single zeroed edge cannot account for a `d=7.7` effect.
But the general claim "no topological organization is available to miss"
is too strong as written and should read "topological change is possible
via weight-zeroing, but is far too rare at this budget to carry the
observed effect."

### A42 — the non-negativity clamp can zero an edge, so `NoTopologyUpdate` does not guarantee constant EFFECTIVE topology (2026-08-14)

**Question this answers:** why did Phase 12's first Stage-3 curvature run
return `nan` for the `Cσ` cell?

**Root cause, found by investigating rather than patching:** Forman-Ricci
divides by `sqrt(w_e · w_neighbor)`. The first run produced
`RuntimeWarning: divide by zero`, so some final weight was exactly 0.0.
Measured directly across 5 seeds × 2 cells:

```
seed  cell     n_zero-weight edges / 1536   w_min
0-2   C0                    0               ~0.93
0-2   Csigma                0               5.2e-2 .. 1.1e-1
3     C0                    0                0.91
3     Csigma                1               0.0      <- the culprit
4     C0                    0                0.93
4     Csigma                0               1.4e-1
```

`HebbianAdaptation`'s `_masked_nonnegative` clamp floors negative weights
at zero. Under noise (`Cσ`), a weight can be pushed below zero and
clamped to exactly 0.0. Rate at this budget: 1 edge in 7680 edge-runs.

**Two consequences, both recorded rather than one silently fixed:**

1. **Numerical (fixed):** `observables/curvature.py` now excludes
   zero-weight edges from the effective graph — as focal edges and as
   incident neighbours — rather than adding an epsilon, which would
   invent a coupling the dynamics had removed. A zero-weight edge carries
   no coupling and is dynamically absent. Regression test:
   `check_curvature.py::test_zero_weight_edges_are_excluded_not_infinite`
   (RED before the fix, GREEN after).
2. **Scientific (open, not fixed):** `[A8]`/`[A14]`'s `NoTopologyUpdate`
   guarantees the *mask* never changes, and this project has repeatedly
   reasoned as if that means the topology is constant. It does not: a
   clamped-to-zero weight is an effective edge deletion. At the observed
   rate this changes no conclusion (see the `[A41]` correction above),
   but the reasoning step "mask fixed ⇒ topology fixed" is invalid in
   general and should not be reused without checking the zero count.

**Why this was worth investigating rather than epsilon-patching:** the
`nan` was a symptom; treating it as a formatting nuisance would have
hidden a real (if small) violation of a structural assumption the
project has relied on in several places.

**Evidence:** [VERIFIED-bash] zero-count measurement across seeds 0-4,
this session's transcript; [VERIFIED-pytest] `check_curvature.py` (6
tests, incl. the lattice positive control at exactly F=-8).

**If wrong:** if a longer run, larger `η`, or stronger `σ̃` raised the
zeroing rate substantially, the "too rare to matter" judgement in the
`[A41]` correction would need revisiting — the rate is budget-dependent
and was measured only at this one budget.

### A43 — Phase 12 Stage 3: Forman-Ricci curvature DOES carry a structural signal that survives the null model — but it is ~0.8% of the geometry scale, with a mundane explanation not yet excluded (2026-08-14)

**Question this answers:** `phase12_spec.md` Stage 3 — G1 never converges
(`[A39]`), so is there geometry-like structure that a plateau-free
observable can see? Forman-Ricci needs no fitting or convergence
criterion. Per `[A41]`'s lesson, the weight-shuffle null model was
applied **from the start**, not retrofitted.

**Result (N=512, 5 seeds, `observables/curvature.py`):**

```
cell     mean F      95% CI              structural excess (F_real - F_shuffled)
C0       -9.9414   (-10.071, -9.812)     +0.00004  CI (+0.00003,+0.00004)  excludes 0
Csigma  -10.0883   (-10.210, -9.967)     +0.01577  CI (+0.00687,+0.02468)  excludes 0

d(Csigma vs C0) on raw mean curvature = -1.449
d(Csigma vs C0) on STRUCTURAL excess  = +3.103   <- passes MCID (|d| >= 0.8)
```

**This is the first Phase 12 signal that survives the weight-shuffle null
model.** Modularity's structural excess was zero in both cells
(`[A41]`); curvature's is nonzero in both, and ~400× larger under `Cσ`
than under `C0`.

**Scale, stated before any interpretation** (the number is meaningless
without it):

```
periodic cubic lattice (real geometry):   F = -8.000  (exact, uniform)
ER C0:                                    F = -9.941
ER Csigma:                                F = -10.088

lattice -> ER gap ("geometry vs random"):        1.941   <- the scale that means something
C0 -> Csigma raw gap:                            0.147   (7.6% of that scale)
   ...of which structural (survives the null):   0.0158  (0.81% of that scale)
```

The structural signal is **~120× smaller than the gap between a lattice
and a random graph**. It is statistically robust and practically tiny.
Curvature moves `Cσ` slightly *further from* the lattice value, not
toward it.

**The mundane explanation, named because it is the leading candidate and
is NOT excluded:** Forman-Ricci contains `1/sqrt(w_e · w_neighbor)`, a
nonlinear function of *pairs* of weights, so its expectation is not
permutation-invariant whenever weights are correlated with position.
`HebbianAdaptation`'s decay term is node-based (`density[i]+density[j]`),
which by construction correlates the weights of all edges sharing a node.
That node-level correlation alone would produce a nonzero structural
excess with no geometric content whatever. **The needed control is a
node-strength-preserving null** (randomize which edges carry which
weights while preserving each node's total strength); if the excess
vanishes under it, the signal is entirely node-level. Not implemented —
this is the single most valuable next step for Phase 12.

**Status therefore: `[HYPOTHESIS]`, not a finding.** A structural signal
exists and is reproducible; whether it reflects anything geometric is
unknown and has a plausible trivial explanation pending test.

**What this does NOT mean:** not evidence of emergent geometry (scale
alone forbids that reading, and the direction is *away* from the lattice
value); not a Gate-A result; not a BILUH claim. The
`docs/falsification_gates.md` grep canary applies unchanged.

**Evidence:** [VERIFIED-bash] Stage 3 rerun output (after the `[A42]`
zero-weight fix), this session's transcript; [VERIFIED-pytest]
`check_curvature.py`, 6 tests including the exact `F=-8` lattice control.

**If wrong:** the first run of this same experiment returned `nan` and
would have been reported as "no signal" had the warning been ignored
(`[A42]`) — a reminder that this result rests on 5 seeds at one budget
and has not been replicated at N=1024 or under a stronger null.

### A44 — `[A43]`'s curvature signal is NOT node-strength heterogeneity: it survives a strength-stratified null (2026-08-14)

**Question this answers:** `[A43]` named node-strength heterogeneity as
the leading mundane explanation for the curvature structural excess and
marked the result `[HYPOTHESIS]` pending exactly this test. Phase 12's
own handoff called it "the single most valuable next step". Run.

**Method** (`scripts/run_phase12_strength_null.py`): bin edges into 20
quantile bins by the product of their endpoints' node strengths, then
permute weights **only within a bin**. This preserves the
weight-position relationship that node strengths induce — which is what
the Hebbian decay term (`density[i]+density[j]`, node-based) creates by
construction — while destroying anything finer.

**Result (N=512, 5 seeds):**

```
cell     global-shuffle excess   strength-stratified excess        retained
C0       +0.00004                +0.00003  CI(+0.00002,+0.00004)   89.9%
Csigma   +0.01577                +0.01074  CI(+0.00823,+0.01326)   68.1%

d(Csigma vs C0) on strength-CONTROLLED excess = 7.473
   ([A43]'s uncontrolled figure was 3.103 — the control REMOVED variance,
    so the separation got cleaner, not weaker)
```

**The signal did not collapse.** Node strengths account for only ~32% of
the `Cσ` excess; ~68% is edge-level structure that survives controlling
for them, with a CI excluding zero. **`[A43]`'s named mundane
explanation is therefore excluded** — this is genuine edge-level
structure, not node-strength heterogeneity.

**But the NEXT mundane explanation is immediately available, and is not
excluded by this test:** `HebbianAdaptation` updates `w_ij` by the
pairwise correlation `C_ij`, so it writes pairwise information into the
weights **by construction**. Any shuffle destroys that pairing,
guaranteeing a nonzero excess for reasons that have nothing to do with
geometry. "Edge-level structure exists" is exactly what a pairwise
update rule produces trivially; it is not evidence that the structure is
geometric. Status therefore stays `[HYPOTHESIS]` — one candidate
explanation was killed, not the class of them.

**Scale unchanged and still decisive against over-reading:** the
strength-controlled excess is 0.0107 against a lattice-to-random gap of
1.941 — **0.55% of the "geometry vs random" scale** — and `Cσ` continues
to move *away* from the lattice value, not toward it.

**Evidence:** [VERIFIED-bash] `scripts/run_phase12_strength_null.py`
output, this session's transcript; script committed for reproducibility.

**If wrong:** 20 quantile bins is a chosen resolution; too-coarse bins
would under-control for strengths and inflate the retained fraction. Not
swept — a bin-count sensitivity check would be the cheap robustness test.

### A45 — DECISIVE: shuffled correlations produce MORE curvature structure than real ones; the effect is anti-correlated with the hypothesis (2026-08-14)

**Question this answers:** `[A44]` excluded node strengths but named the
remaining mundane explanation — `HebbianAdaptation` writes pairwise
information into weights by construction, so "edge-level structure
exists" is trivially guaranteed and says nothing about geometry. The
discriminator is this project's own H0 control
(`CorrelationShuffleAdaptation`, `[A31]`): identical Oja-normalized
update, correlation term shuffled across edges — same magnitude
distribution, wrong pairing.

**Result (N=512, 5 seeds, both at `σ̃=0.05`, `γ=0`,
`scripts/run_phase12_curvature_h0.py`):**

```
excess vs GLOBAL-shuffle null:
  H1 (real correlations)      = +0.01577  CI (+0.00687, +0.02468)
  H0 (shuffled correlations)  = +0.03263  CI (+0.02769, +0.03757)
  d(H1 vs H0) = -2.907   CI overlap: NO   MCID met: YES

excess vs STRENGTH-STRATIFIED null:
  H1 (real correlations)      = +0.01074  CI (+0.00823, +0.01326)
  H0 (shuffled correlations)  = +0.02108  CI (+0.01543, +0.02673)
  d(H1 vs H0) = -2.936   CI overlap: NO   MCID met: YES
```

**The sign is the finding.** Real dynamical correlations produce roughly
**half** the structural excess that randomly shuffled correlations do —
a large, MCID-passing difference in the direction *opposite* to H1. This
is not "no difference" (Milestone 5's ambiguous scalar null,
`[A37]`, `d=-0.735` with CI overlap); it is a clear, reproducible
difference that actively contradicts the hypothesis it was meant to test.

Plausible mechanism (not itself tested): shuffling the correlation term
scatters weight updates incoherently with respect to node-level density,
producing more position-dependent weight variance for Forman-Ricci's
nonlinear `1/sqrt(w_e·w_neighbor)` term to register. Real correlations,
being smoother and partly aligned with node density, produce less. Under
either mechanism the conclusion is the same: **the excess does not track
what the dynamics actually correlates.**

**KILL ANALYSIS.**

*What this kills:* the entire "open-system dynamics organizes the graph
via real dynamical correlations" line, at this budget, across every
observable tried:
- G1 (spectral dimension): never converged, 0/80 points (`[A39]`).
- Modularity: whole effect reproduced by a structure-destroying null,
  structural excess ≡ 0 (`[A41]`).
- Conductance: no MCID-passing separation at any N (`[A39]`).
- Forman-Ricci curvature: excess is real and survives node-strength
  control (`[A44]`), but is *larger under shuffled correlations*, and is
  ~0.5% of the lattice-to-random scale in the direction away from the
  lattice (`[A43]`, this entry).

*What this does NOT kill:*
- Any measurement. Every number in `[A37]`/`[A39]`/`[A43]`/`[A44]`
  stands as recorded; only interpretations collapsed.
- The infrastructure: open/closed backends, T1–T10, seed discipline,
  provenance, the null-model toolkit built here.
- Other adaptation rules. `AntiHebbianAdaptation` and
  `AlternativeObjective` exist and were never run in open-system mode.
- Other `(γ̃,σ̃)` regimes — one point was ever tested, by design
  (`[A35]`).
- Any claim about geometry per se. No observable used here is a
  validated geometry detector on non-converged data; "no geometric
  organization found" is not "geometric organization is impossible".

*Minimal Relaxation options, one assumption each (not pursued here):*
(a) different adaptation rule, same everything else; (b) different
`(γ̃,σ̃)` regime, same rule; (c) a topology-updating arm, since
`NoTopologyUpdate` forbids the one kind of reorganization that could
show up structurally (`[A42]` showed even the accidental zeroing route
is negligible at this budget).

**Evidence:** [VERIFIED-bash] `scripts/run_phase12_curvature_h0.py`
output, this session's transcript; script committed. Both null models
computed on the identical graphs and seeds, so H1/H0 are directly
comparable.

**If wrong:** 5 seeds at one budget, one graph size. The H0/H1 gap is
large (`d≈-2.9`) so underpowering is unlikely to explain it, but the
mechanism claim above is untested speculation and is labelled as such.

### A46 — the adaptation rule NEVER strengthens any weight above baseline: all "movement" is decay (2026-08-14, prompted by a parallel session's unsigned-`D_W` catch)

**Provenance of the question, credited not absorbed:** a parallel working
session running `/claim-decomposer` against its own earlier
interpretation caught that `D_W = ‖W_t−W_0‖_F/‖W_0‖_F`
(`observables/trajectory_divergence.py`) is **unsigned** — a large `D_W`
is equally consistent with weights collapsing toward the
`_masked_nonnegative` clip as with structural organization. It correctly
downgraded its own claim to `[WEAKEN]` and left the direction question
open. `[A42]` had measured only the *exactly-zero* endpoint (1 edge of
1536); the drift direction was never measured. This entry measures it.

**Result (N=512, 3 seeds, initial weight = 1.0 uniform for every edge,
`[A19]`):**

```
cell           D_W      mean_w    w_min    w_max   % of weights below 1.0
C0            0.0107    0.9903    0.9305   0.9974          100.0%
Cgamma        0.0025    0.9996    0.9622   1.0000          100.0%
Csigma        0.5077    0.5032    0.0751   0.8066          100.0%
Cgammasigma   0.0606    0.9403    0.8892   0.9664          100.0%
```

**No weight in any cell ever exceeds its initial value.** `Cσ`'s maximum
weight is 0.807 against a start of 1.0, and its mean has fallen to 0.503.
The concern was not merely valid — it is the whole picture: `Cσ`'s
headline `D_W ≈ 0.51` is a **~50% near-uniform decay**, not organization
of any kind.

**Mechanism (consistent with the implemented rule, `[A3]`):** the
Oja-normalized update is `η·dτ·(correlation − W·(density_i+density_j)/2)`.
With `psi0` localized on a single node (`localized_psi0`), density is
concentrated and both terms are ≈0 for the vast majority of edges — hence
`C0`'s tiny drift. Adding noise spreads amplitude across all nodes, which
switches the **decay** term on globally while the correlation term stays
noise-dominated and near zero on average. Net effect: global decay. `γ`
suppresses the noise that would otherwise drive this, which is why
`Cγ` barely moves and `Cγσ` sits between.

**Why this matters beyond bookkeeping — it unifies the whole REJECT:**
- `[A41]`'s "noise widens the weight distribution ~24×" is more
  precisely *noise drives a large downward drift with spread*, and a
  broader weight distribution mechanically raises achievable modularity
  on a degenerate landscape. Same conclusion, now with a mechanism.
- `[A45]`'s reversal (shuffled correlations beat real ones) is
  unsurprising once the correlation term is known to be nearly inert
  relative to the decay term: shuffling a term that contributes little
  cannot hurt, and adds incoherent variance the curvature statistic
  registers.
- **Organization was never mechanically available at this budget.** A
  rule that cannot strengthen anything above baseline cannot produce
  differential reinforcement, which is what "organization" would require.

**Consequence for the Relaxation Map (`null_results/20260814-open-system-
geometrogenesis.md`): V1 (different adaptation rule) now has genuine
independent motivation and satisfies AOG-5.** The reason to change the
rule is no longer "the hypothesis failed, try something else" (motivated
relaxation) but "the implemented rule is measured to be net-decaying at
this budget, so it could not have produced the effect under test". That
is an independent mechanical fact about the apparatus, established
without reference to whether the hypothesis is true.

**Evidence:** [VERIFIED-bash] direct measurement across 3 seeds × 4
cells, this session's transcript. Cross-checks `[A42]`'s zero-count
measurement (consistent: near-zero weights are approached but almost
never reached).

**If wrong:** measured at one `(K, dt, dtau_steps, η)` budget and one
initial condition (localized `psi0`). A delocalized initial state would
activate the correlation term far more broadly and could change the
balance entirely — untested, and arguably the cheapest V1-adjacent probe
available.

### A47 — THEOREM: `W = 1` is an absorbing upper barrier for the implemented rule; `[A46]` is structural, not budget-dependent (2026-08-14)

**What this establishes:** `[A46]` measured that no weight ever exceeds
its initial value and read that as a property of the tested budget. It
is not. It follows from the rule's algebra and holds unconditionally.

**Proof.** The implemented update (`adaptive.py`, `[A3]`) is

```
Δ_ij = η·dτ·( C_ij − W_ij·(ρ_i + ρ_j)/2 ),    ρ = diag(C)
```

where `C_ij = ⟨Re(ψ_i* ψ_j)⟩_t` and `ρ_i = ⟨|ψ_i|²⟩_t`. Then:

1. `Re(ψ_i* ψ_j) ≤ |ψ_i||ψ_j|` pointwise, and time-averaging with
   Cauchy–Schwarz gives `C_ij ≤ √(ρ_i ρ_j)`.
2. AM–GM gives `√(ρ_i ρ_j) ≤ (ρ_i + ρ_j)/2`.
3. Hence `Δ_ij ≤ η·dτ·(ρ_i + ρ_j)/2 · (1 − W_ij)`.
4. So `W_ij ≥ 1 ⟹ Δ_ij ≤ 0`.

Every edge starts at exactly `W = 1.0` (`[A19]`). **Therefore no weight
can ever exceed 1.0 — for any initial state, any noise realization, any
`(η, dτ, K, dtau_steps)`, any number of adaptation windows.**

**Numerically verified** (the inequality, not just its consequence):
`max(C_ij − (ρ_i+ρ_j)/2) = +0.000e+00` across three qualitatively
different initial states (localized, uniform delocalized, random-phase
delocalized). Zero rather than negative because the diagonal attains
equality exactly (`C_ii = ρ_i`). Observed maximum final weights across
the four cells: 0.998 / 0.99999 / 0.783 / 0.967 — the barrier is never
crossed.

**The rule's fixed point is structured, though:** `Δ_ij = 0` at
`W*_ij = 2·C_ij / (ρ_i + ρ_j) ∈ [0, 1]` — the *normalized correlation*
of the edge's endpoints. The dynamics is a contraction from the uniform
initial condition **downward** toward `W*`. Organization is therefore
possible in principle, but only ever as **differential decay**, never as
differential growth.

**This explains every cell without further assumptions:**
- `Cσ`: noise decorrelates, so `C_ij → 0` off-diagonal ⇒ `W* → 0` ⇒
  monotone decay (measured mean weight 0.503 and still falling).
- `C0`: `psi0` is localized, so `ρ ≈ 0` on most of the graph ⇒ BOTH
  terms vanish ⇒ weights stay pinned near 1.0 (`D_W = 0.011`).
- `Cγ`: damping suppresses the spreading that would activate either
  term ⇒ least movement of all (`D_W = 0.0025`).

**CORRECTION to `[A46]` — recorded, not silently edited.** `[A46]`
justified variant V1b (delocalized initial state) on the grounds that
"the rule is net-decaying at this budget". That justification is
**wrong**: net-decay is a theorem and no change of initial state can
lift the ceiling. The correct justification for V1b is different and
sharper: **a localized `psi0` leaves the correlation term inert across
most of the graph, so the rule's own structured fixed point `W*` was
never approached anywhere except near the source.** A delocalized state
*without* noise makes `ρ_i > 0` everywhere while keeping `C_ij`
coherent, which is the one regime in which `W*` carries real structure
and the rule could actually differentiate edges. That regime has never
been run.

**What this does NOT license:** `W*` being structured is not evidence
that it is *geometric*. It is the normalized correlation of a quantum
walk on a random graph; whether that has any geometric content is
exactly the open question, and every observable and null model built in
Phase 12 remains required to answer it.

**Evidence:** [VERIFIED-bash] inequality checked directly on three
initial states; maximum-weight consequence checked on all four cells,
this session's transcript. [DERIVED] the proof above is algebra over
the implemented expression, not an empirical generalization.

**If wrong:** the proof assumes `C` is a genuine time-averaged
correlation matrix with `ρ = diag(C)` and that weights start at 1.0. A
future rule with an additive source term, a different normalization, or
non-uniform initial weights (`[A19]` changed) would break step 3 and the
barrier with it — which is precisely what variant V1 would explore.

### A48 — cheapest differentiating test for V1b: `W*`'s edge-to-edge spread is measured directly (no adaptation run needed), and picks random-phase delocalization over uniform delocalization (2026-08-14)

**Motivation:** `[A47]` named the untested regime for V1b as "delocalized
initial state without noise" but did not distinguish between candidate
delocalizations. `W* = C_ij / [(ρ_i+ρ_j)/2]` can be computed from a
single closed trajectory — no adaptation loop, no seeds beyond the
trajectory's own randomness — making "how much does `W*` actually vary
across edges" the cheapest possible differentiating test (`~/.claude/
rules/falsification-ladder.md`'s CDT protocol) before committing to a
real V1b run.

**A computational bug was found and fixed before any number below was
trusted, recorded per this project's practice of investigating rather
than silently patching.** An exploratory script computed
`W* = 2·C_ij / [(ρ_i+ρ_j)/2]` — carrying the `/2` from `denom`'s own
definition AND a spurious literal `2×`, doubling the true value. This
produced apparent violations of `[A47]`'s own bound (`|W*|` up to 1.9999,
1534/1536 edges "violating" `|W*|≤1`) that looked like a refutation of
the just-established theorem. Diagnosis (checking the diagonal, which
must equal exactly 1.0 at the true fixed point, and finding it computed
as 2.0) isolated the error to this one exploratory script. **`[A47]`'s
own theorem verification is unaffected** — it compared `C_ij` directly
against `(ρ_i+ρ_j)/2` (no division, no factor-of-2 opportunity) and
remains correct as recorded. This is a reminder that a numeric
"falsification" of an algebraic proof is far more likely to be a
computation bug than a wrong proof, and should be diagnosed as such
before it is allowed to overturn a derivation checked by hand.

**Result, corrected formula, 3 independent graphs (N=512):**

```
regime                      W* mean (range across seeds)   W* std (range across seeds)
localized (current, [A19])  +0.26 (+0.25 .. +0.27)          0.41 (0.40 .. 0.41)
uniform delocalized         +0.95 (+0.94 .. +0.95)          0.07 (0.07 .. 0.07)
random-phase delocalized    +0.00 (-0.01 .. +0.01)          0.53 (0.52 .. 0.54)
```

**Uniform delocalization is a worse V1b candidate than the status quo,
not a better one.** Its `W*` is tightly clustered just under the ceiling
(mean 0.946, std 0.07) — nearly every edge gets pulled to nearly the same
value, which is LESS edge-to-edge differentiation than the currently-used
localized state already has (std 0.40). A rule contracting toward a
nearly-constant target cannot produce structure; it can only produce a
second, milder version of `[A46]`/`[A47]`'s uniform decay.

**Random-phase delocalization is the better candidate**: `W*` centers
near zero with the largest spread of the three (std ≈ 0.53, both signs
represented) — genuine edge-to-edge differentiation is available for the
rule to contract toward, unlike either of the other two regimes.

**V1b is revised accordingly**: the untested regime worth running is
random-phase delocalized `psi0`, `γ=σ=0`, not an arbitrary "delocalized"
state. This is still one assumption changed from the baseline (initial
state), consistent with the Relaxation Map.

**What this does NOT establish:** a larger `W*` spread is a necessary
condition for the rule to have something to differentiate, not a
sufficient one for that differentiation to be geometric — `[A44]`/`[A45]`
already showed that edge-level structure existing (curvature) does not
imply it tracks real correlations. The same null-model discipline
(global shuffle, strength-stratified shuffle, H0 correlation-shuffle
control) applies to any V1b run exactly as it did to the original.

**Evidence:** [VERIFIED-bash] `W*` computed directly via
`_time_averaged_correlation`/`evolve_trajectory` (both reused, no new
code), 3 graph seeds, this session's transcript.

**If wrong:** `W*`'s spread is a property of ONE closed trajectory at
K=50 steps; a full adaptive run has `dtau_steps=50` such windows with the
graph itself updating between them, so the actual trajectory of `W`
toward `W*` across many windows could behave differently from this
single-window snapshot. This is a screening heuristic for which regime
to run, not a substitute for actually running it.

### A49 — V1b ran: zero structural excess, contradicting `[A48]`'s screening prediction (2026-08-14)

**Question this answers:** `[A48]` predicted random-phase delocalized
`psi0` was the best-motivated V1b candidate because its single-window
`W*` has the most edge-to-edge spread (std≈0.53) of any regime screened.
Does that prediction survive an actual `dtau_steps=50`-window adaptive
run?

**Method:** `scripts/run_v1b_random_phase.py`. Identical budget to every
other experiment in this project (N=512, K=50, `dtau_steps=50`, `η=0.1`,
`HebbianAdaptation`, `ClosedUnitaryBackend`, `γ=σ=0`) — the ONLY changed
assumption is `psi0`: random-phase delocalized instead of localized
(`[A19]`/`localized_psi0`). 5 seeds. Same structural-excess discipline as
`[A41]`/`[A44]` (global weight-shuffle null and strength-stratified
null).

**Result:**

```
seed   F_real    exc_global   exc_strat
0      -10.0534   +0.00000     +0.00000
1       -9.9622   +0.00000     +0.00000
2       -9.8620   +0.00000     +0.00000
3       -9.8073   +0.00000     +0.00000
4      -10.0221   +0.00001     +0.00000

global-shuffle excess  = +0.00000  CI (+0.00000, +0.00001)
strength-strat excess  = +0.00000  CI (+0.00000, +0.00000)
```

**Zero structural excess** — at the numerical-noise floor, essentially
identical to the localized-`psi0` `C0` baseline's own near-zero excess
(`[A43]`: `+0.00004`/`+0.00003`). Mean curvature (`F_real ≈ -9.94`
averaged) is also statistically indistinguishable from localized `C0`'s
own `-9.9414` (`[A43]`).

**`[A48]`'s screening heuristic did NOT predict this.** Single-window
`W*` spread (std≈0.53 for this regime, vs 0.41 for localized) suggested
more differentiation potential than the status quo — the opposite of
what the full multi-window run shows. **Named mechanism (not further
tested here):** `W*` is computed from ONE closed window at the ORIGINAL
graph. Once adaptation begins, the graph's weights update between all
50 windows and `psi`'s density redistributes under the *evolving*
Laplacian each window — a single-window snapshot of the target a
50-window contraction is heading toward is not obviously representative
of where 50 iterated contractions on a moving target actually end up.
`[A48]`'s own "If wrong" clause anticipated exactly this gap and is
confirmed, not merely hypothetically true.

**Kill Analysis:**
- *What this kills:* V1b, as a route to structural organization, for
  `HebbianAdaptation` at this budget. The independently-motivated
  rationale (`[A47]`'s theorem plus `[A48]`'s screening) does not
  translate into an actual signal.
- *What this does NOT kill:* `[A47]`'s theorem itself (unaffected — it
  is proven algebra, not contingent on this result). `[A48]`'s W* spread
  measurements (correct as computed; their PREDICTIVE VALUE for
  multi-window outcomes is what failed, not their arithmetic). V1
  (a genuinely different adaptation rule) and V3 (active topology
  updates) remain untested and are unaffected by this result.
- *Methodological lesson, worth keeping:* a cheapest-differentiating-test
  screening heuristic computed on a static/single-step proxy can fail to
  predict a multi-step dynamical outcome. Future screening heuristics in
  this project should be validated against at least a short real run
  before being trusted to rank candidates, not just checked for internal
  consistency as `[A48]` was.

**Evidence:** [VERIFIED-bash] `scripts/run_v1b_random_phase.py` output,
this session's transcript; script committed for reproducibility.

**If wrong:** 5 seeds, one budget, one graph size (N=512). A larger
`dtau_steps` might let the multi-window dynamics eventually reflect more
of the single-window `W*` structure `[A48]` measured — not tested; would
be a new, separately-motivated variant, not a re-run of this one.

### A50 — V1 ran (`AlternativeObjective`): zero structural excess, same null pattern as every prior rule/regime (2026-08-14)

**Question this answers:** does a mechanistically OPPOSITE adaptation
rule — pure density-driven growth, no decay term, no correlation/phase
information at all — produce organization where correlation-driven
`HebbianAdaptation` did not?

**Rule choice, stated not silent:** two alternative rules already exist
in the codebase. `AntiHebbianAdaptation`'s own docstring already
documents it as "decay toward the non-negativity floor... a different,
already-bounded pathology" — running it would reproduce a
pre-characterized decay pathology, not test anything new, so it was
skipped. `AlternativeObjective` (`[A4]`) was run instead:
`dW_ij/dτ = η·(ρ_i+ρ_j)/2`. `_masked_nonnegative` only floors at zero —
there is no ceiling analogous to `[A47]`'s theorem, so this rule can in
principle differentiate edges by GROWTH, the one direction Hebbian's
rule structurally cannot reach. Sanity-checked first for numerical
safety: 50 windows produce finite, modest growth (mean 1.0098×, max
1.08× of the uniform 1.0 start) — no blowup.

**Method:** `scripts/run_v1_alternative_objective.py`. Same discipline
as `[A41]`/`[A44]`/`[A49]`: N=512, closed dynamics, localized `psi0`
(baseline-comparable), 5 seeds, curvature structural excess under both
null models.

**Result:**

```
global-shuffle excess  = +0.00003  CI (+0.00003, +0.00004)
strength-strat excess  = +0.00003  CI (+0.00002, +0.00004)

Reference, HebbianAdaptation C0: global +0.00004, strat +0.00003
```

**Numerically indistinguishable from the Hebbian `C0` baseline's own
noise-floor excess.** Despite being mechanistically opposite (pure
growth vs. decay-toward-a-ceiling), `AlternativeObjective` produces the
same absence of structure. Combined with `[A49]` (V1b, zero excess) and
`[A45]` (Hebbian under noise, negative excess relative to shuffled), this
is now the THIRD independently-motivated variant to show no organization.

**Kill Analysis:**
- *What this kills:* V1 as tested. Neither of the two alternative rules
  already implemented in this codebase produces structure at this
  budget — the absence of organization is not an artifact specific to
  `HebbianAdaptation`'s particular algebra.
- *What this does NOT kill:* a genuinely novel rule with additive
  sourcing or non-uniform initial weights (outside `[A19]`'s current
  scope, would require a dated contract addendum) is untested. Rules
  that ignore density/correlation entirely and instead reinforce by some
  other signal (e.g. degree, betweenness) are untested and outside this
  project's current rule family.
- *Standing of the Relaxation Map:* V1 and V1b are now BOTH tested and
  closed. Of the original three branches, **only V3 (active topology
  updates) remains untested** — and it is qualitatively different from
  V1/V1b: it requires a `TopologyUpdateRule`, which is currently
  forbidden almost everywhere in this project (`NoTopologyUpdate`,
  `[A8]`/`[A14]`) and would need a dated contract addendum to
  `mathematical_contract.md`, not just a new script.

**Evidence:** [VERIFIED-bash] `scripts/run_v1_alternative_objective.py`
output, this session's transcript; script committed for reproducibility.

**If wrong:** 5 seeds, one budget, one graph size, one initial state
(localized). `AlternativeObjective` combined with a delocalized `psi0`
(the `[A48]`/`[A49]` regime) was not tried — a 2-assumption combination,
correctly out of scope for a single Minimal-Relaxation variant.

### A51 — V3 ran (`PruneZeroWeightTopologyUpdate`): the rule barely fires at this budget — inconclusive, NOT a decisive closure (2026-08-14)

**Question this answers:** does letting the topology actually change
where `HebbianAdaptation`'s clamp zeroes a weight produce structure the
fixed-topology arms did not? The last open branch of the Relaxation Map.

**Method:** `scripts/run_v3_topology_pilot.py`, using the V3 pilot
infrastructure (`experiment/v3_topology_pilot.py`,
`dynamics/topology.py::PruneZeroWeightTopologyUpdate`, both new this
session, contract addendum in `mathematical_contract.md` §3.3). Single
assumption changed from the already-established `Cσ` regime
(`σ̃=0.05`, `γ=0`, N=512, 5 seeds, `HebbianAdaptation`, localized
`psi0` — exactly `[A43]`/`[A44]`'s configuration): the topology rule is
`PruneZeroWeightTopologyUpdate` instead of `NoTopologyUpdate`. `Cσ`
was chosen over `C0` because `[A46]` showed `Cσ`'s weights actually
approach the floor (mean 0.503) while `C0`'s barely move (mean 0.990).

**Result:**

```
seed  n_edges_before  n_edges_after  n_pruned
0     1536            1536           0
1     1536            1536           0
2     1536            1536           0
3     1536            1535           1
4     1536            1536           0

Total pruned: 1 / 7680 edge-runs (0.013%)

global-shuffle excess  = +0.01763  CI (+0.00958, +0.02568)
strength-strat excess  = +0.01013  CI (+0.00918, +0.01109)

Reference, Csigma WITHOUT pruning ([A43]/[A44]):
  global +0.01577, strat +0.01074
```

**The rule fired essentially once across 7680 edge-run opportunities.**
The structural-excess numbers with pruning active are statistically
indistinguishable from the no-pruning `Cσ` baseline — unsurprising,
since a rule that almost never activates cannot be expected to change
the outcome. This is the correct and only honest reading.

**This is NOT a decisive closure of V3, unlike `[A49]`/`[A50]`'s closure
of V1/V1b — stated explicitly to avoid over-claiming:**

- `[A49]` and `[A50]` tested mechanisms that WERE substantially
  exercised (large `W*` spread, real weight movement) and still produced
  no structure — a meaningful negative result.
- `[A51]` tested a mechanism that was barely exercised at all. "No
  effect from a rule that almost never fires" is expected regardless of
  whether active topology change would matter in principle — the test
  was underpowered by construction, not a demonstration that topology
  updates don't help.

**Kill Analysis, calibrated to this distinction:**
- *What this kills:* `PruneZeroWeightTopologyUpdate` specifically, at
  this exact budget, as a way to test V3 — it does not trigger often
  enough to be informative here.
- *What this does NOT kill:* V3 as a general direction. A more
  aggressive topology rule (e.g. pruning below a small positive
  threshold rather than requiring exact zero, or a longer `dtau_steps`
  budget giving more zeroing opportunities) remains untested and would
  be a genuinely different, separately-motivated variant — not a repeat
  of this one, per the Minimal Relaxation Rule (changing the threshold
  or budget is itself a new single-assumption change from THIS variant).

**Evidence:** [VERIFIED-bash] `scripts/run_v3_topology_pilot.py` output,
this session's transcript; script and rule committed for reproducibility.

**If wrong:** a threshold-based prune rule (e.g. `W_ij < 0.01`, not only
`W_ij == 0`) would fire far more often at this same budget and could
show a genuinely different result — this is the natural next variant,
not tested here to keep this entry's single-assumption discipline clean.

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
