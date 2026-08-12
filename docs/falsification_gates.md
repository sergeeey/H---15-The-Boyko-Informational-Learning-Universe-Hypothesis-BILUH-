# Falsification Gates — BILUH / boyko-benchmark

Frozen Phase-0 artifact. Defines the verdict machine `phase_gates.py` must
implement — nothing else may compute or emit a Stage-1 verdict. Every
threshold here is fixed before any production run (Anti-Overfitting
discipline: a gate loosened after seeing a borderline result is invalid).

---

## Two Separate Results (never conflate them)

### Gate A — Geometric Phase Candidate (implemented in this version)

Tests only whether Arm A's adaptive dynamics produces stable, finite-size-
convergent geometric observables, statistically separated from matched
negative controls. Six criteria, `G1`–`G6`, all defined in terms of
quantities from `mathematical_contract.md` and the MCID from `estimand.md`.

### Gate B — Physical Spacetime Candidate (NOT implemented, this version)

Requires, at minimum: Lorentz-symmetry recovery, relativistic dispersion
relation, causal covariance, field excitations, gauge structure, gravity.
None of these are defined, measured, or tested anywhere in this codebase.
**No code, test, doc, plot title, or log message in this repository may
imply Gate B has been attempted, let alone passed.** This separation exists
specifically to block the false inference `geometric network = physical
spacetime` (ТЗ.txt §10).

---

## Gate A — Criteria (all six required for SURVIVES)

Each criterion is evaluated **per arm, aggregated across the full FSS grid**
(`mathematical_contract.md` §6) — never from a single `N`, never from a
single seed.

| ID | Criterion | Pass condition | Source quantity |
|---|---|---|---|
| **G1** | Finite-size stability of spectral behavior | The heat-kernel `d_s(t)` plateau value (§5.1) does not drift monotonically with `N` across the FSS grid — its estimate at the largest `N` tested falls within the 95% CI of its estimate at the second-largest `N` (convergence, not divergence) | `spectral_dimension.py` output per `(arm, N)` |
| **G2** | Appropriate spectral-gap closure | Regression of `λ_1(N)` vs. `N` on a log-log scale (§5.2) yields `γ > 0` with the fit's own `R² ≥ 0.9` — the gap genuinely closes with a *fitted*, not assumed, exponent | `laplacian_gap.py` + `finite_size_scaling.py` |
| **G3** | Graph-distance growth inconsistent with trivial expander behavior | `diameter(N)` growth is significantly better fit by a power law (`δ > 0`, `R² ≥ 0.9`) than by a logarithmic (small-world) model on the same data — model comparison, not just "a slope was fit" | `graph_geometry.py` + `finite_size_scaling.py` |
| **G4** | Low-energy mode delocalization | `IPR(N)` scaling exponent `η` (§5.3) is bounded away from 0 with `R² ≥ 0.9` — modes shrink in concentration as `N` grows, ruling out persistent localization | `ipr.py` + `finite_size_scaling.py` |
| **G5** | Operational finite-propagation behavior | The `r_q(t) = v_eff·t + b` fit (§5.5) achieves `R² ≥ 0.9` over its declared unsaturated window, with a finite, positive `v_eff` and a documented saturation radius — front moves at a well-defined finite rate, neither frozen nor instantaneous | `propagation.py` |
| **G6** | Statistically meaningful separation from negative controls | **Tiered — see G6 Tiering below.** The MCID from `estimand.md` (`\|Cohen's d\| ≥ 0.8` **and** non-overlapping 95% CIs) is evaluated on each of the 5 G1–G5 observables, for Active vs. **each** of Frozen (B), Parameter-Matched Random (C), and Topology Scrambled (D) — 15 cells total | `effect_sizes.py` |

**Arm E (Fixed Flat Geometry)** is not a negative control for G6 — it is
the *positive* calibration anchor: the estimators themselves (§5 of the
contract) must reproduce known values on it (`d_s ≈ 3` for a 3D lattice,
etc.) as a prerequisite for trusting G1–G5 on any other arm at all. A
failure on Arm E's calibration tests blocks the Gate-A run entirely — it is
a Substrate/Oracle problem, not evidence about Active (see Oracle Adequacy
note below).

