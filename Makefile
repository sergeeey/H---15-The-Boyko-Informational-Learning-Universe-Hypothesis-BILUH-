.PHONY: install test lint typecheck coverage mutation smoke all

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ tests/ scripts/ configs/

typecheck:
	mypy src/ scripts/ --strict

coverage:
	pytest tests/ --cov=src/boyko_benchmark --cov-report=term-missing --cov-fail-under=90

# Mutation testing targets the critical scientific modules named in
# CLAUDE.md, not the whole codebase — full-codebase mutation is too slow
# to be a routine check.
# Paths corrected 2026-08-12 (Phase 10): the original analysis/* paths
# were Stage B's provisional guess before the package layout was decided
# in Phases 6-9; actual layout is statistics/ + top-level phase_gates.py.
mutation:
	mutmut run \
		--paths-to-mutate=src/boyko_benchmark/observables/spectral_dimension.py,src/boyko_benchmark/dynamics/adaptive.py,src/boyko_benchmark/statistics/finite_size_scaling.py,src/boyko_benchmark/phase_gates.py,src/boyko_benchmark/statistics/cell_statistics.py

smoke:
	python scripts/run_smoke.py --config configs/smoke.yaml

# Full milestone-completion check, per CLAUDE.md's Completion Rule —
# run this and show its output before declaring any milestone done.
all: lint typecheck coverage
