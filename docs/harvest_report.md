# Harvest Report — boyko-benchmark (Phases 11-12), 2026-08-14

Per `/harvest` methodology (Asset Score = Reuse + Pain + Proof + Uniqueness,
each 1-5, max 20). Scope: everything built or found this session that has
value independent of whether the BILUH hypothesis itself survives.

## Asset table

| Asset | Type | Reuse | Pain | Proof | Uniqueness | Score | Action |
|---|---|---|---|---|---|---|---|
| Null-model toolkit (global shuffle, strength-stratified shuffle, ARI/partition-similarity, Forman-Ricci with zero-weight handling) | code_asset | 5 | 4 | 5 | 4 | **18/20** | Extract as standalone package |
| `null_results/` protocol instantiation (Kill Analysis, Relaxation Map, AOG-5 revival condition, dated addenda discipline) | process_asset | 5 | 4 | 5 | 3 | **17/20** | Extract as reusable research-discipline template |
| Falsification Ladder applied end-to-end (pre-registration → substrate gate → kill analysis → REJECT) | process_asset | 5 | 4 | 5 | 3 | **17/20** | Test as standalone methodology on a different project |
| Resumable, background-safe experiment runners (incremental JSONL, `(size,seed,cell)`-keyed resumability) | code_asset | 5 | 4 | 5 | 2 | **16/20** | Mini-library — generic to any long-running compute pipeline |
| conductance/modularity/curvature diagnostic module | code_asset | 4 | 3 | 5 | 3 | 15/20 | Keep as reusable module |
| Provenance/seed discipline (`OpenPilotProvenance`, fail-closed `dirty_flag`, `SeedSequence.spawn` for independent windows) | process_asset | 4 | 3 | 4 | 2 | 13/20 | Note/module, not standalone |
| `[A42]` nominal-vs-effective-topology finding (clamp creates implicit topology change) | research_asset | 3 | 3 | 4 | 3 | 13/20 | Worth a short write-up, generalizes to any clamped adaptive rule |
| `[A47]` theorem (`W=1` absorbing barrier, Cauchy-Schwarz+AM-GM proof) | research_asset | 2 | 2 | 5 | 4 | 13/20 | Research note; specific to this exact rule but the proof technique generalizes |
| `detect_plateau` + its N-dependent resolving-power finding (`[A36]`) | code_asset | 3 | 3 | 4 | 3 | 13/20 | Keep as module + documented caveat |
| T1-T10 regression suite (open-system dynamics validation) | code_asset | 2 | 3 | 5 | 2 | 12/20 | Archive as reference test pattern, tightly coupled to this project |
| `[A45]` open anomaly (shuffled correlations beat real ones) | research_asset | 2 | 2 | 3 | 5 | 12/20 | Preserve as a standalone open question (see Final Knowledge Map) |
| `[A53]`-`[A56]` negative mechanistic map (4 refuted explanations for `[A45]`) | research_asset | 2 | 2 | 4 | 3 | 11/20 | Archive as "what NOT to try again" for `[A45]` |

## Top-3 assets to develop (score ≥ 16)

1. **Null-model toolkit (18/20)** — the most reusable, most proven, most
   distinctive piece. Directly transplantable to any network-science
   project asking "is this metric measuring structure, or an artifact of
   a degenerate landscape / distribution shape?" Caught two real false
   positives this session (`[A41]`'s modularity, the first `[A43]`
   curvature reading before `[A44]`'s control).
2. **`null_results/` protocol (17/20)** — a working instantiation of
   honest negative-result bookkeeping (Kill Analysis, what-survived vs
   what-didn't, AOG-5 revival conditions). Directly reusable as a
   template for any hypothesis-testing codebase.
3. **Resumable runners (16/20)** — generic, proven pattern for
   long-running background compute: incremental JSONL, safe to kill and
   resume, no wasted recomputation. Zero BILUH-specific coupling.

## Next test (3 days, per `/harvest promote`)

For the null-model toolkit specifically: extract `observables/
partition_similarity.py`, `observables/curvature.py`, and
`scripts/run_phase12_strength_null.py`'s two shuffle functions into a
standalone module with its own tests, independent of `boyko_benchmark`'s
dynamics code. Try it on one external dataset (any weighted graph with a
known degenerate-modularity risk) to confirm it works outside this
project's specific generator functions.

## Kill condition

If the extracted toolkit needs BILUH-specific types (`WeightedGraph`,
this project's `mask`/`weights` convention) baked in at a level that
can't be trivially swapped for a generic adjacency representation,
de-prioritize — the value was in the *methodology*, not this project's
particular data structures.