**Arm F (Alternative Objective)** is not a G6 negative control either — it
answers a different question (is the result specific to this adaptation
rule, per `estimand.md`'s non-interpretation #2), reported alongside the
verdict but not gating it.

**Arm CD (Classical Diffusion Control, added 2026-08-11)** is likewise not
a G6 negative control — it answers yet another different question (is the
result specific to the unitary/quantum carrier, or does it arise under any
Laplacian-driven adaptive rule; `mathematical_contract.md` §2.2, §4). G1–G4
are reported for Arm CD alongside the verdict (computed identically to
every other arm, since they depend only on `W(τ)`); G5 uses the
carrier-agnostic `ρ_i(t)` notation. None of this gates G6 — Arm CD answers
a mechanism-specificity question, not a "did adaptation do anything"
question. **Do not compare Arm CD directly against Active for
carrier-specificity conclusions** — Arm CD necessarily uses the
combinatorial operator `L`, not `L_norm` (`[A18]`, `mathematical_contract.
md` §2.2), so a direct Active-vs-CD read confounds carrier and operator.
The correct carrier-isolating comparison is Arm CD vs. the
Operator-Independence Diagnostic's `L`-driven quantum rerun (§5.6 of the
contract) — both use `L`, differing only in carrier.

### G6 Tiering (added 2026-08-11, DDD skeptic finding #4)

**Why this exists:** requiring all 15 cells (5 observables × 3 comparators)
to simultaneously clear the MCID is a very strict conjunction — a real,
scientifically interesting *partial* geometric-phase result (e.g. clean
separation on 12 of 15 cells, with IPR vs. Frozen specifically ambiguous at
small `N` because both are dominated by the same few low modes there) would
be discarded as an undifferentiated `FAILS`, destroying exactly the
information a Stage-1 *screen* exists to surface. Pre-registered **now**,
before any production run, per Anti-Overfitting discipline — this
threshold is fixed here and does not move after seeing results.

```
15/15 cells clear MCID   →  G6_STRONG
≥10/15 cells clear MCID  →  G6_PARTIAL   (10 = 2/3 of 15, pre-registered)
 <10/15 cells clear MCID →  G6_FAIL
```

`phase_verdict.json` always records the full 15-cell matrix (which
observable, which comparator, effect size, CI, pass/fail) regardless of
tier — the tier is a summary, not a replacement for the raw grid.

### Verdict Machine

```
G1..G5 all PASS  AND  G6_STRONG   →  SURVIVES_GEOMETRIC_PHASE_SCREEN
G1..G5 all PASS  AND  G6_PARTIAL  →  SURVIVES_GEOMETRIC_PHASE_SCREEN_PARTIAL
otherwise                          →  FAILS_GEOMETRIC_PHASE_SCREEN
```

No fourth silent outcome. `SURVIVES_GEOMETRIC_PHASE_SCREEN_PARTIAL` is a
genuine, reportable Stage-1 outcome — not a euphemism for FAILS and not
promotable to the unqualified `SURVIVES` string in any downstream report.
Record which specific G1–G5 gates and which of the 15 G6 cells failed in
`phase_verdict.json` either way. A mixed result is exactly the input the
Kill Analysis (below) is for.

---

## Oracle Adequacy — `phase_gates.py` must be tested as a judge, not just as code

Per the Oracle Adequacy Gate (Step 2b of this project's Falsification
Ladder): before any Active-arm verdict is trusted, `phase_gates.py` itself
must be shown to discriminate correctly on inputs with a **known** answer:

- **Positive control (single-arm):** feed the gate machinery synthetic data
  shaped like a genuine converging geometric phase (e.g., the Fixed Flat
  Geometry arm's own FSS trajectory, or a synthetic power-law-consistent
  series) → must return `PASS` on each of G1–G5 individually.
- **Negative control (single-arm):** feed it a synthetic non-convergent /
  non-power-law series (e.g., random noise scaling, or an expander-like
  flat `λ_1(N)`) → must return `FAIL` on each of G1–G5 individually.
- A gate implementation that cannot tell these two synthetic cases apart on
  G1–G5 is `ORACLE_INADEQUATE` — fix the gate logic before running it on
  any real arm's data.

