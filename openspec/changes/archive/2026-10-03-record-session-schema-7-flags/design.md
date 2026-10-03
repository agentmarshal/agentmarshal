## Context

CR-160 registered the schema-7 session field family —
`commit`, `model`, `trace`, `cli_session`, `report_ready` and
`fallback_reason` — and `create_session_record` already accepts them as
optional keyword arguments. What is missing is the writer: the harness
records sessions with `record-session`, which today takes only identity,
activity, outcome, tokens and the usage pair.

## Goals

- `record-session` writes every schema-7 session field the record
  carries, one optional flag each.
- `--commit` takes any revision git accepts and stores the resolved
  full id, resolved in the repository the work is in — the host in a
  sidecar.
- Nothing existing changes: no flag, no field, schema 3 — or 6 for
  coordination — as before.

## Non-Goals

- `--started-at`, `--ended-at`, `--resets-at`, the cost flags and
  `--if-missing` — the ADR's remaining record-session surface, a later
  pair of tasks.
- Any reader of the fields.

## Decisions

- **`record_session` gains the six as optional keyword arguments** and
  passes them straight to `create_session_record` — the `usage` pair's
  own pattern. The record rules stay the only judge of a value: the
  command layer adds no check of its own, so a refused value — an empty
  or whitespace-only string, a non-boolean where a boolean belongs, a
  character that could forge a rendered line — is refused with the
  record rule's message and nothing is written.
- **`--commit` resolves in the CLI, with the gate's `_resolve_commit`,
  against `placement.host_root`.** The flag accepts any revision git
  accepts — `git rev-parse --verify <rev>^{commit}` — while the field
  holds exactly 40 lowercase hex, so resolution is a presentation-layer
  step that belongs where the flag lives, and `record_session` stays
  free of git. `placement.host_root` is the root `review --commit` and
  `complete --commit` already resolve against: the project itself for an
  embedded journal, the host for a sidecar. The placement is resolved
  with `require_host` only when `--commit` is given — the sidecar
  without the flag has no host fact to read and is asked for none.
- **`--report-ready` is a presence flag** (`store_true`, default
  `None`): it asserts the run's report was finished, and its absence
  asserts nothing, so a session without it writes no `report_ready` at
  all and keeps its schema.
- **Refusals keep their existing messages.** A revision git cannot
  resolve fails inside `_resolve_commit` with a message naming the
  revision; a value the record rules refuse surfaces through
  `SessionRecordError` with the rule's own message, and both write
  nothing. `--outcome` is untouched.

## Risks

- [A sidecar is asked for its host when none is reachable] → only when
  `--commit` is given: `require_host` is conditional on the flag, and
  without it the command reads no host fact.
- [`--commit` given a revision naming a tag or other non-commit] →
  `^{commit}` peels it to the commit, which is the value the field
  wants; a rev that cannot peel is refused naming it.
