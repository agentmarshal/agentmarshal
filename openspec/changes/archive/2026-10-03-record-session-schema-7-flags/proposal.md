## Why

CR-160 gave the session record its schema-7 fields (ADR-0022 section 2):
`commit` — the commit the implementer run produced (ADR-0018 decision 3),
`model`, `trace` and a separate `cli_session` (proposal 042),
`report_ready` (proposal 041) and an optional `fallback_reason`
(ADR-0018). The harness records sessions with `record-session`; until it
can pass these, nothing writes them.

## What Changes

- `record-session` accepts `--commit <rev>`, `--model <name>`,
  `--trace <link>`, `--cli-session <id>`, `--report-ready` and
  `--fallback-reason <text>`, each optional, writing the matching
  schema-7 session field. A session recorded with any of them stamps
  schema 7, as any record carrying the family does; a session recorded
  with none keeps the schema it had.
- `--commit` resolves any revision git accepts to the full 40-character
  id with `git rev-parse --verify <rev>^{commit}` in the repository the
  work is in — the host when the journal is a sidecar — and refuses a
  revision git cannot resolve with a message naming it.
- A flag value the record rules refuse — an empty or whitespace-only
  string, a forgeable character — is refused with the record rule's
  message and no record is written. `--outcome` stays free text,
  unchanged.

## Capabilities

- modified: `session-activity`

## Impact

`record_session` gains the six as optional keyword arguments and passes
them to `create_session_record`, which already takes them. `--commit`
resolution reuses the gate's `_resolve_commit` against
`placement.host_root` — the root `review --commit` and
`complete --commit` already resolve against — with `require_host` only
when the flag is given, so a sidecar without the flag is untouched. The
time, reset and cost flags of the same ADR section, and `--if-missing`,
are later tasks.
