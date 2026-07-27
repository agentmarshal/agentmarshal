+++
schema = 1
id = "CR-020"
title = "Gate completion lane base-state check"
scope = ["src/agentmarshal/journal/gate.py", "tests/test_gate.py"]
acceptance = []
+++

# CR-020: Gate completion lane base-state check

## Context

Self-hosting flip (2026-07-27) surfaced a real gap: the gate's first
check reads the task state from the candidate's working tree, so a
completion transaction — which appends a `completed`/`abandoned` record
and thus projects the task to a terminal state — fails the
`task is open` check and the completion MR has to be merged with a SKIP
override. The gate must accept a legitimate open→terminal transition
while still refusing work merged onto an already-closed task.

## Objective

Base the "task is open" gate check on the task's state at the base tree
(before the candidate), so opening, implementation and completion
candidates all pass, while a candidate against an already-closed task is
still refused — without a SKIP override.

## Acceptance Criteria

- [ ] The gate no longer refuses a completion candidate (an open task at
      base whose candidate appends exactly a terminal record); the
      journal-only completion lane passes cleanly.
- [ ] The gate still refuses a candidate whose task is already closed at
      the base tree (a `completed`/`abandoned` record present on the base
      for that task), reported as a clear FAIL.
- [ ] Opening (task absent at base) and implementation (task open at
      base, no terminal added) candidates still pass exactly as before;
      `load_task_status` still validates the post-candidate journal is
      well-formed and fails closed on an inconsistent projection.
- [ ] The check derives "closed at base" from the base tree the gate
      already reads (no trust in the candidate side for this decision).
- [ ] Tests cover: completion candidate passes; already-closed task
      candidate refused; opening and implementation candidates still
      pass; the existing gate suite stays green.
- [ ] `uv run agentmarshal validate`, `pytest`, `ruff check`,
      `ruff format --check`, `mypy` green locally and in CI.

## Non-Goals

- No change to the other eight gate checks, the journal model, or
  `am-merge`. Routing completion MRs is unnecessary once the gate accepts
  them; `am-merge` stays the single authority path.

