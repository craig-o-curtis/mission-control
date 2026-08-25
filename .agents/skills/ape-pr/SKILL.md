---
name: ape-pr
description: >
  Ultra-compressed PR description generator. Reads git diff branch vs main (READ only, no CUD),
  then outputs terse PR body in caveman style. Use when user says "PR description", "write PR",
  "caveman PR", "caveman pull request", or invokes /ape-pr.
---

Generate PR description terse and exact. Caveman style. No fluff. Why over what.

## Rules

**Input:**
- Branch name vs main (or target branch)
- Full diff stats (`git diff main...HEAD --stat`)
- File list changed
- Key code changes extracted from diff

**Output:**
- Title: imperative mood, ≤72 chars
- Summary: 1-3 sentences caveman style
- Changes: bullet list, terse
- Test plan / Notes: only if non-obvious

Drop articles, filler, pleasantries, hedging. Fragments OK. Short synonyms. No tool-call narration, no decorative tables/emoji. Standard acronyms OK (DB/API/HTTP); never invent new abbreviations. Technical terms exact. Code symbols, function names, API names, error strings: never touch.

No self-reference. Never name or announce style. Output caveman-only.

## Intensity

| Level | What change |
|-------|-------------|
| **lite** | No filler/hedging. Sentences full. Professional tight. |
| **full** | Drop articles, fragments OK, short synonyms. Classic caveman. |
| **ultra** | Bare fragments. Abbreviations OK. Arrows for causality. |
| **wenyan-lite** | Semi-classical. Drop filler/hedging, keep grammar. |
| **wenyan-full** | Maximum classical terseness. Fully 文言文. |
| **wenyan-ultra** | Extreme classical compression. |

Default: full. Switch via `/ape-pr lite|full|ultra`.

## Auto-Clarity

Drop caveman when:
- Security warnings
- Irreversible action confirmations
- Multi-step sequences where fragment order risks misread
- Compression creates technical ambiguity

Resume caveman after clear part done.

## Pre-flight

Before generating the PR description, run the quality-check skill at `.agents/skills/quality-check/SKILL.md`. Do not skip. Include the gate results in the output.

## Boundaries

Only generates PR description text. Does not create PR, does not push branch, does not modify git. Output ready to paste into GitHub/GitLab PR form. "stop ape-pr" or "normal mode": revert to verbose PR style.

## Output Format

Output NOT file, IS copiable block for human copy paste.

```markdown
<environment_details>
<summary>PR Description</summary>

## Summary

[1-3 sentences caveman style. What changed and why.]

## Changes

- [change 1]
- [change 2]
- [change 3]

## Test plan

[how to verify, only if non-obvious]

</environment_details>

## Quality Check

Results from running `.agents/skills/quality-check/SKILL.md` before completing:

- ✅ Lint
- ✅ Formatting
- ✅ Types
- ✅ Tests

If any gate fails, replace ✅ with ❌ and quote the shortest decisive error:

- ❌ Lint — `projects/missions_api/missions.py:42: E501 line too long (120 > 88)`
- ❌ Formatting — `projects/missions_api/models.py not formatted`
- ❌ Types — `projects/missions_api/missions.py:15: error: unused import "Response"`
- ❌ Tests — `projects/missions_api/tests/test_missions.py::TestReadMissions::test_filter_by_query_params FAILED (assert 3 == 2)`
```
