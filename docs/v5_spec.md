# V5 — Balanced Support Rewiring: Technical Specification

**Status: PROPOSED, 2026-08-18. Not approved. Nothing implemented, nothing run.**

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
| **M3+** | Not specified here — deferred until `K1'`'s result is known, matching this project's own discipline of not pre-committing to a full campaign before the cheap gate resolves | — |

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

Based on this session's V4 timings (K1c/K1d's 5-seed campaigns at
N=512 completed within single-digit minutes each): `K1'` at the same
scale (N=512, 5 seeds, a comparable swap budget to V4's `ρ·|E|·
dtau_steps` exposure target) is expected to be similarly cheap —
comparable to or cheaper than K1c/K1d, since each swap slot is a
single argmax over an enumerated candidate set (no persistence
tracking, no cap bookkeeping, no capacity audit needed at this stage).

---

## 12. Regrowth/selection rule — DECIDED, not open

Deterministic argmax with a seeded tiebreak is the sole selection rule
specified here, for both `A3` and `A4` (differing only in which values
they argmax over). No stochastic/temperature-based variant is proposed
or licensed, matching V4 §12's own guardrail against physical-
temperature or vacuum-fluctuation interpretations of any future
stochastic extension.
