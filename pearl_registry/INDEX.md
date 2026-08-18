# Pearl Registry

Per `~/.claude/rules/falsification-ladder.md`: side-findings that don't
fit the current experiment's REJECT/ARCHIVE/PROMOTE verdict shape, but
are real, testable, and worth not losing. Never delete an entry —
update its status (`pending`/`verified`/`refuted`) when checked.

| date | source_experiment_id | observation | falsifiable_prediction | impact_score | trigger_condition | next_check | status |
|---|---|---|---|---|---|---|---|
| 2026-08-18 | A70 (`docs/v5_spec.md` Sec15, Geometry Signal Audit) | On the UNDAMAGED T7 lattice, the top-`D`-by-`C_ij` candidates show `P(d*=r \| top-D)=0` for EVERY ODD true distance `r` (1,3,5,7,9,11) and nonzero only at even `r`, reproducibly across all 10 trials — a structured, non-random pattern, not evidence of a bug | If this is a genuine bipartite-lattice parity effect (periodic cubic lattice is bipartite by coordinate-sum parity; nearest-neighbor-only coupling under coherent unitary evolution may impose a parity structure on which pairs achieve high `\|C_ij\|`), then restricting the "near" positive class to an EVEN true distance (e.g. `d*=2`, same-sublattice near neighbors) instead of `d*=1` should show `AUROC`/`Recall@D` clearly ABOVE chance — even though `[A70]`'s own `d*=1` framing showed none | 6 | Before designing any future geometry-signal test that needs to choose a "near"/positive-class distance definition, or if `[A70]`'s World-A (no signal) conclusion is ever challenged or revisited | Before any follow-up to `[A70]` is pre-registered (no fixed calendar date — this project's own pace is session-driven, not calendar-driven; check at the START of that follow-up's design, not deferred indefinitely) | pending |
