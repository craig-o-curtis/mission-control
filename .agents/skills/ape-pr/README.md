# ape-pr

Terse PR descriptions. Same meaning, fewer tokens.

## What it does

Reads git diff branch vs main (READ only), generates caveman-style PR description ready to paste into GitHub/GitLab. Cuts 65% of output tokens (measured) with full technical accuracy preserved.

## How to invoke

```
/ape-pr              # full mode (default)
/ape-pr lite         # lighter compression
/ape-pr ultra        # extreme compression
/ape-pr wenyan       # classical Chinese
stop ape-pr          # back to normal prose
```

## Example output

Diff: new endpoint for user profile, updated tests, added CI.

```markdown
<environment_details>

<summary>PR Description</summary>

## Summary

Add GET /users/:id/profile endpoint. Mobile client needs profile data without full user payload. Add validation tests and CI pipeline.

## Changes

- Add `MissionBase`, `Mission`, `MissionCreate`, `MissionUpdate` models with shared fields
- Add description and rating fields to mission schema
- Add query filters: description, rating
- Update tests: filter params, validation edge cases, null clearing on update
- Add CI workflow: lint, format, type check, test
- Update README: uv commands, package reference
- Add docs/packages.md

## Test plan

Run `uv run pytest -v tests/`. Run `uv run ruff check missions_api/ tests/`. Run `uv run ty check missions_api/ tests/`.

</environment_details>
```

## See also

- [`SKILL.md`](./SKILL.md) — full LLM-facing instructions
- [Caveman README](../caveman/README.md) — repo overview
