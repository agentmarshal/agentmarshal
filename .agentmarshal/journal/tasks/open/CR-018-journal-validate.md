# CR-018: journal-wide validate command

Owner: lead
Type: feat
Priority: P2
Created: 2026-07-27
Status: open
Scope:
- .agentmarshal/journal/tasks/open/CR-018-journal-validate.md
- src/agentmarshal/
- tests/

## Context

Self-hosting cutover (parallel/shadow, Variant 1) needs a v2 governance
command for the CI job that today runs the v1 `agentmarshal validate`.
The v2 CLI has no `validate`: it has `doctor` (project setup health) and
`gate` (per-candidate). Neither asserts that the whole journal is
well-formed. This slice adds `agentmarshal validate`: a deterministic,
read-only, journal-wide integrity check that fails closed on any
malformed contract, invalid record, inconsistent projection, or record
collision — the command a governance CI job runs on every push.

It reuses the existing validators rather than reimplementing them:
contract parsing (`parse_contract_text`), record schema validation
(`validate_record_content`), status projection (`load_task_status` /
`project_status`, which already reject record-after-terminal and
duplicate `opened`), and the record reader (`read_records`). No change
to the gate, the journal model, or gitflic-ci (the CI switch is the
later flip, out of scope).

## Objective

`agentmarshal validate` verifies every task in the journal and exits
non-zero on the first class of violation it finds, reporting each.

## Acceptance Criteria

- [ ] `agentmarshal validate` discovers every task under the journal
      (`tasks/**`), and for each: parses its contract, validates every
      record's content, and projects its status; it also detects record
      path/id collisions across tasks. Read-only; touches no files.
- [ ] Exit code is 0 with a per-task OK summary when the journal is
      clean, and non-zero with a clear per-violation message (task id +
      reason, no traceback) when any contract fails to parse, any record
      is invalid, any projection is inconsistent, or any record path/id
      collides. Non-UTF-8 or unreadable journal content is a controlled
      failure, never a traceback.
- [ ] Must be run inside an initialized project; a clear message and
      non-zero exit otherwise (mirroring the other subcommands).
- [ ] The check logic lives in a validate module and is unit-testable
      independently of the CLI, reusing existing validators (no
      duplicated parsing/validation/projection logic).
- [ ] Tests cover: a clean multi-task journal passes; a malformed
      contract, an invalid record, an inconsistent projection
      (record-after-terminal or duplicate opened), and a record
      collision each fail closed with the expected message; running
      outside a project fails closed.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check`, `mypy` green
      locally and in CI on the reviewed SHA.

## Non-Goals

- No change to `gitflic-ci.yaml` (switching the CI governance job to this
  command is the self-hosting flip, a separate operator step).
- No change to any gate check, the journal model, or record schemas.
- No new validation rules beyond composing the existing validators; this
  is an aggregator, not a new policy.
