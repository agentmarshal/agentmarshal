+++
schema = 2
id = "CR-168"
title = "The gate's output carries the task's count of changes_required verdicts, flagged at the project's threshold"
scope = [
  "src/agentmarshal/journal/gate.py",
  "tests/",
  "docs/quickstart.md",
  "docs/sidecar.md",
  "openspec/changes/gate-changes-required-count/",
  "openspec/changes/archive/",
  "openspec/specs/gate-lanes/",
]
acceptance = [
  "the change gate-changes-required-count has a proposal, a design.md and a delta spec modifying gate-lanes (ADR-0016 decision 4 names this revision): an ADDED requirement for the count line and, if the default-run requirement's text needs it, a MODIFIED one with its exact header; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "on the implementation lane, in both placements, the gate prints one line carrying the task's count of `changes_required` verdicts over the whole task (every review record of the task's candidates, whatever commit it names — a review bound to a research finding, ADR-0009, is not counted) and the project's threshold from `review.changes_required_threshold` (default 3, read through the settings module of CR-151), and marks the line when the count has reached the threshold; the wording is stated in design.md and the line is the tool's own text",
  "the line never adds a violation, never changes the exit status and never blocks a merge; a malformed threshold setting is reported on the line and does not fail the run",
  "the gate fixtures for the implementation lane are regenerated through the test's explicit update path and the fixture diff is exactly the new line; the embedded journal-only lane prints no count line and its fixture is unchanged; in a sidecar there is no journal-only lane (ADR-0008 decision 2), so the sidecar case whose candidate touches only the journal runs the implementation lane and its fixture gains the line too",
  "every gate transcript the documentation shows and a test pins (docs/quickstart.md's main path) and the sidecar transcript in docs/sidecar.md show the new line, and the full CI sequence passes",
]
documents = ["openspec/specs/gate-lanes/"]
+++

# CR-168: the changes_required count in the gate's output

## Context

ADR-0016 decision 4: `status` shows the task's count of `changes_required`
verdicts, and the gate's output gains a line carrying the same count,
flagged when it reaches the project's threshold (default 3). It blocks
nothing — it is the signal to stop and revisit the contract. The new line
revises gate-lanes, whose default-run requirement pins the transcript by
fixtures (CR-146); this task changes those fixtures on purpose and names it.
CR-151 reads the threshold from project.json.

## Objective

Whoever reads the gate's output sees how many times the task was returned,
and when that has reached the threshold.

## Acceptance Criteria

As in the header.

## Non-Goals

- The count in `status` (a separate task).
- Counting since the last amendment — that is `next`'s count (ADR-0023); the
  gate and status count over the whole task.
