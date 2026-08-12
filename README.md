# boyko-benchmark

A falsification-first computational benchmark testing whether adaptive
weighted-network dynamics can generate a stable, low-dimensional
geometric-phase candidate that survives finite-size scaling and is absent
in matched negative controls.

**This project does not attempt to prove that the Universe is a neural
network.** It tests one narrow, falsifiable claim about one specific
adaptive rule on one specific class of dynamical graphs. Read
[`CLAUDE.md`](CLAUDE.md) — Scientific Boundary section — before assuming
otherwise.

## Status

**Phase 0 (scientific contract) is closed.** No simulation code exists yet.
Current stage: repository infrastructure (this commit's contents). Next:
Phase 1 (package structure, seed manager, graph primitives) under strict
TDD.

## Start here

1. [`CLAUDE.md`](CLAUDE.md) — development protocol, scientific boundary,
   required arms/observables/gates, quality gates.
2. [`docs/assumptions.md`](docs/assumptions.md) — every unresolved
   ambiguity from the source planning document and the default chosen for
   each, with evidence markers.
3. [`docs/novelty_check.md`](docs/novelty_check.md) — prior-art scan;
   what novelty this project can and cannot claim.
4. [`docs/mathematical_contract.md`](docs/mathematical_contract.md) — the
   frozen formulas everything else must satisfy.
5. [`docs/estimand.md`](docs/estimand.md) — population, intervention,
   comparators, MCID, identifiability.
6. [`docs/falsification_gates.md`](docs/falsification_gates.md) — the
   G1–G6 verdict machine and terminology lock.
7. [`.claude/memory/decisions.md`](.claude/memory/decisions.md) — full
   review history (3 DDD skeptic cycles, every finding and response).

## Development

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

pytest tests/ -v --tb=short
ruff check src/ tests/
mypy src/ --strict
pytest tests/ --cov=src/boyko_benchmark --cov-report=term-missing --cov-fail-under=90
```

Strict vertical TDD — one failing test, minimum implementation, refactor.
See `CLAUDE.md` § Development Method for the full protocol and the
anti-cheating rules that go with it.
