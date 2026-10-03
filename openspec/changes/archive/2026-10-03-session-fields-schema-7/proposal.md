## Why

ADR-0022 section 2 adds six fields to the session record under schema 7:
`commit` (the commit the implementer run produced, ADR-0018 decision 3),
`model` (ADR-0018; the vendor stays `usage.provider`), `trace` and a
separate `cli_session` (proposal 042; two fields by the operator's decision
on revision 3), `report_ready` (proposal 041) and an optional
`fallback_reason` (ADR-0018; shown, never verified). CR-154 made schema 7
known and laid down the registry a field family registers through — field
admission by schema, validator tables keyed by record type and field, and
the minimum-schema derivation. A session today cannot yet say what the run
produced or with what.

## What Changes

- A session record may carry, from schema 7 only: `commit` (40 lowercase
  hex), `model`, `trace`, `cli_session`, `report_ready` (a boolean) and
  `fallback_reason`. Each is optional; each string field passes the
  forgeable-text rule registered for that record type and field; ADR-0022
  section 8 bounds no length for them, so none is bounded.
- Any of the fields on a session stamped below 7 is refused at write and,
  on read, by the field-admission rule of the record's own schema — as the
  other schema-gated fields are. A writer carrying any of them stamps 7
  through the minimum-schema derivation; a session without them stamps
  what it stamps today — 3, or 6 for coordination.
- `create_session_record` accepts the six as optional keyword arguments.

## Capabilities

- modified: `session-activity`

## Impact

No other record type changes and the gate's fixtures are unchanged. The
fields are write-side only for now: no reader of them exists yet — the
`record-session` flags that set them and the reports that read them are
separate tasks, as are the time, reset and cost fields of the same ADR
section.
