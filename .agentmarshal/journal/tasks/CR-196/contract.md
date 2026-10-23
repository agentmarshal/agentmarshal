+++
schema = 2
id = "CR-196"
title = "report shows a task's lead time and its phases — opened, first implementer start, first review, approval, completion — and the review rounds, unknown where a record cannot say"
scope = [
  "src/agentmarshal/journal/report.py",
  "docs/sidecar.md",
  "tests/",
  "openspec/changes/report-lead-time/",
  "openspec/changes/archive/",
  "openspec/specs/session-activity/",
]
acceptance = [
  "the change report-lead-time has a proposal, a design.md and a delta spec on the capability session-activity with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal report --task <id>` shows the task's phases: opened (the `opened` record's time), the first implementer session's `started_at`, the first review, the first approving review, completion — and the durations between consecutive known boundaries; a boundary a record cannot supply (an implementer session with no `started_at`, a task not yet reviewed, approved or completed) is shown as unknown or not yet, never substituted with a record's `created_at` (ADR-0019 decision 2)",
  "the same view lists the task's review rounds in order with each review's verdict and the time since the previous review (or since the first implementer start for the first), unknown where a boundary is unknown",
  "`agentmarshal report` without `--task` adds, after what it prints today, an aggregate over completed tasks: the count of tasks with a fully known lead time and the median and maximum lead time among them, and the count of tasks whose lead time is unknown — never averaging an unknown in",
  "what `report` prints today stays first and unchanged, which a test pins; the example `report --task` output in docs/sidecar.md shows exactly what the command prints for that example (its record times included); every value from a record is escaped on display; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/session-activity/"]
decisions = ["ADR-0019", "ADR-0022"]
+++

# report shows lead time and its phases

## Context

ADR-0019 decision 2: `report` shows, per task and in aggregate, opened →
the start of the first implementer session → the first review → approval →
completion, and the review rounds with their durations; for a session
written before the decision — one carrying no start and end — the boundary
it cannot supply is shown as unknown, never substituted with `created_at`,
because the write time would print a wrong number confidently. CR-176
landed `started_at`/`ended_at` on sessions and CR-188 the `record-session`
flags that write them.

## Objective

How long a task took, and where the time went, can be read from the
journal — and where the journal cannot say, the report says so.

## Acceptance Criteria

As in the header.

## Non-Goals

- Money per currency, refused checks and finding classes in `report`
  (later tasks).
- Business-hours or wall-clock adjustments; durations are plain elapsed
  time between recorded instants.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
