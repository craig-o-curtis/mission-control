---
name: quality-check
description: >
  Run all project quality gates: lint, format, typecheck, tests. Report PASS/FAIL per gate.
  Use when user says "quality check", "run checks", "lint and test", "qcheck", "quality",
  or invokes /qcheck.
---

Run all quality gates in order. Report concise PASS/FAIL summary. No raw log dumps.

## Trigger

Auto-activate on: "quality check", "run checks", "lint and test", "qcheck", "quality", "run quality".

## Gates

Run these commands from workspace root. Use `uv run` for all.

### 1. Lint (parallel)

```
uv run ruff check projects/ libs/
```

### 2. Format (parallel)

```
uv run ruff format --check projects/ libs/
```

### 3. Typecheck (sequential — after lint+format)

```
uv run ty check projects/ libs/
```

### 4. Tests (sequential — last)

```
uv run pytest -v projects/*/tests/ libs/*/tests/
```

## Execution

- Run lint + format in parallel (separate terminals).
- Wait for both to complete before running typecheck.
- Run tests last.
- If lint fails, still run format and tests (report all results).
- If format fails, still run typecheck and tests (report all results).
- Never skip gates — report full picture.

## Output

**PASS case:** single line — `Lint: PASS | Format: PASS | Typecheck: PASS | Tests: PASS`

**FAIL case:** one line per failed gate, quote shortest decisive error only. No full stack traces unless asked.

Examples:
- `Lint: FAIL — projects/missions_api/missions.py:42: E501 line too long (120 > 88)`
- `Format: FAIL — projects/missions_api/models.py not formatted`
- `Typecheck: FAIL — projects/missions_api/missions.py:15: error: unused import "Response"`
- `Tests: FAIL — projects/missions_api/tests/test_missions.py::TestReadMissions::test_filter_By_query_Params FAILED (assert 3 == 2)`

## Rules

- No tool-call narration ("I'm running lint now...").
- No decorative tables, emoji, or status phrases.
- Quote errors exact. Technical terms exact.
- If all pass, say nothing more than the summary line.
- If any fail, list failures only. No "next steps" unless asked.
