# Boyko Benchmark — Claude Code Development Protocol

## Project Mission

Build a reproducible falsification-first computational benchmark for
testing whether adaptive weighted-network dynamics can generate a stable
low-dimensional local geometric-phase candidate without explicit coordinate
information or hidden target geometry.

The project does not attempt to prove that the Universe is a neural
network.

The project tests a narrower scientific claim:

A specific adaptive network rule may generate geometric observables that
survive finite-size scaling and are absent in parameter-matched
non-adaptive and scrambled controls.

**Provenance note (read before touching anything under `docs/`):** this
project is built from `../ТЗ.txt` alone. The document it references as the
primary specification — `boyko-minimal-experiment-v1.0.md` — does not exist
on this machine (confirmed by full-disk search, 2026-08-11) and the user
has confirmed it is not available. Every place `ТЗ.txt` left an ambiguity
that `v1.0` presumably resolved, `docs/assumptions.md` records the default
chosen and why. If `v1.0` ever surfaces, re-run the Resolution Protocol at
the bottom of `docs/assumptions.md` before trusting anything here as final.

## Phase 0 Artifacts (frozen scientific contract — read in this order)

```
docs/assumptions.md          — every unresolved ambiguity + chosen default + why
docs/novelty_check.md        — prior-art scan (FL Step -3), what novelty is/isn't licensed
docs/mathematical_contract.md — frozen formulas: graph primitives, dynamics, observables
docs/estimand.md             — EstimandOps L1: population/intervention/comparator/MCID/ICE
docs/falsification_gates.md  — Gate A criteria G1-G6, verdict machine, terminology lock
```

Do not implement simulation code before internalizing these five documents.
They are the contract; code that contradicts them is wrong by definition
until the contract itself is revised through a dated addendum — never
silently.

## Scientific Boundary

Never claim:

- physical spacetime emerged;
- Lorentz invariance was proven;
- a Lieb-Robinson theorem was proven;
- quantum gravity was reproduced;
- the Boyko Informational Reality Hypothesis (BILUH) was confirmed;

unless a later specification explicitly defines and verifies those claims.
See `docs/falsification_gates.md` for the machine-checkable grep canary
that enforces this.

The strongest allowed Stage-1 verdict is:

`SURVIVES_GEOMETRIC_PHASE_SCREEN`

or:

`FAILS_GEOMETRIC_PHASE_SCREEN`

## Terminology

Until a formal intrinsic objective functional is defined and mathematically
connected to the update rule (`docs/assumptions.md` A3 — this has NOT been
done here; the implemented rule is a heuristic correlation rule, not proven
gradient descent on anything), use:

`adaptive Hebbian meta-dynamics`

instead of:

`learning` or `self-learning Universe`.

## Development Method

Use strict vertical Test-Driven Development.

For every behavior:

1. Write exactly one failing test.
2. Run the test and show the failing output.
3. Write the minimum implementation required to pass that test.
4. Run the test and show passing output.
5. Refactor only after the test passes.
6. Run the complete relevant test suite after refactoring.
7. Never change an assertion merely to make implementation pass.

Never implement several scientific behaviors before tests exist.

**Builder Blindness:** when a task is split into "implement X" vs. "write
falsifying tests for X," the implementer's prompt gets the specification
(this file + the Phase-0 docs) but not the specific falsification test
cases the reviewer/tester will use — a builder who has seen the exam
answers writes to the exam, not to the spec.

## Anti-Cheating Rules

Never:

- delete a failing test to obtain green status;
- weaken numerical tolerances without documented physical or numerical
  justification (document it in the test itself, not just in a commit
  message);
- modify expected scientific values after seeing output unless the
  specification itself (a Phase-0 doc) was demonstrated to be wrong via a
  dated addendum;
- insert target dimension, lattice coordinates, preferred geometry, or
  expected spectral dimension into the adaptive objective (`docs/
  mathematical_contract.md` §3 — this is exactly what `[A7]`'s
  Erdős–Rényi-over-random-geometric-graph choice exists to prevent
  structurally, not just by convention);
- generate illustrative synthetic results and present them as simulation
  output;
- claim a command was executed unless its actual output exists in the
  session transcript;
- claim convergence based on one seed;
- treat time points within one run as independent experimental replicates
  (`docs/estimand.md` — Independence rule, §7 of the contract).

## Mathematical Contract (summary — `docs/mathematical_contract.md` is authoritative)

Baseline closed-system fast dynamics:

```
i dψ/dt = H(W) ψ,   H(W) := L_norm(W) = I - D^{-1/2} W D^{-1/2}
```

