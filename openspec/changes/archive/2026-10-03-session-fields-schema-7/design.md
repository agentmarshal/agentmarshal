## Context

CR-154 laid down how a field family registers: an entry in
`_FIELD_FAMILIES` ((schema, record type, fields) — the `fields` rule
computes the admitted set from the record's own schema), the shared
validator tables keyed by (record type, field) — `_TEXT_CHAR_LIMITS`,
`_TEXT_BYTE_LIMITS`, `_JSON_BYTE_LIMITS`, `_FORGEABLE_TEXT_FIELDS` — and
the minimum-schema derivation that stamps what the record carries. This
change registers ADR-0022 section 2's session field family through that
mechanism. The time, reset and cost fields of the same ADR section, and
the `record-session` flags that write all of them, are separate tasks.

## Goals

- A session record may carry the six fields under schema 7 and nothing
  older changes.
- Registration follows the CR-154 mechanism exactly.

## Non-Goals

- `started_at`, `ended_at`, `resets_at`, `cost` — a separate task.
- `record-session` command-line flags — a separate task.
- Any reader of the fields (gate, `status`, `next`).

## Decisions

- **The family is one `_FIELD_FAMILIES` entry, `(7, "session",
  _SCHEMA_7_SESSION_FIELDS)` — nothing more admits the fields.** From
  schema 7 a session may carry `commit`, `model`, `trace`, `cli_session`,
  `report_ready` and `fallback_reason`; below 7 the `fields` rule refuses
  them at write and, on read, under the record's own schema — the same
  field-admission rule that gates `usage` from 2 and `reviewed_contract`
  from 5.
- **Each string field registers into `_FORGEABLE_TEXT_FIELDS` keyed
  `("session", field)`; `report_ready` does not.** `commit`, `model`,
  `trace`, `cli_session` and `fallback_reason` are displayed strings, so
  ADR-0022 section 8 puts them under the forgeable-text rule. The
  registration keys on the record type as the mechanism requires — a
  `None` ("every type") key would claim the rule guards these names
  wherever they lie, and no other type carries them. `report_ready` is a
  boolean: the rule refuses a registered non-string fail-closed, so
  registering it would refuse every honest value.
- **No field registers into a length-bound table.** ADR-0022 section 8
  bounds `excerpt`, `payload` and the new record types' `reason` alone —
  none of these fields — so `_TEXT_CHAR_LIMITS`, `_TEXT_BYTE_LIMITS` and
  `_JSON_BYTE_LIMITS` stay empty of this family.
- **The shapes no shared validator covers get one rule of their own,
  `session-fields-7`, bound to 7.** This is the one touch beyond the
  registrations, and it is needed: `commit`'s 40-lowercase-hex shape (the
  `_REVIEWED_COMMIT_PATTERN` the binding fields already measure by), the
  non-empty-string shapes and `report_ready`'s boolean are not any of the
  four shared validators, and a family with no shape check would admit a
  malformed value the spec refuses. The rule is its own table entry bound
  to the schema whose fields it guards — the same binding the shared
  validators and the `coordination` gate take — never folded into the
  schema-1 `session-fields` rule, where a tightening would claim to apply
  to records that predate the family. It registers with the other session
  rules: the `fields` rule stays ahead of it, so a field of the family on
  a session stamped below 7 still gets the unsupported-fields refusal, at
  write and on read alike.
- **`_minimum_schema` raises to 7 on any family field.** One clause —
  `record.keys() & _SCHEMA_7_SESSION_FIELDS` — beside the schema-4 and
  schema-6 clauses it already holds; `session_record_schema`, which feeds
  the same derivation, stays unchanged since a backfilled session carries
  none of these fields.
- **`create_session_record` accepts the six as optional keyword
  arguments**, setting each only when supplied — the `usage` pair's own
  pattern — so a session without the family is byte-identical to today's.

## Risks

- [A schema-6 or older session hand-edited to carry a family field reads
  fine] → it does not: the `fields` rule is bound to 1 and computes the
  admitted set from the record's own schema, so the record is refused on
  read exactly as a schema-1 record carrying `usage` is today.
- [A reader predating schema 7 meets such a session] → intended by
  ADR-0022's upgrade rule: the schema check refuses the record, not a
  field it cannot read.
