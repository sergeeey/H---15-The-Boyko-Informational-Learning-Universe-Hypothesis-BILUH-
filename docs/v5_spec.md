# V5 — Balanced Support Rewiring: Technical Specification

**Status: M0-M2 implemented and run (`[A65]`/`[A66]`); M3
(`V5-K1'-Exposure`, §13) RAN 2026-08-18 and returned `FAIL`
(`[A68]`, `null_results/20260818-v5-k1-prime-exposure.md`) — per §13.4's
own frozen stop-rule, no automatic follow-up. This is a result about ONE
scorer/budget/endpoint combination, NOT a rejection of the swap
substrate itself: `K_skip=0%` was reconfirmed at 2x the seed count and
5x the budget of `K1'`, so `V5`'s core feasibility claim (degree-
preserving connected rewiring avoids `V4`'s collapse) stands
independently of M3's negative result. See `[A68]`'s "What is NOT
killed" section before deciding what, if anything, comes next.**

**§14 (`C_ij` Recall@D/AUPRC Signal Diagnostic) RAN 2026-08-18:
essentially at chance (final-checkpoint `Recall@D` ratio `1.19x`,
`AUPRC` ratio `0.98x` its own exact chance baseline — corrected
same-day after a reviewer-caught baseline-formula error, `[A69]`) —
H1 (signal problem) favored over H2 (operator problem). The swap
operator's own feasibility is not implicated; `C_ij` itself does not
appear to encode
which specific edges were removed strongly enough for ANY selection
rule to exploit, at this `N`/damage level/adaptation rate.**

**§15 (Geometry Signal Audit) RAN 2026-08-18: World A, corrected —
`[A70]`/`[A71]`.** `[A70]`'s original `Re(C_ij)`-based result
(`AUROC≈0.49`, `Recall@D=0.0000` at every checkpoint) was caught by
review as analytically DEGENERATE on this exactly-bipartite lattice —
`Re(C_ij)` is forced to ~0 for every `d*=1` pair regardless of ground
truth, so that result could not have shown anything else. `[A71]`
verifies this independently and adds a magnitude-based companion
metric (`|C_ij|`) that does not share the degeneracy; the corrected
result STILL shows no meaningful geometric signal (`AUROC` stays within
`[0.49,0.52]` of chance at every checkpoint), now on solid footing
rather than a coincidence of a degenerate test. More upstream and more
decisive than `[A68]`/`[A69]`, with this important caveat: only the
`Re`/magnitude convention was tested, not a phase-only or higher-moment
observable. See `[A71]` for the full correction and `[A70]` for the
reproducible distance-parity side-finding (Pearl Registry,
`pearl_registry/INDEX.md`) that motivated the fix.

**§16 (Early-Time Timescale Sweep) RAN 2026-08-18: `[A72]` — timescale
hypothesis CLOSED.** `AUROC`/`Spearman` (the robust, full-distribution
metrics) stay at chance at EVERY checkpoint from window=1 through
window=49 — no timescale within this mechanism (frozen `eta=0.1`) shows
geometric encoding. A superficially interesting early-window elevation
in the sparser `Recall@D` metric was checked directly (not assumed) and
found to be bit-identical across trials with different source nodes —
a lattice-translation-symmetry artifact, not a per-node signal, the
same pattern `[A71]`'s own review already flagged for `AUROC_mag`. Per
the user's own frozen order (timescale first, `eta` next if unresolved
— Minimal Relaxation Rule), `eta` is the next, separately-motivated
candidate; not launched automatically.

**Status (as originally written, kept for history): PROPOSED, 2026-08-18.
Not approved. Nothing implemented, nothing run.**

**Revision 1 (2026-08-18, after `[A66]`) — M2's `K1'` result is PASS but
WEAK (`Cohen's d=0.63 < 0.8` MCID, effect concentrated in 1/5 seeds,
`K_skip=0%` confirming the substrate itself is clean). The user's own
diagnosis and pre-registration for the follow-up: `[A66]`'s weak result
is most plausibly compute-driven starvation (`n_swaps=3`/window,
`dtau_steps=10` ⇒ only ~30 committed swaps against ~148 damaged edges),
not evidence against the mechanism. §13 below pre-registers
**`V5-K1'-Exposure`** — a single, frozen dose-response follow-up, not an
open-ended budget search — BEFORE any of it runs. §8's `M3` row is filled
in accordingly.**

**Provenance.** Succeeds `V4` (`docs/v4_spec.md`, CLOSED 2026-08-18 as
`FEASIBILITY REJECT`, `docs/assumptions.md` `[A64]`,
`null_results/20260818-v4-prune-regrow-feasibility.md`). V4's entire
K1/K1c/K1d line established, via an exact capacity-optimization audit
(not a greedy-selector artifact), that INDEPENDENT edge-wise ranking-
then-deletion is structurally incompatible with the node-correlated
concentration this project's Hebbian dynamics produces, at two
independently-motivated incidence-cap formulations. V5 changes the
elementary structural operation itself — from independent edge
DELETION (decoupled from creation) to a degree-preserving, connectivity-
checked edge SWAP — directly because that decomposition was diagnosed
as the mechanism-level cause of V4's failure (`[A57]`-`[A64]`), not
because a different mechanism might happen to pass. This is the user's
own explicit synthesis, adopted here verbatim as the design brief.

**Why this removes V4's failure mode by construction, not by
constraint:** a swap `(a,b),(c,d) → (a,c),(b,d)` (or `(a,d),(b,c)`)
changes which edges exist but leaves every node's degree EXACTLY
unchanged. There is no node-level incidence budget to exhaust, no
degree to inflate via regrowth, no feedback loop between "how much was
just removed" and "how much may be removed next" — the entire class of
problem `[A57]`-`[A63]` diagnosed (star collapse, cap-vs-exposure
conflict) does not exist for this operation, because the operation
never creates the asymmetry (many-edges-removed-from-one-node) that
caused it.

Read `docs/assumptions.md` `[A64]` and
`null_results/20260818-v4-prune-regrow-feasibility.md` first if
resuming this project — this spec's §9 lists exactly what carries over
from V4 and what does not, so V5 does not silently re-derive already-
settled infrastructure decisions, nor silently re-inherit V4's killed
assumptions.

---

## 1. L0 Gate (EstimandOps — mandatory first step)

