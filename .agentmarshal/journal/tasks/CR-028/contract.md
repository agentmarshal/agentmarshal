+++
schema = 1
id = "CR-028"
title = "measurements accrue post-terminal: session records after a closed task"
scope = ["src/agentmarshal/journal/status.py", "src/agentmarshal/journal/gate.py", "tests/test_gate.py", "tests/test_complete.py"]
acceptance = []
+++

# CR-028: measurements accrue post-terminal

## Context

ADR-0005 Decision 3: measurements are not lifecycle. A `session`
(measurement) record may be appended to a task in any state — including a
terminal one — because it projects to no lifecycle state, while lifecycle
records (`opened`, `review`, `completed`, `abandoned`) stay immutable once
a task is terminal. Recording economics at or after completion, and the
sanctioned retroactive backfill (a later CR), both depend on this.

Today two checks forbid it. The status projection refuses *any* record
after a terminal one, so `load_task_status` — which the gate runs on the
post-candidate journal — raises. And the gate's base-state check refuses
*any* candidate merging onto a task already closed at base. Both must
admit a measurements-only append while still refusing lifecycle changes.

## Objective

Let `session` records accrue after a task's terminal record, through the
normal validating status projection and merge gate, without weakening the
immutability of the lifecycle or opening any non-measurement path onto a
closed task.

## Acceptance Criteria

- [ ] `project_status` admits a `session` record that follows a terminal
      record (the state stays `done`/`abandoned`); it still rejects any
      lifecycle record (`opened`, `review`, `completed`, `abandoned`)
      after a terminal record, and still rejects a second terminal record.
- [ ] The gate admits a candidate whose changes are journal-only and whose
      added records are all `session` records, even when the task is
      closed at base — a distinct "measurements-only" pass line. It still
      refuses a candidate that is closed at base and adds any non-session
      record or any non-journal file (the existing "already closed at
      base" refusal).
- [ ] The gate's other invariants are unchanged for the measurements lane:
      append-only (no record tampering), added records valid, no path
      collisions, and lifecycle consistency all still run and still refuse
      violations. Review is not required (journal-only lane).
- [ ] Tests: `project_status` accepts session-after-terminal and still
      rejects lifecycle-after-terminal; the gate passes a session-only
      append to a task closed at base and still refuses a completed-record
      or code-file candidate on a closed task.
- [ ] `uv run agentmarshal validate`, pytest, ruff, and mypy stay green.

## Non-Goals

- No capture-policy config, no backfill tool, no forward-capture flip —
  later CRs. CR-028 only makes the projection and gate admit post-terminal
  measurements; it does not itself write any session record.
- No change to how sessions are recorded (`record-session`) or measured.
- No new record type and no schema change (CR-027 already added schema 2).