**Paired-arm synthetic tests (added 2026-08-11, DDD skeptic finding #6) —
required in addition to the single-arm checks above.** The single-arm
checks alone cannot exercise G6's 15-cell cross-arm tiering logic at all
(there is no second arm to compare against). Required synthetic paired-arm
cases, each with a known correct tier:

| Synthetic input | Cells clearing MCID | Expected tier |
|---|---|---|
| Two arms with `\|d\| ≈ 0.9` on all 5 observables × all 3 comparators | 15/15 | `G6_STRONG` |
| Two arms with `\|d\| ≈ 0.7` on 4 of 5 observables (below threshold on all 3 comparators for the 5th) | 12/15 | `G6_PARTIAL` |
| Two arms with `\|d\| ≈ 0.9` on only 1 comparator, `\|d\| ≈ 0.3` on the other 2 | 5/15 | `G6_FAIL` |

A gate that misclassifies any of these three synthetic tiers is
`ORACLE_INADEQUATE` for the G6 tiering logic specifically — this is a
distinct failure mode from the single-arm G1–G5 checks above and must be
reported separately.

This is a check on the judge, independent of whether Active's real data
ultimately passes or fails.

---

## Terminology Lock (enforced, not aspirational)

**Never claim, anywhere in code, comments, docstrings, plot titles, log
messages, or generated reports** — unless a later specification explicitly
defines *and* verifies it:

- physical spacetime emerged
- Lorentz invariance was proven
- a Lieb–Robinson theorem was proven
- quantum gravity was reproduced
- the Boyko Informational Reality Hypothesis (or BILUH) was confirmed
- "learning" (unadorned) for the adaptive weight dynamics — use `adaptive
  Hebbian meta-dynamics` (`mathematical_contract.md` §3)

**Machine-checkable canary (must be run and shown green before any
milestone is declared complete, mirrors the `/goal` example in ТЗ.txt §17):**

```bash
grep -RiE "PHYSICAL_SPACETIME_CONFIRMED|LIEB_ROBINSON_PROVEN|physical spacetime emerged|lorentz invariance (was |is )?proven|quantum gravity (was |is )?reproduced|hypothesis (was |is )?confirmed" src/ docs/ tests/ scripts/
```

Must return no matches outside this file itself (which quotes the forbidden
strings intentionally, as the canary's own reference list).

The strongest allowed Stage-1 output string is exactly one of:
`SURVIVES_GEOMETRIC_PHASE_SCREEN`, `SURVIVES_GEOMETRIC_PHASE_SCREEN_PARTIAL`
(§ G6 Tiering above), or `FAILS_GEOMETRIC_PHASE_SCREEN`. The `_PARTIAL`
suffix must never be silently dropped when the verdict is reported or
quoted downstream — reporting a `_PARTIAL` result as the unqualified
`SURVIVES_GEOMETRIC_PHASE_SCREEN` is itself a terminology-lock violation.

---

## On a REJECT (FAILS_GEOMETRIC_PHASE_SCREEN)

A `FAILS` verdict is not "the project failed" — it falsifies a specific,
narrow, documented set of assumptions (per the Minimal Relaxation Rule,
`falsification-ladder.md`). The result written to `phase_verdict.json` and
any accompanying `decision.md` must include a **Kill Analysis**:

1. **What was killed, precisely** — cite the exact `AdaptationRule`
   (§3.2 of the contract), its parameters (`η`, `K` from `[A9]`), and the
   generative model (`[A7]`) under which the FAILS verdict was obtained.
   The claim killed is *"HebbianAdaptation with these specific parameters,
   under this specific initial-graph model, fails Gate A"* — not
   "adaptive dynamics can't produce geometry."
2. **What was NOT killed** — the mathematical contract's operator choices
   (`[A1]`, `[A5]`), the verdict machinery itself (if it passed its own
   Oracle Adequacy check), and any Gate-A criteria that individually
   passed.
3. **Relaxation map** — per the Minimal Relaxation Rule, any follow-up
   variant changes exactly **one** assumption from the registry (a
   different `η`/`K` per the `[A9]` sensitivity sweep already planned in
   `estimand.md`, or a different adaptation rule per `[A4]`) and gets a new
   experiment ID. Do not bundle multiple changes into one retry.

---

## Cross-References

- Observable definitions and formulas: `mathematical_contract.md`.
- MCID, ICE handling, identifiability: `estimand.md`.
- Assumption provenance for every `[A#]`: `assumptions.md`.
- Prior-art positioning (what novelty claims are and are not licensed):
  `novelty_check.md`.