the **normalized** graph Laplacian, chosen so the same operator serves both
the unitary walk generator and every geometric observable (`[A1]`).

Adaptive dynamics is a separate `AdaptationRule` interface implementing an
Oja-normalized Hebbian correlation rule (`[A3]`, revised 2026-08-11 after
DDD skeptic review found the original unconstrained-growth form had no
depression term) — explicitly not proven to be gradient descent on any
objective.

**Mandatory diagnostic:** every Gate-A run also recomputes G1/G2/G4 under
the *combinatorial* Laplacian `L = D − W` in parallel with `L_norm`, to
catch the case where a "geometric" signature is actually a feedback
artifact of using one operator for both dynamics and measurement
(`mathematical_contract.md` §5.6, `[SUSPECT-OPERATOR-ARTIFACT]` flag).

Graph topology (sparsity mask `M`) and edge weights (`W`) are separate
objects. Weights may change only through an `AdaptationRule`. Edges may
appear or disappear only through an explicit `TopologyUpdateRule`; the
Stage-1 default for every arm except Topology Scrambled's one-shot rewire
is `NoTopologyUpdate` (`[A8]`, `[A14]`). Noise must not silently create
previously absent edges — enforced as a hard invariant, not a convention.

## Required Experimental Arms

Implement seven arms (`docs/mathematical_contract.md` §4; the 7th was
added 2026-08-11 at the user's request, see `.claude/memory/decisions.md`):

1. **Active** — same initialization as Frozen and Alternative Objective;
   fast dynamics on; `HebbianAdaptation` on; `NoTopologyUpdate`.
2. **Frozen** — identical initial graph, weights, state, seed stream;
   `NoAdaptation`.
3. **Parameter-Matched Random** — Erdős–Rényi, mean degree matched to
   Active's initial graph (`[A7]`); no correlation-driven topology.
4. **Topology Scrambled** — derived from Active's *final* topology
   (`[A8]`), degree sequence preserved, one-shot rewire.
5. **Fixed Flat Geometry** — periodic regular lattice; positive geometric
   calibration only, never an optimization target.
6. **Alternative Objective** — same initialization and adaptation budget as
   Active; different adaptation rule (`[A4]`); tests whether results are
   specific to the chosen rule, not a Gate-A negative control.
7. **Classical Diffusion Control (Arm CD)** — same shared graph/weights as
   Active; classical dissipative diffusion carrier (`dp/dt = -L p`, the
   *combinatorial* Laplacian — `L_norm` cannot support a conserved
   diffusion on an irregular graph, `[A18]`) instead of the unitary
   Schrödinger carrier; `ClassicalHebbianAdaptation` (`[A18]`), same
   adaptation budget as Active. Tests whether the geometric signature is
   specific to the quantum carrier or arises under any Laplacian-driven
   adaptive rule — not a Gate-A negative control, directly answers
   `docs/novelty_check.md` finding d2. **Do not compare directly against
   Active** — the operator differs too (`L` vs `L_norm`); compare against
   the Operator-Independence Diagnostic's `L`-driven quantum rerun instead
   (`docs/mathematical_contract.md` §2.2, §5.6).

Also required: a mandatory **Operator-Independence Diagnostic** for Active
— a full second dynamics trajectory using the combinatorial Laplacian `L`
in place of `L_norm` as the fast-dynamics generator (`docs/mathematical_
contract.md` §5.6). This is apparatus-trust infrastructure, not an 8th
scientific arm.

## Required Observables

Implement and test (`docs/mathematical_contract.md` §5):

- heat-kernel spectral dimension;
- normalized Laplacian gap;
- effective-resistance diameter/mean resistance (G3 revised 2026-08-11 —
  hop-count diameter alone is identical across arms under fixed topology
  and cannot gate anything);
- low-mode inverse participation ratio;
- average shortest-path length;
- operational finite-propagation front (multi-source-averaged, `[A17]`);
- finite-size scaling exponents (`γ, η, δ` — all estimated, none
  hard-coded);
- confidence intervals;
- effect sizes (Cohen's d).

## Spectral Dimension

```
P_return(t) = Tr(exp(-t L_norm)) / N
d_s(t) = -2 d ln P_return(t) / d ln t
```

For large matrices, use a reproducible stochastic trace estimator
(`[A13]`). Do not treat `I - L_norm` as a standard random-walk transition
matrix.

## Propagation Front

Operational diagnostic only — never proof of a Lieb-Robinson bound.
`r_q(t)` = graph-distance radius (hop count on the fixed initial topology,
`[A15]`) containing a configured fraction `q` (default 0.9) of total
probability. Fit the unsaturated regime to `r_q(t) = v_eff·t + b`. Record
`v_eff`, 95% CI, fit `R²`, fit window, saturation radius.

## Finite-Size Scaling

Never infer a geometric phase from one network size. Every scientific
result spans multiple `N` and multiple independent seeds.

Development: `N ∈ {64, 125, 216, 343, 512}`.

Production: `≥ 5` distinct sizes, `≥ 20` independent seeds per arm/size
(`30–50` where budget allows).

## Statistical Requirements & MCID

For every metric: raw per-seed samples, mean, standard deviation, median,
95% CI, effect size. Comparisons across independent runs only — never
across time points within one run.

**MCID (fixed in `docs/estimand.md`, do not revise after seeing results):**
`|Cohen's d| ≥ 0.8` **and** non-overlapping 95% CIs, both required, between
Active and each negative-control arm (Frozen, Random, Scrambled), on each
Gate-A observable.

## Reproducibility

Every run persists: complete configuration, master seed, derived seeds
(`SeedSequence.spawn`, `[A11]`), Git commit hash, Python/NumPy/SciPy/
NetworkX versions, OS metadata, raw measurements, aggregate measurements,
statistical results, generated figures, final phase verdict.

## Scientific Gates

Stage 1 tests only a geometric-phase candidate. G1–G5 (`docs/
falsification_gates.md`) must all pass — finite-size stability, gap
closure, non-expander resistance-distance growth (G3 revised 2026-08-11 to
use effective resistance, not hop-count, after skeptic review found
hop-count identical-by-construction across arms under fixed topology),
low-mode delocalization, finite propagation. G6 (MCID-level separation
from negative controls) is now **tiered**, not a flat pass/fail: 15/15
cells → `SURVIVES_GEOMETRIC_PHASE_SCREEN`, ≥10/15 → `SURVIVES_GEOMETRIC_
PHASE_SCREEN_PARTIAL`, below that → `FAILS_GEOMETRIC_PHASE_SCREEN`. The
`_PARTIAL` suffix is a genuine reportable outcome and must never be
silently dropped. Passing Stage 1 (at either SURVIVES tier) does not
establish physical spacetime — Gate B is explicitly out of scope.

Before trusting any verdict, `phase_gates.py` itself must pass its own
Oracle Adequacy check (positive/negative synthetic control inputs) — see
`docs/falsification_gates.md`.

## Test Quality

Required commands before declaring a milestone complete:

```bash
pytest tests/ -v --tb=short
ruff check src/ tests/
mypy src/ --strict
pytest tests/ --cov=src/boyko_benchmark --cov-report=term-missing --cov-fail-under=90
```

Mutation testing targets critical scientific modules, minimum 80% mutation
score:

```
spectral_dimension.py
adaptive.py
finite_size_scaling.py
phase_gates.py
statistics.py
```

## Commit Discipline

One logical scientific behavior per TDD cycle. Do not bundle unrelated
changes. Run the full test suite before each milestone checkpoint. If a
refactor breaks a previously passing test, revert or isolate the refactor
before continuing.

## Completion Rule

Never state a milestone is complete based on reasoning alone. A milestone
is complete only after the specified verification commands are run and
their output is shown in the session transcript.

If an unresolved scientific ambiguity prevents implementation, stop and
record it in `docs/assumptions.md` instead of silently choosing an
interpretation — follow the existing entry format (ambiguity / default /
evidence marker / if-wrong consequence).

## Relationship to the Global Rule Stack

This repo inherits the user's global `~/.claude/rules/*` stack
(Falsification Ladder, EstimandOps, Perelman audit, doubt-driven
development, audit-verification-gate). The five Phase-0 docs above are this
project's concrete instantiation of that stack's Full-Ladder tier:

| Global concept | Local artifact |
|---|---|
| FL Step -3 (Novelty Check) | `docs/novelty_check.md` |
| EstimandOps L0/L1 | `docs/estimand.md` |
| Mathematical/scientific contract | `docs/mathematical_contract.md` |
| Falsification gates + verdict machine | `docs/falsification_gates.md` |
| Assumption registry (Gate 1 provenance + every default) | `docs/assumptions.md` |
| Oracle Adequacy Gate (Step 2b) | `docs/falsification_gates.md` § Oracle Adequacy |
| Kill Analysis / Minimal Relaxation Rule on REJECT | `docs/falsification_gates.md` § On a REJECT |

A future REJECT verdict's `decision.md` still belongs in a project-level
`null_results/` per the global protocol — not invented fresh here.
