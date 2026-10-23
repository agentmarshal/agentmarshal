+++
schema = 2
id = "CR-194"
title = "status shows a task's count of changes_required verdicts, flagged at the project's threshold, and the advisory findings its completion deferred"
scope = [
  "src/agentmarshal/journal/status_view.py",
  "tests/",
  "openspec/changes/status-count-and-deferrals/",
  "openspec/changes/archive/",
  "openspec/specs/finding-lifecycle/",
]
acceptance = [
  "the change status-count-and-deferrals has a proposal, a design.md and a delta spec on the capability finding-lifecycle with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "when the task has at least one `changes_required` verdict, `status <task>` prints one line with the count — counted over every review of the task as the gate's line counts them since CR-168 — and marks it when the count reaches the project's `review.changes_required_threshold` (default 3), the same count and threshold the gate prints; the line blocks nothing",
  "for a task whose `completed` record carries `advisory_dispositions`, `status <task>` lists each `deferred` finding with its reason and, when present, its follow-up task — and that follow-up task's state when the journal holds it, or that the journal does not hold it; `fixed` and `rejected` dispositions are counted on one line, not listed",
  "a task with no `changes_required` verdict and no dispositions prints exactly today's detail view — a test pins it byte for byte, and the example `status` output in docs/sidecar.md stays true without an edit; every value from a record is escaped on display",
  "no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/finding-lifecycle/"]
decisions = ["ADR-0016", "ADR-0022"]
+++

# status shows the count and the deferrals

## Context

ADR-0016 decision 4: `status` shows the task's count of `changes_required`
verdicts, and the gate's output carries the same count, flagged at the
project's threshold (default 3) — the signal to stop and revisit the
contract that a person otherwise has to notice unaided; it blocks nothing.
CR-168 landed the gate's line and CR-151 the threshold key. Decision 1:
`status` and `report` show the deferrals still open; CR-175 landed
`advisory_dispositions` on `completed` and CR-192 the `complete` flags
that write them.

## Objective

A reader of `status` sees how hard a task has been to land and what its
completion left for later.

## Acceptance Criteria

As in the header.

## Non-Goals

- `report` showing deferrals and classes across tasks (a later task).
- Review-by dates on deferrals (pending an operator decision).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