**Causal**, identical framing to `docs/v4_spec.md` §1: the experimental
unit is a whole simulation *run*, potential outcomes over runs, not
over individual swap events or nodes within one run (unit-level SUTVA
satisfied by construction — units are independent runs).

```
τ = E_u[Y_state(u) − Y_matched-null(u)]
```

`Y(u)` is the same `R_edge`-style restoration endpoint V4 used (§3
below), evaluated at the end of a fixed swap budget. The causal claim
remains scoped explicitly to "within this simulator" — no claim about
physical spacetime, BILUH, or any real network is licensed by any
result here, exactly as `docs/v4_spec.md` §1/§10 stated and as this
project's `CLAUDE.md` requires.

**Identifiability, unchanged from V4:** consistency, positivity,
exchangeability, and SUTVA are all satisfied by construction — `A3`
and `A4` are literally the same simulator with a different swap-scoring
function, run under the experimenter's full control, on independent
seeds.

---

## 2. Decision Gate — the three questions, answered before proceeding

### Q1. Is there a genuinely new mechanism, not just a harsher threshold?

**Yes.** Independent edge deletion and degree-preserving swap are
different elementary operations, not the same operation with a
different parameter. V4's entire cap-tuning exercise (`[A60]`-`[A63]`)
varied ONE parameter (`q`, and the degree source it read from) within
the SAME operation and hit an unmovable exact-optimum ceiling twice.
V5 does not vary that operation's parameters further — it replaces the
operation.

### Q2. Is there an observable that separates specific structural learning from generic rewiring?

**Yes**, and more cleanly than V4's original A3-vs-A4 contrast: `A4`
(matched-null swap) shares with `A3` (state-driven swap) the identical
initial graph, identical swap COUNT, identical degree sequence (both
are swaps — degree sequence is invariant for BOTH arms, automatically,
not something that needs separate matching), identical candidate-pair
pool, and identical distance profile of that pool. The only thing that
differs is WHICH specific pair, among legal candidates, gets chosen —
exactly isolating whether `C_ij` carries pair-specific information
useful for restoration, or whether any degree-preserving connected
rewiring at the same rate does equally well.

### Q3. Can a kill criterion be stated in advance, without parameter rescue?

**Yes** — §7 below states it before any V5 code exists. Critically,
this kill criterion does not need V4's ICE-1/ICE-2 exposure/
connectivity gates AT ALL: exposure is simply "how many swaps were
budgeted, all of which execute unconditionally on the same graph size"
(no eligibility bottleneck the way persistence-gated pruning had one),
and connectivity is enforced as **move legality**, not measured
post-hoc. There is no possible "grid INVALID" outcome analogous to
`[A57]`/`[A60]`/`[A62]` for the swap COUNT itself — a swap either has a
legal target or it doesn't, checked before commitment, never after.

**Verdict: PASS.** V5 is pre-registrable.

---

## 3. Estimand (EstimandOps L1)

**Population:** for the K1-equivalent gate (§8, M2-equivalent): the
T7/`[A32]` positive-control periodic cubic lattice, N=512, corrupted by
10% degree-preserving damage (reusing `corrupt_lattice_edges`
unchanged — see §9). For a later main campaign (not specified in
detail here, deferred to its own milestone): the same Erdős–Rényi
population V4's main campaign would have used.

**Intervention:** `A3`, state-driven swap selection — among the legal
swap candidates available this round, choose the one maximizing
`ΔS = C_added − C_removed` (§4).

**Comparator:** `A4`, matched-null swap selection — the identical
candidate generation and legality-checking machinery as `A3`, but the
specific candidate chosen is determined by a distance-stratified
permutation of the SAME `C_ij` values `A3` would have used (same
construction as V4's own `DistanceStratifiedShuffleScorer`, reused
conceptually — see §4), not an independent random draw. This preserves
the event count, the `C_ij` value multiset, and the correlation-
vs-distance dependence, destroying only pair-specific correspondence —
same design principle as V4 Revision 1's own A4 redefinition, carried
over because it was never the part of V4 that failed.

**Endpoint:** `R_edge = |E_recovered ∩ E_damaged_out| / |E_damaged_out|`
— UNCHANGED formula from V4's own corrected version
(`docs/v4_spec.md` §7, `[A61]`/`observables/edge_recovery.py`, reused
directly, not redefined).

**Summary measure:** difference in means across seeds, `Δ_specific =
Y(A3) − Y(A4)`, with Cohen's d and 95% CI, matching this project's
MCID convention (`|d| ≥ 0.8` and non-overlapping CIs).

**MCID:** `|Cohen's d| ≥ 0.8` and non-overlapping 95% CIs — unchanged
from V4's own frozen MCID (`estimand.md`, `[A10]`).

**ICE (Intercurrent Events) — qualitatively different from V4's:**

| ICE | Strategy | Why this differs from V4 |
|---|---|---|
| A proposed swap has no legal target this round (all candidate pairs illegal: would create a multi-edge, self-loop, or disconnect the graph) | **while-active, per-swap**: skip that swap slot, do not substitute a worse-scored legal alternative silently — report the skip rate. If skip rate is high, that is itself informative (§7, `K1'`), not hidden. | V4's ICE-1 (exposure) was about a STRUCTURAL inability to reach the target count at all across many windows; V5's analog is per-swap-slot and, by construction, only occurs when the ENTIRE legal candidate pool is exhausted — a much rarer, more informative event. |
| Disconnection | **Cannot occur by construction** during the run itself — a swap is only committed if the resulting graph is connected (§4). The only place disconnection can enter is if the DAMAGED graph itself (before any V5 dynamics) is already disconnected — checked explicitly before the run starts (§8), with a bounded-retry re-damage if so, mirroring `generators.py`'s existing `_MAX_CONNECTIVITY_RETRY_ATTEMPTS` pattern. | V4's ICE-2 was a run-time failure mode requiring truncation. V5 has no run-time analog — connectivity is a precondition on every state, not a property that can be lost mid-run. |

**Independence rule (unchanged from V4/Phase 11-12):** comparisons are
across independent seeds only, never across swap events or time points
within one run.

