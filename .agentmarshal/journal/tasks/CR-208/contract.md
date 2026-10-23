+++
schema = 2
id = "CR-208"
title = "status says which implementer session produced the commit the latest review judged, and how that session ended"
scope = [
  "src/agentmarshal/journal/status_view.py",
  "tests/",
  "openspec/changes/status-candidate-session/",
  "openspec/changes/archive/",
  "openspec/specs/session-activity/",
]
acceptance = [
  "the change status-candidate-session has a proposal, a design.md and a delta spec on the capability session-activity with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`status <task>` prints one line for the commit the task's latest review judged (`reviewed_commit`): the implementer session whose `commit` equals it — its id, `actor`, `outcome`, and `report_ready` when present — and, when the outcome is not `implemented`, says so plainly; when several sessions name that commit, the latest is shown and the count of the others is given",
  "when no implementer session names the reviewed commit, or the task has no review, `status` prints exactly what it prints today — a candidate produced by a runner that wrote no session is shown as before (proposal 036's disposition); a test pins the detail view of such a task byte for byte",
  "every value from a record is escaped on display; nothing is refused or blocked — this is the read side only; the refusal in `review` and the gate is a later task",
  "no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/session-activity/"]
decisions = ["ADR-0018", "ADR-0022"]
+++

# status names the session behind the reviewed commit

## Context

Proposal 036: a review can approve a candidate whose implementer run was
interrupted, because nothing linked the commit to the run. Its disposition
accepts the session's `commit` field (landed in CR-160, written by
`record-session --commit` since CR-166) and, with it, the `status` display
of which session produced the candidate head and how that session ended —
the read side of the link; the refusal in `review` and the gate, with the
operator's override, comes with a later record schema (operator decision
of 2026-10-23). When no session names the commit, behaviour is as today.

## Objective

A reader of `status` can see whether the commit under review came from a
run that finished.

## Acceptance Criteria

As in the header.

## Non-Goals

- Refusing anything in `review` or the gate (a later task, with the
  override under record schema 8).
- Showing sessions for commits other than the latest reviewed one.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
