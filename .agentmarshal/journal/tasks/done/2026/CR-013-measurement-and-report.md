# CR-013: measurement records and `agentmarshal report`

Owner: lead
Type: feat
Priority: P1
Created: 2026-07-19
Status: done
Completion-Review: CR-013
Reviewed-Commit: 643515e3a5e8aae95e3e670809a2c5f36c87809a
Target-Branch: master
Merged-Commit: c42a15df19c5b866aee63bafa7d6ce506ae53d00
Completed-At: 2026-07-19T10:30:40Z
Completion-Review-Artifact: .agentmarshal/journal/reviews/2026/CR-013-completion-643515e3a5e8.md
Completion-Review-SHA256: sha256:6d2f00c38bdd2a3c9a4eb3a9e785f4cb90fdb7e4d81fd41af54b488dd18a28aa
Scope:
- .agentmarshal/journal/tasks/open/CR-013-measurement-and-report.md
- src/agentmarshal/
- tests/

## Context

Measurement is the second half of "justified delegation" (founding
brief §2.6): the gate gives a quality floor, measurement gives the
economic meaning — cost per merged task and review cycles per task,
read out of the journal. Every retro so far has recorded a measurement
gap: only launched sessions land in stats, while operator/assistant
work does not; the report must accommodate any channel, not only
vendor sessions.

Design constraints (binding):

- New append-only record type `session`, validated fail-closed like
  existing records; it captures one unit of work against a task.
- All journal I/O through the existing recorder/loader; standard
  library only; `pathlib`; explicit `encoding=`.
- The report derives entirely from journal records — no external state.

## Objective

A `session` record type records attributed work, and
`agentmarshal report` summarizes delegation economics from the journal.

## Acceptance Criteria

- [ ] Record type `session` with fields: `schema`, `record_type`,
      `task`, `created_at`, `tool_version`, `role` (non-empty), `actor`
      (non-empty; e.g. a vendor+model string or a human/assistant
      label), `activity` (one of `implementation`, `review`, `other`),
      `outcome` (non-empty string), and `tokens` (an object with
      integer `input`, `output`, `cache` >= 0; any may be zero to
      denote unmeasured). Validated fail-closed.
- [ ] `agentmarshal record-session --task CR-NNN --role <r> --actor <a>
      --activity <act> --outcome <o> [--input-tokens N] [--output-tokens
      N] [--cache-tokens N]` writes the record for an existing task and
      prints its path; unknown task or malformed values fail closed.
- [ ] `agentmarshal report` prints, from all task records: per task —
      terminal state, number of review records (review cycles) and total
      tokens across its session records; and an overall summary — count
      of tasks by terminal state, total review cycles, total tokens.
      `agentmarshal report --task CR-NNN` prints one task's line.
- [ ] The report attributes tokens across every session channel present,
      including sessions whose actor is a human or assistant label, not
      only vendor sessions (closes the measurement gap).
- [ ] Tests cover: a session record round-trip; each validation failure
      (bad activity, negative token, empty role/actor); a report over a
      repo with a completed task, an abandoned task, review records and
      mixed-actor sessions asserting the per-task and summary numbers;
      `report --task` for one task; a report over an empty journal.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check` and `mypy`
      are green locally and in CI on the reviewed SHA.

## Non-Goals

- No automatic session capture from launchers (recording is explicit
  here; wiring launchers to emit session records is a later slice), no
  cost-in-currency conversion, no ranking/routing, no OTel export.
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