**Six independent seed streams, same discipline as V4 §3 (`[A11]`):**
`graph_seed` (damage), `initial_state_seed` (psi0, deterministic
lattice-center here so effectively unused, kept for interface
parity), `carrier_noise_seed` (unused, `gamma=sigma=0` as in every V4
K1-equivalent run), `adaptation_seed` (unused — Hebbian weight
adaptation has no RNG), `swap_tiebreak_seed` (breaks exact ties in
`ΔS` ranking among legal candidates), `matched_null_permutation_seed`
(drives A4's distance-stratified shuffle). Reuses `SeedManager`
(`[A11]`) unchanged.

---

## 4. Mathematical contract addendum (proposed — to be formalized in `mathematical_contract.md` as a dated Addendum 5 at M0, before any code)

**Elementary operation: degree-preserving, connectivity-checked,
simple-graph edge swap.**

Given the current topology mask `M` and two currently-existing,
node-disjoint edges `(a,b)` and `(c,d)` (i.e. `{a,b} ∩ {c,d} = ∅`,
the standard precondition for a valid double-edge-swap — prevents
self-loops and degenerate cases by construction), the swap replaces
them with EITHER:

```
reconnection 1: (a,c), (b,d)
reconnection 2: (a,d), (b,c)
```

**A swap (a specific pair of existing edges + a specific reconnection
choice) is LEGAL iff, after applying it:**

1. The result is a simple graph (neither `(a,c)`/`(b,d)` nor
   `(a,d)`/`(b,c)`, whichever reconnection is being evaluated, already
   exists as an edge elsewhere in the current graph — no multi-edges).
2. The result is connected (checked via BFS from any node, reusing
   `hop_distances_from_source`, same primitive V4's while-active check
   used — `observables/propagation_front.py`).

**Degree preservation is automatic, not a checked property** — every
node's degree is invariant under this operation by construction
(each of `a,b,c,d` loses exactly one incident edge and gains exactly
one), so there is nothing to verify here, unlike V4's incidence cap
which required active enforcement.

**Candidate generation for one swap slot:** enumerate all currently-
existing edge pairs `{(a,b),(c,d)} : {a,b}∩{c,d}=∅`, times the 2
possible reconnections each, filter to LEGAL ones (both conditions
above), yielding the candidate pool for that slot. `A3`'s score
`ΔS = C_added − C_removed` is then computed per legal candidate:

```
C_removed = C_ij(a,b) + C_ij(c,d)          [edges being deleted]
C_added   = C_ij(new_edge_1) + C_ij(new_edge_2)   [edges being created]
ΔS = C_added − C_removed
```

using the SAME time-averaged correlation `C_ij` V4 used
(`dynamics/adaptive.py`'s `time_averaged_correlation`, reused
unchanged). `A3` deterministically picks the LEGAL candidate
maximizing `ΔS`, ties broken by `swap_tiebreak_seed` (same seeded-
tiebreak discipline as V4's Top-K, `np.lexsort`).

**`A4` (matched-null):** identical candidate generation and legality
filtering. Score assignment: the `ΔS` values computed for the SAME
candidate pool are permuted within graph-distance strata of the
INVOLVED node pairs (reusing `DistanceStratifiedShuffleScorer`'s
stratification logic conceptually — same "preserve the value multiset
and the distance-vs-value dependence, destroy only pair-specific
correspondence" principle), then the same deterministic-argmax-with-
tiebreak selection rule picks the top-scoring (now shuffled) candidate.

**Swap budget, not a rate rule.** Unlike V4's `ρ·|E|` per-window rate
(which existed to define exposure against a target that could be
under-realized), V5's structural-change unit is simply "N_swaps per
window," a DIRECT parameter, not a target subject to eligibility
gating. `N_swaps` is frozen before any run (§8), not tuned after
seeing results.

**No stochastic/temperature-based selection, same guardrail as V4 §12:
deterministic argmax with a seeded tiebreak only.** No claim of
physical temperature or vacuum fluctuation is licensed for any future
stochastic variant, unchanged from V4's own explicit rejection.

---

## 5. Arms

| Arm | Selection rule | Degree | Connectivity |
|---|---|---|---|
| **A3 — state-driven swap** | deterministic argmax of `ΔS = C_added − C_removed` over legal candidates | invariant (swap) | enforced by move legality |
| **A4 — matched-null swap** | distance-stratified shuffle of the SAME `ΔS` values, then deterministic argmax | invariant (swap) | enforced by move legality |

Only two arms for the K1-equivalent gate (§8) — V4's full seven-arm
Stage-1 table is out of scope here; V5 is confined to the same narrow
question V4's K1 line was confined to (does state information help
damaged-lattice restoration), not a re-run of the full benchmark.

---

## 6. The confound V4 already named and controlled — carried over unchanged

`ψ` spreads over the graph, so nearby nodes have correlated `ψ`, and a
rule that favors high-`C_ij` new edges could simply connect already-
nearby nodes for reasons having nothing to do with genuine pair-
specific learning. `A4`'s distance-stratified shuffle exists
specifically to control for this, exactly as it did in V4
(`docs/v4_spec.md` §5) — carried over unchanged, not re-derived.

---

## 7. Kill criteria — pre-registered, in evaluation order

**`K1'` — the damaged-lattice restoration gate (cheap, runs first,
direct analog of V4's K1 but without an ICE-invalidation risk by
construction).** Same T7/`[A32]` lattice, same 10% degree-preserving
damage, same `R_edge` endpoint and formula. **PASS requires
`R_edge(A3) > R_edge(A4)`.** If A3 does not beat A4: `K1' FAIL ⇒
STOP` before any larger campaign — same discipline as V4's own P2/K1.

**`K_skip` — legal-candidate exhaustion rate.** Fraction of swap slots
across the whole run where the legal candidate pool was empty (no
swap could be committed that round). Reported per run; **if this
exceeds 20% of swap slots, that specific run's `R_edge` is flagged
`[WEAK]`**, not silently trusted — mirrors V4's own ICE-1 threshold
philosophy (a bare majority of intended structural change actually
happening) without claiming V4's exact 0.95 number transfers
unchanged to a qualitatively different operation.

**No `H-A`/`H-B` capacity-audit distinction needed at K1' — stated
explicitly, not by omission.** V4 needed `[A61]`/`[A63]`'s exact-
optimum audit because ITS selection was a many-to-one CONSTRAINED
problem (rank many edges, delete under a shared cap) where greedy could
plausibly be suboptimal. V5's selection is a single best-candidate
argmax per swap slot — there is no analogous constrained-optimization
question to audit; each slot's choice is independently, trivially
optimal by construction (deterministic argmax over an exhaustively
enumerated legal candidate set).

---

## 8. Milestones (each gates the next)

| # | Deliverable | Gate |
|---|---|---|
| **M0** | Dated Addendum 5 to `mathematical_contract.md` (§4 above, formalized); this spec committed | Contract revised before code, per `CLAUDE.md` |
| **M1** | Swap-operation infrastructure + TDD: legality checker (simple-graph + connected), candidate generator, `ΔS` scorer, deterministic-argmax-with-tiebreak selector, `A4`'s distance-stratified shuffle reused from V4's `DistanceStratifiedShuffleScorer` logic. Degree-invariance and connectivity-by-construction verified as explicit test invariants, not assumed. | All tests green before any science |
| **M2** | `K1'` damaged-lattice restoration gate at real scale (N=512, 5 seeds, same `master_seed=20260818` convention) | **KILL GATE** — stop here if `K1'` fails |
| **M3** | `V5-K1'-Exposure` — frozen dose-response follow-up (§13), pre-registered after `[A66]`'s weak-but-clean `K1'` result. **RAN 2026-08-18: `FAIL`** — `[A68]`, `null_results/20260818-v5-k1-prime-exposure.md`. `K_skip=0%` reconfirmed (substrate not the limiting factor); state-specific advantage did not clear MCID/majority even at `B=D`. | Per §13's own frozen stop-rule — no automatic `M4`, applied |

**Before M2 runs:** verify each seed's damaged graph is connected
BEFORE any swap dynamics start (bounded-retry re-damage if not, same
pattern as `generators.py`'s `_MAX_CONNECTIVITY_RETRY_ATTEMPTS`) —
`corrupt_lattice_edges` does not currently guarantee this, and it is a
precondition V5's connectivity argument depends on.

---

## 9. What carries over from V4, and what does not

**Carries over (established, reused unchanged):**
- `corrupt_lattice_edges` (degree-preserving damage) — same tool,
  now ALSO the same TYPE of operation as V5's own elementary swap,
  which is a pleasing consistency V4 didn't have (V4's damage mechanism
  and its own topology rule were different operation classes; V5's are
  the same class).
- `R_edge`/`compute_edge_recovery` (`[A61]`'s corrected formula) —
  identical, no redefinition needed.
- `SeedManager` (`[A11]`), `DistanceStratifiedShuffleScorer`'s
  stratification LOGIC (reused conceptually for `A4`'s permutation,
  even though the concrete scorer class differs since it now operates
  on swap candidates, not regrow candidates).
- `time_averaged_correlation` (`dynamics/adaptive.py`).
- `hop_distances_from_source` (connectivity checking primitive).
- The MCID definition, seed discipline, provenance capture, and the
  general Falsification Ladder / EstimandOps process this whole
  project follows.

**Does NOT carry over (deliberately not reused):**
- `RateBasedTopologyRule` / `BoundedIncidenceTopologyRule` and the
  entire incidence-cap apparatus — the mechanism V5 exists to replace.
- V4's ICE-1 (exposure)/ICE-3 (cap activity) gates and the exact-
  capacity-audit technique (`observables/capacity_matching.py`) — not
  needed for the reasons stated in §7, though the MODULE remains
  available if a future V5 variant ever reintroduces a constrained-
  selection step.
- V4's `q`, `d_min`, persistence-window `m` parameters — none of these
  concepts apply to a swap-based operation.

**Unresolved and untouched by V5:** `[A45]`'s Phase 11-12 anomaly
(shuffled correlations beating real ones on curvature) remains open.
V5 does not test it and must not be read as bearing on it, same
disclaimer V4 carried.

---

## 10. What a V5 result will NOT mean

Written before results, per EstimandOps requirement, same discipline
as V4 §10:

1. Does **not** establish emergent physical geometry, spacetime, or any
   BILUH claim.
2. Does **not** generalize beyond the specific swap budget, N=512, or
   this adaptation rule, tested here.
3. A positive `Δ_specific` establishes that state-driven swap selection
   differs from distance-matched swap selection — **not** that the
   resulting structure is geometric, for the same reason V4 §10 named:
   `[A39]`'s G1 non-convergence gives no reason to expect otherwise.
4. Does **not** revive V4's `FEASIBILITY REJECT` (`[A64]`) or Phase
   11-12's REJECT — both stand on their own evidence regardless of
   V5's outcome.
5. A `K1'` PASS does **not** retroactively validate independent-edge-
   deletion as a viable mechanism — it would validate the SWAP
   operation specifically, which is what this document pre-registers.

---

## 11. Cost estimate

**Original estimate (kept for history, found WRONG during M1, not
silently corrected):** based on V4's timings, `K1'` at N=512 with a
swap budget comparable to V4's `ρ·|E|·dtau_steps` exposure target was
expected to be cheap. This assumed candidate SELECTION cost scales like
V4's rate rule (bounded by `n_target`), not realizing swap candidate
GENERATION itself is `O(|E|^2)` — a fundamentally different scaling
than V4's `O(n_target)` selection.

**Corrected, per `docs/assumptions.md` `[A65]` (measured, not
estimated):** at N=512, `generate_swap_candidates` enumerates ~2.3
million legal candidates per call; even fully vectorized, each swap
slot costs ~1.2-1.3s (dominated by `np.lexsort` over that array). The
swap budget is calibrated DOWN accordingly (§8 M2's own parameters:
`n_swaps_per_window=3`, `dtau_steps=10`, ≈300 total swap-slot
operations across the 5-seed/2-arm campaign, ≈6 minutes estimated) —
a compute-driven adjustment made from measured cost BEFORE any `K1'`
run, not a response to seeing `R_edge`.

---

## 12. Regrowth/selection rule — DECIDED, not open

Deterministic argmax with a seeded tiebreak is the sole selection rule
specified here, for both `A3` and `A4` (differing only in which values
they argmax over). No stochastic/temperature-based variant is proposed
or licensed, matching V4 §12's own guardrail against physical-
temperature or vacuum-fluctuation interpretations of any future
stochastic extension.

---

## 13. `V5-K1'-Exposure` — dose-response follow-up (Revision 1, pre-registered before any of it runs)

**Question this answers.** `[A66]`: `K1'` PASSED the bare inequality
but weakly (`d=0.63 < 0.8` MCID, 1/5 seeds carrying almost the entire
effect), while `K_skip=0%` showed the substrate itself is fully
feasible. Was the weak result caused by an insufficient number of
structural opportunities (starvation), or does state-driven selection
genuinely not beat the matched null even when given as many swaps as
there are damaged edges to recover?

**This is a distinct experiment from `K1'`, not a re-run of it** — the
question, the budget, and the primary diagnostic (`ΔR(B)`, a curve, not
a single-point inequality) are all new. It is also **not** a revival of
`V4`'s `FEASIBILITY REJECT` (`[A64]`,
`null_results/20260818-v4-prune-regrow-feasibility.md`) — that verdict
concerned independent edge pruning, a different elementary operation;
nothing here touches or reopens it.

**L0 gate:** unchanged from §1 — causal, potential outcomes over whole
runs, same identifiability argument. No new estimand primitive is
introduced; `B` (swap budget) becomes an indexing variable for a
dose-response CURVE over the same `Y(A3)`/`Y(A4)` endpoint, not a new
outcome.

### 13.1 Budget — frozen from damage size, not from the observed effect

`D` = number of genuinely-damaged edges for a given seed
(`len(damaged_out)`), observed in `[A66]` to be 146–149 out of 1536 at
`damage_fraction=0.10`, N=512. Freeze a single nominal value for the
whole campaign:

```
D_nominal = 148
B_total   = D_nominal = 148   (target committed swaps, full run)
```

**Deliberately NOT chosen to reach `d≥0.8`** — chosen because it equals
the number of things there are to recover, the natural upper reference
scale for "enough exposure," decided before any checkpoint is read.

**`n_swaps_per_window` stays frozen at 3** (§8 M2's own value) — the
follow-up increases the number of topology WINDOWS, not the
per-window rate, so the timescale ratio between fast dynamics and
structural update is unchanged from `K1'`. Changing the rate would
confound "was it starved" with "does a faster structural clock change
the answer," which is a different, unasked question.

**Checkpoint window schedule (frozen, single continuous run per
arm/seed — not three separate restarted runs):**

| Checkpoint | `B/D` target | Window count (`round(target/3)`) | Nominal committed swaps |
|---|---|---|---|
| C1 | 0.2 | 10 | 30 |
| C2 | 0.5 | 25 | 75 |
| C3 | 1.0 (= `B_total`) | 49 | 147 |

`dtau_steps=49` for the whole run; `R_edge`, cumulative committed, and
cumulative skipped are recorded at windows 10, 25, and 49 from ONE
continuous trajectory per arm/seed — never by restarting
`run_adaptive_dynamics_v4` at three different `dtau_steps` values,
which would not guarantee the first 10/25 windows are identical to a
standalone shorter run unless verified, and this design sidesteps that
question entirely rather than assuming it. Actual committed-swap counts
at each checkpoint are MEASURED (via the accumulating wrapper), not
assumed to equal `3×window_count` — `K1'`'s `K_skip=0%` makes that a
reasonable expectation, not a substitute for reporting the real number.

**No further checkpoints, no reactive insertion of a 4th.** All three
are reported regardless of what C1/C2 show — cherry-picking the
"nicest" checkpoint post hoc is exactly what this table exists to
prevent.

### 13.2 Primary diagnostic

```
ΔR(B) = R_edge(A3, B) − R_edge(A4, B)
```

reported at all three checkpoints, forming a dose-response curve, not
a single point. This is deliberately a stronger requirement than
`K1'`'s own bare `R_edge(A3) > R_edge(A4)` — the interpretation below
depends on the SHAPE of `ΔR(B)`, not just its sign at `B=D`.

### 13.3 Seed count — decided by measured compute cost, not by the observed effect

Preference order, stated before any timing is measured:

1. **10 paired seeds** if the measured real per-window cost (§11,
   `[A65]`) keeps the full campaign within roughly the same order of
   magnitude of wall-clock effort already spent on this project's other
   real campaigns.
2. **5 seeds** (reusing exactly `K1'`'s own `seed_index 0..4`, same
   `master_seed=20260818` — directly comparable damaged lattices) if
   compute is not tolerable at 10.

**The actual choice is made from a timing PROBE run before the full
campaign, documented as a compute decision in `docs/assumptions.md`
(same precedent as `[A65]`) — never chosen after seeing any `R_edge`
value from this follow-up.** If 5 seeds are used, results are reported
with explicit caution about `d`'s instability at `n=5` (§13.5) rather
than silently treated as equally powered to a 10-seed run.

### 13.4 Success / stop criteria — frozen in evaluation order

**Primary, at `C3` (`B=D`):**

```
ΔR_edge(B=D) > 0   AND   Cohen's d ≥ 0.8   (non-overlapping 95% CIs)
```

**Additional requirement, not substitutable by the above:**

```
majority of paired seeds show A3 > A4 at C3
```

A large standardized effect concentrated in one seed (exactly `[A66]`'s
own failure mode) does not, by itself, satisfy this follow-up's
success criterion even if `d≥0.8` is reached numerically.

**Frozen stop-rule — no exceptions, no automatic escalation:**

> If, at `B/D=1.0` (`C3`), the substrate remains fully feasible
> (`K_skip` still near 0%) but `A3` does not beat `A4` by the MCID
> above, `V5-K1'-Exposure` is closed as its own result. No automatic
> `2D`, `5D`, or `10D` follow-up is run. A further budget increase would
> require a new, separately-motivated pre-registration, exactly like
> this one — never a silent continuation.

### 13.5 Interpretation, pre-registered before data (four buckets)

1. **Strong positive.** `ΔR(B)` increases with `B` (at least up to some
   saturation) and, at `C3`, `A3>A4` with `d≥0.8` distributed across a
   majority of paired seeds, not concentrated in one. Read as: state-
   specific correlation information causally improves recovery of a
   known geometric structure inside this simulator — a genuine positive
   result for the swap mechanism, not a claim about BILUH, geometrogenesis,
   or physical spacetime (§10 still applies in full).
2. **Null.** `A3 ≈ A4` all the way to `C3`. The "just not enough swaps"
   explanation is substantially weakened (the budget now equals the
   damage count). `V5-K1' FAIL` under this follow-up's own criteria;
   the stop-rule (§13.4) applies — no automatic larger budget.
3. **Both improve, no differential.** `R_edge(A3)` and `R_edge(A4)` both
   rise with `B`, but `ΔR(B)≈0` throughout. Read as: degree-preserving
   rewiring helps generic structural recovery, but the specific
   `C_ij`-driven selection carries no additional value over a
   distance-matched null — informative and reportable, but a negative
   result for the state-specific mechanism this project cares about.
4. **Non-monotonic.** `A3` leads at an intermediate checkpoint, then
   the gap shrinks or reverses by `C3`. Report the full `ΔR(B)` curve
   honestly as non-monotonic dose-response (possible over-rewiring or
   disruption of already-restored structure) — the pre-registered `C3`
   endpoint remains the one the stop-rule is evaluated against; a
   better-looking intermediate checkpoint is never substituted for it
   after the fact.

**What this follow-up does NOT establish, regardless of outcome** — all
of §10's five points apply unchanged, plus: a strong-positive result
here would validate the SWAP operation with a properly-powered budget,
not resurrect V4's independent-deletion mechanism, and would not by
itself be evidence for or against `[A45]`'s still-open Phase 11-12
anomaly.

### 13.6 What is already established independent of this follow-up

Regardless of `V5-K1'-Exposure`'s result, `[A66]`'s clean-substrate
finding stands on its own: **balanced, degree-preserving structural
moves resolve the feasibility conflict that `V4`'s independent edge
deletion could not** (`K_skip=0%` across 300 real swap-slot operations,
vs. `V4`'s `K1`/`K1c`/`K1d`, none of which ever produced a clean
substrate). This is a concrete adaptive-topology design principle, not
contingent on whether the state-specific advantage this follow-up tests
turns out to be strong, null, or absent.

---

## 14. `C_ij` Recall@D Signal Diagnostic — pre-registered before any of it runs (Revision 2, after `[A68]`'s FAIL)

**RAN 2026-08-18: `[A69]`.** Final-checkpoint `Recall@D` ratio `1.19x`
chance, `AUPRC` ratio `0.98x` its own exact chance baseline — the H1
(signal problem) bucket below, not H2. See `[A69]` for the full
per-checkpoint table, per-seed detail, and a same-day reviewer-caught
correction to the `AUPRC` baseline formula (§'s "computed exactly, not
assumed" claim below now holds for BOTH metrics, not just `Recall@D` —
it did not, in the first run).

**Motivation.** `[A68]` killed the state-specific SWAP advantage at
`B=D`, but left an important ambiguity unresolved (the user's own H1/H2
split): does `C_ij` itself fail to carry information about which edges
were removed (**H1 — signal problem**), or does it carry the signal but
the swap operator's combinatorial constraints fail to exploit it
(**H2 — operator problem**)? This diagnostic answers that directly,
without running the swap mechanism at all — a mechanistic probe, not
another campaign, and by construction far cheaper (no `O(|E|^2)`
candidate enumeration, `[A65]`'s bottleneck, is involved at all).

**L0 gate (EstimandOps — mandatory first step):** **Predictive**, not
causal. The question is "does the existing `C_ij` field, at a fixed
point in the dynamics, discriminate genuinely-damaged edges among
non-edges better than chance?" — a ranking/discrimination question
about an already-computed quantity, no intervention or counterfactual
is proposed. No DAG, no identifiability argument, no causal layer
required.

**Population:** the SAME T7/`[A32]` N=512 lattice, 10% degree-preserving
damage, SAME 10 seeds (`master_seed=20260818`, identical damaged
lattices to `K1'`/`K1'-Exposure` — direct comparability, no new draws).

**Procedure per seed:** run fast dynamics (`ClosedUnitaryBackend`) +
`HebbianAdaptation` (`eta=0.1`, `dt=0.05`, `k=50`, matching `K1'-
Exposure` exactly) on the DAMAGED graph, topology held FROZEN via
`IdentityStatefulTopology` (§ above — no swaps, no pruning, nothing
structural happens at all). Reuses `run_adaptive_dynamics_v4`
unchanged, with the identity rule in place of any real topology rule
and the same `on_window` checkpoint hook used for `K1'-Exposure`.

**Checkpoints:** SAME window counts as `K1'-Exposure`, `{10,25,49}` —
direct comparability with the `ΔR(B)` curve already recorded.

**Endpoint, at each checkpoint:** compute `C_ij = time_averaged_
correlation(trajectory)` from that window's own trajectory (the exact
quantity `CorrelationSwapScorer` would have used). Candidate universe =
every currently non-adjacent pair `(i,j)`, `i<j` (topology is frozen,
so this universe is IDENTICAL across all three checkpoints for a given
seed — only the `C_ij` VALUES change). Positive set = `damaged_out`
(the genuinely-removed lattice edges, as unordered pairs). Rank all
candidates by `C_ij` descending; report:

- **`Recall@D`** (primary, per the user's own preference for
  interpretability under extreme imbalance): fraction of the top-`D`
  ranked candidates (`D=len(damaged_out)` for that seed) that are
  actually in `damaged_out`.
- **`AUPRC`** (secondary): area under the precision-recall curve over
  the full ranking.
- **Chance baseline for both, computed exactly — NOT the same formula
  for each, corrected 2026-08-18 after a reviewer caught this document
  originally assuming otherwise:** `Recall@D` under a uniformly random
  ranking has expectation `D / M_candidates` (hypergeometric mean,
  exact). `AUPRC`'s chance expectation is a DIFFERENT closed form —
  `H_m/m + ((d-1)/(m(m-1)))(m-H_m)`, `H_m` = the `m`-th harmonic
  number (`_expected_average_precision`, `observables/signal_
  diagnostic.py`, verified against brute-force enumeration on small
  cases before being trusted). The two happen to be numerically close
  at this project's scale (`D≈148`, `M≈129,000` ⇒ both ≈`0.11-0.12%`)
  but are not interchangeable, and diverge sharply as `D` shrinks.
  Reported
  per-seed, not assumed constant, since `D` varies slightly by seed
  (`[A68]`: 142–150).

**No MCID, no PASS/FAIL gate — this is diagnostic, not confirmatory.**
The question this answers is interpretive (which hypothesis, H1 or H2,
does the next design decision rest on), not a claim requiring a
frozen-in-advance accept/reject threshold. Reported as a ratio to
chance (`Recall@D / baseline`), with the two-bucket interpretation
below stated before any run:

- **`Recall@D` and `AUPRC` orders of magnitude above chance** (e.g.
  `>10x`): `C_ij` DOES carry genuine information about which edges are
  missing — **H2 (operator problem)** is favored. A future attempt
  should focus on a better structural operator or endpoint, not on
  the correlation signal itself.
- **`Recall@D` and `AUPRC` near chance** (within roughly `2-3x`):
  **H1 (signal problem)** is favored — the correlation field itself
  does not encode which specific edges were removed, at this `N`/
  damage level/adaptation rate. Improving the swap operator further,
  without changing what drives the score, would not be expected to
  help.

**What this does NOT mean, regardless of outcome:** does not retroactively
validate or invalidate `[A68]`'s FAIL verdict (that stands on its own
evidence); does not test any DIFFERENT `N`, damage fraction, or
adaptation rate; a signal-favors-H2 result does not by itself specify
what the better operator or endpoint should be — only that it is worth
looking for one.

---

## 15. Geometry Signal Audit — pre-registered before any of it runs (Revision 3, after `[A69]`'s H1 finding)

**RAN 2026-08-18: `[A70]`, CORRECTED same-day by `[A71]`.** `[A70]`'s
`Re(C_ij)`-only result was analytically degenerate on this exactly-
bipartite lattice (chiral symmetry forces `Re(C_ij)≈0` for every
`d*=1` pair regardless of ground truth) — caught by review, verified
independently, fixed with a magnitude-based companion metric
(`time_averaged_correlation_magnitude`). World A still holds under the
corrected metric, now on solid footing. **Read `[A71]` before citing
this section — `[A70]` alone is not the final word.**

**Motivation.** `[A69]` found `C_ij` does not encode EXACT damaged-edge
identity — but that is a narrower claim than "`C_ij` carries no
geometric information at all." The user's own reframing: exact
single-edge recovery may simply be the wrong target. A network could
fail to identify "node 37 must connect to node 91" while still
encoding coarser locality ("37 and 91 are close," "same neighborhood,"
"distance ~1, not ~7"). This audit tests THAT question directly,
decoupled from damage/restoration entirely — the most upstream
possible check of whether `psi → C_ij` produces any detectable
geometric signal at all.

**L0 gate:** **Predictive**, not causal — same status as §14. "Does
`C_ij`, computed on the clean positive-control lattice, discriminate
pairs by their TRUE graph distance?" is a discrimination/correlation
question about an already-computed quantity; no intervention.

**Not a duplicate of `[A69]` or of `V4`'s `FEASIBILITY REJECT`** — this
runs on the UNDAMAGED lattice (no damage step, no restoration, no swap
operator at all), asking a strictly upstream question. `null-results-
pre-check`'s keyword match against `v4-prune-regrow-feasibility` is a
false positive: nothing here touches independent edge pruning.

### 15.1 Population and procedure

Same T7/`[A32]` N=512 lattice, but **UNDAMAGED** — the clean positive
control itself, with EXACTLY known ground-truth distances
`d*(i,j)` (`graph_distance_matrix`, already used for this project's own
G1-G6 gates elsewhere). No damage seed, no swap operator — topology
held frozen via the same `IdentityStatefulTopology` §14 introduced.

**"Trials," not "seeds" — a deliberate naming break, stated explicitly
rather than silently reusing "seed" to mean something else.** Nothing
in this loop is stochastic once the topology is undamaged and frozen:
`HebbianAdaptation` has no RNG, and `ClosedUnitaryBackend` with
`noise_seed=None`/`gamma=sigma=0` is deterministic. Ten identical
"seeds" would silently produce ONE identical result. Instead, 10 trials
vary the excitation SOURCE NODE (`localized_psi0`'s `source_node`),
drawn deterministically via `SeedManager(master_seed=20260818)` — a
genuine robustness check (does any geometric signal appear regardless
of where the excitation starts), not a cosmetic seed count.

Same checkpoints `{10,25,49}`, same `eta=0.1`/`dt=0.05`/`K=50` as §13/
§14, for continuity — not because they are optimal for this new
question, but so results are directly comparable in scale.

### 15.2 Four diagnostic levels, all computed per checkpoint per trial

Candidate universe here is EVERY pair `(i,j)`, `i<j` (not just
non-edges — unlike §14, the positive class below mostly IS existing
edges, which is the point: does correlation strength track adjacency).

1. **Nearest-neighbor discrimination.** Positive = `d*(i,j)=1`
   (true lattice edges), negative = `d*(i,j)>1`. `AUROC` (Mann-Whitney
   U, `scipy.stats.mannwhitneyu` — a trusted library implementation,
   not a re-derived formula, learning from `[A69]`'s own baseline-
   formula error), plus `Recall@D`/`AUPRC` and their EXACT chance
   baselines, reusing `signal_diagnostic.py`'s reviewer-verified
   `compute_rank_metrics` core directly (not a second, independently
   -written copy of the same math).
2. **Distance ordering.** Spearman `rho(C_ij, -d*(i,j))`
   (`scipy.stats.spearmanr`). `rho≈0` ⇒ no ordinal locality at all;
   `rho>0` and meaningfully large ⇒ closer pairs systematically score
   higher, independent of exact-edge questions.
3. **Distance shells.** Mean `C_ij` at each true distance value
   `d*=1,2,3,...` — a strong geometric encoding should show a
   systematic (not necessarily perfectly monotonic) decline.
4. **Top-D distance distribution.** Among the top-`D` (`D`=count of
   true `d*=1` pairs) candidates ranked by `C_ij`, the empirical
   distribution of TRUE distances — `P(d*=r | top-D)` for every `r`
   present, cumulative sum gives `P(d*≤r | top-D)`.

### 15.3 Interpretation, pre-registered before data — two worlds

**World A — no geometric signal at all.** `AUROC≈0.5`, `AUPRC≈`chance,
`rho≈0`, distance shells indistinguishable, top-`D` distribution
matches the base rate. Conclusion: **the problem is upstream of
topology learning entirely** — `psi → C_ij` itself does not produce
detectable geometric information at this `N`/adaptation rate, and no
future topology operator (swap-based or otherwise) can be expected to
recover geometry from a signal that isn't there. This would be a
materially stronger negative result than `[A68]`/`[A69]` — it would
argue against the fast-dynamics/correlation-functional/timescale
choices themselves, not just the restoration mechanism built on top of
them.

**World B — coarse geometry present, exact identity is not.**
`rho(C,-d*)` meaningfully positive, top-`D` candidates enriched for
low true distance, distance shells show a real trend — while `[A69]`'s
exact-edge `AUPRC` stays at chance. Conclusion: **`C_ij` encodes
locality but not exact adjacency** — the earlier target (recover the
specific missing edge) was too strict; a future mechanism should learn
a coarse distance/neighborhood metric, not a specific edge set.

**No MCID, no PASS/FAIL gate — diagnostic, matching §14's own
discipline.** The two worlds above are the pre-registered interpretive
buckets; a result landing between them is reported as such, honestly,
not forced into one bucket.

### 15.4 What this does NOT mean, regardless of outcome

Does not retroactively change `[A68]`'s FAIL or `[A69]`'s H1 finding
(both stand on their own evidence — this is a different, upstream
question). Does not test any damaged lattice, restoration, or swap
mechanism. A World-B result does not by itself specify what a coarse-
locality-learning mechanism should look like — only that one might be
worth designing. Does not license any claim about physical spacetime,
BILUH, or geometrogenesis regardless of outcome, per this project's
standing `CLAUDE.md` scope discipline.

### 15.5 Metric caveat, added same-day after `[A70]`'s own result — the `Re(C_ij)` convention is degenerate on THIS lattice

**Reviewer-caught (2026-08-18), independently verified, `[A71]`:** the
T7 periodic cubic lattice is exactly bipartite by coordinate-sum
parity, and EVERY `d*=1` pair is a cross-parity pair. For a
real-valued localized `psi0` evolved under `H=L_norm`, chiral spectral
symmetry forces `Re(<psi_i* psi_j>_K)` — the SAME convention `§15.2`'s
levels 1-4 use, and the SAME convention `CorrelationScorer`/
`CorrelationSwapScorer` use throughout this project — to cancel to
machine epsilon for cross-parity pairs REGARDLESS of ground truth. A
World-A verdict on `§15.2`'s `Re`-based metrics alone is therefore
UNFALSIFIABLE on this specific lattice — it cannot distinguish "no
signal" from "signal present but phase-encoded." §15.2's levels 1-4
are run BOTH on `Re(C_ij)` (as originally specified) AND on
`|C_ij|` (`time_averaged_correlation_magnitude`, `dynamics/
adaptive.py`) as a mandatory companion, not a substitute — `[A71]`'s
corrected result used both and reports both.

---

## 16. Early-Time Timescale Sweep — pre-registered before any of it runs (Revision 4, after `[A71]`'s corrected World A)

**RAN 2026-08-18: `[A72]`.** CLOSED — `AUROC`/`Spearman` at chance at
every checkpoint `{1,2,3,5,8,10,25,49}`. See `[A72]` for the full
per-checkpoint table and the cross-trial invariance check that ruled
out the early `Recall@D` elevation as a genuine signal.

**Motivation.** `[A71]`'s corrected (magnitude-based) result held World
A at windows `{10,25,49}`, but the raw numbers contain a weak,
un-chased hint: `Recall@D_mag` was higher at window 25 (`0.0446`) than
at window 49 (`0.0039`) — `[A71]` read this as noise/transient because
it didn't survive to the largest checkpoint, which remains the correct
call for THAT pre-registration's own primary-checkpoint discipline. But
it raises a genuinely new, cheap, well-motivated question `§15`'s
schedule never tested: **does an EARLIER, less-delocalized/less-adapted
snapshot of `psi`/`C_ij` show geometric structure that later windows
wash out?** A localized `psi0` spreads ballistically at first and only
later approaches a more delocalized, adaptation-mixed regime — `§15`'s
earliest checkpoint (window 10) may already be past whatever early
structure exists.

**Per the Minimal Relaxation Rule (falsification-ladder.md): exactly
ONE assumption changes here — the checkpoint schedule (timescale).
`eta=0.1` stays FIXED, unchanged from every prior test in this
project.** The user's own broader direction named both `eta` and
`timescale` as candidates; timescale is tested first because it is
cheaper (zero new source code — `checkpoint_windows` was already a
free parameter of `run_geometry_signal_audit_one_trial`) and better
motivated by data already in hand. If this sweep does not resolve the
question, varying `eta` (fixed here) is the natural next, separately-
motivated follow-up — not bundled into this one.

**L0 gate:** unchanged from `§15` — Predictive, not causal.

**Population and procedure:** identical to `§15.1` — SAME 10 trials
(SAME `master_seed=20260818`, SAME deterministic source nodes per
trial — direct continuity, not a new draw), SAME UNDAMAGED T7 N=512
lattice, SAME `eta=0.1`/`dt=0.05`/`K=50`, topology frozen. The ONLY
change: checkpoint schedule extends earlier and denser —
`{1,2,3,5,8,10,25,49}` (the last three reproduce `[A71]`'s own
checkpoints exactly, for direct comparability within one continuous
run rather than a second restarted one).

**Endpoint:** identical to `§15.2` — BOTH `Re`-based and `|C_ij|`-based
(magnitude) `AUROC`/`Recall@D`/`AUPRC`/Spearman/shells/top-D
distribution at every checkpoint, per `§15.5`'s mandatory-companion
rule (unchanged, the bipartite degeneracy applies at every timescale,
not just the ones `§15` originally tested).

**Interpretation, pre-registered before data:**

- **If `AUROC_mag`/`Spearman_mag` stay at chance at EVERY checkpoint,
  including the earliest (`window=1`):** the timescale hypothesis is
  closed — no sampling time within this mechanism (Hebbian correlation
  + frozen topology, this `N`/`eta`) shows geometric encoding. `eta` is
  then the next, separately-motivated candidate to test, not this
  mechanism's timescale.
- **If early windows show `AUROC_mag`/`Recall@D_mag` clearly and
  consistently above chance, decaying toward the already-known
  near-chance value by window 49:** a genuine, novel positive finding —
  early-time `C_ij` encodes something the late-time snapshot loses.
  This would directly motivate re-examining `K1'`/`K1'-Exposure`'s own
  scorer, which always samples `C_ij` from the CURRENT (late,
  post-many-windows) trajectory, never an early one — a real design
  lead, not just a curiosity.
- **Non-monotonic or single-checkpoint spikes:** report honestly as
  such, per this project's own non-monotonic-dose-response discipline
  (`§13.5`'s pattern) — no cherry-picking the nicest window.

**No MCID, no PASS/FAIL gate — diagnostic, matching `§14`/`§15`'s own
discipline.**

**What this does NOT mean, regardless of outcome:** does not test
`eta` (fixed); does not test any damaged lattice or the swap mechanism;
a positive early-time finding would not by itself validate any
specific restoration mechanism — only that early-sampled `C_ij` is
worth designing one around.
