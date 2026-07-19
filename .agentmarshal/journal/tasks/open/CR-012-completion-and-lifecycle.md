# CR-012: completion and lifecycle records — closing the loop

Owner: lead
Type: feat
Priority: P1
Created: 2026-07-19
Status: in_review
Scope:
- .agentmarshal/journal/tasks/open/CR-012-completion-and-lifecycle.md
- src/agentmarshal/
- tests/

## Context

The gate (CR-011) verifies a candidate; this slice records the terminal
lifecycle outcomes and closes the loop end-to-end. Per ADR-0004 state is
a projection, so completion and abandonment are append-only records, not
directory moves. Per the founding brief completion is automated on a
passing merge — the operator does not run a separate transaction — so the
`complete` verb runs the gate itself and only records completion when the
gate passes. This is the milestone where the v2 loop runs
contract → review → gate → completion without a manual completion step.

Design constraints (binding):

- Reuse `run_gate` (CR-011) inside `complete`; do not duplicate any
  check. Completion records only when the gate passes.
- New append-only record types `completed` and `abandoned`, validated
  fail-closed like existing records; extend the projection's explicit
  mapping: `completed` -> `done`, `abandoned` -> `abandoned`.
- Projection rules (fail-closed): a task with a `completed` record is
  `done`; with an `abandoned` record is `abandoned`; a record after a
  terminal record, or both terminal records, is an error.
- Standard library only; all journal I/O through existing loaders and
  the recorder.

## Objective

`agentmarshal complete` gates a candidate and records completion on
success; `agentmarshal abandon` records abandonment; `status` projects
both terminal states.

## Acceptance Criteria

- [ ] Record types `completed` (fields: schema, record_type, task,
      created_at, tool_version, completed_commit — 40 lowercase hex) and
      `abandoned` (same minus commit, plus a non-empty `reason`), both
      validated fail-closed.
- [ ] `agentmarshal complete --task CR-NNN --commit <sha> --base <ref>
      [--pipeline-sha <sha>]` runs the gate; on a pass it writes the
      `completed` record and prints its path and "completed"; on a gate
      refusal it prints the gate's violation lines, writes nothing, and
      exits non-zero.
- [ ] `agentmarshal abandon --task CR-NNN --reason <text>` writes the
      `abandoned` record for an open task; refuses a task that is
      already terminal; writes nothing on failure.
- [ ] Projection: `completed` -> `done`, `abandoned` -> `abandoned`; a
      record following a terminal record, or two terminal records, is a
      fail-closed error; `status` shows the terminal state and lists the
      terminal record in detail view.
- [ ] Tests cover: complete on a passing candidate (record written,
      status `done`, end-to-end from open through review to completion);
      complete refused when the gate refuses (nothing written);
      abandon on an open task (status `abandoned`); abandon refused on a
      terminal task; the projection errors (record after terminal, both
      terminal records); a full loop test: open → implement commit →
      submit-review approved → complete passes → status done.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check` and `mypy`
      are green locally and in CI on the reviewed SHA.

## Non-Goals

- No provider/MR/CI-job integration (the gate and completion are library
  and CLI here; wiring them into this repository's own governance is the
  self-hosting milestone), no post-merge graph audit beyond the
  projection, no measurement records (next slice).
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
