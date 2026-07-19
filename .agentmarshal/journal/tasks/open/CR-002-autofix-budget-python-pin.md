# CR-002: enable bounded review-autofix loops and pin the dev Python floor

Owner: lead
Type: chore
Priority: P2
Created: 2026-07-19
Status: in_review
Scope:
- .agentmarshal/journal/tasks/open/CR-002-autofix-budget-python-pin.md
- .agentmarshal/project.json
- .python-version

## Context

CR-001 ran with the default review-autofix budget of 0, so every
`changes_required` verdict stopped the managed runbook for a manual
operator fix cycle. The fix→re-review loop itself proved sound when
driven manually; giving the runbook a small bounded budget removes that
operator toil while keeping the loop finite.

Separately, the supported Python range is declared as `>= 3.12` but no
floor is pinned for development environments, so local runs use whatever
interpreter is ambient while CI runs 3.12.

## Objective

The managed runbook retries `changes_required` reviews autonomously
within a bounded budget, and development environments default to the
minimum supported Python.

## Acceptance Criteria

- [ ] `.agentmarshal/project.json` sets
      `"agmake": {"implementation_mode": "managed", "review_autofix_loops": 2}`.
- [ ] `./agentmarshal/bin/agentmarshal validate` passes with the updated
      config.
- [ ] A freshly generated agmake runbook manifest records
      `review_autofix_loops: 2`.
- [ ] `.python-version` contains `3.12`, matching the CI job image and
      the declared minimum in `pyproject.toml`; `uv sync --locked` and
      the full check suite pass under it.

## Non-Goals

- No change to `pyproject.toml` (`requires-python` stays `>= 3.12`).
- No runbook/template changes; the budget is host configuration only.
