## Context

`records.py` has a single `_validate_record` that every path calls —
`validate_record_for_write` on the write side, `read_records` and
`validate_record_content` on the read side. Inside it the schema-bound checks
are scattered: field-family admission (`_SCHEMA_2_FIELDS`,
`_SCHEMA_2_SESSION_FIELDS`, `_SCHEMA_5_FIELDS`), the `reviewed_contract`
gate, the finding-binding gate, the `schema >= 2` provenance gate, the
coordination-activity gate inside `_validate_session_record` — while every
writer picks its `schema` literal by hand.

ADR-0015: (1) write-time checks are the current rules, read-time checks are
the rules of the record's own schema; (2) writers stamp the minimum schema;
(6) existing checks apply from schema 1; (7) a table "rule → the schema it
applies from" lives in validation, and a test catches a rule without its
number.

## Goals

- One table in `records.py` maps every read-time rule to the schema it
  applies from; a rule cannot be checked without an entry.
- Read paths apply the record's own schema's rules; the write path applies
  all rules.
- One derivation stamps the minimum schema in every writer.
- Zero observable change for lawful records: same stamped numbers, same
  accept/refuse answers, same messages.

## Non-Goals

- Schema 7 and its fields/record types (ADR-0022 tasks).
- Escaping on display (ADR-0015 decision 5 — a later task; refusal at write
  stays in place).
- The contract header's and extension manifest's parallel rule (decision 8).
- Changing which records are accepted or refused today.

## Decisions

- **A rule is a named predicate plus a table entry, in two structures.** A
  decorator `@_rule("name")` registers each check into the ordered `_RULES`
  registry (name → predicate); `_RULE_FROM_SCHEMA` (name → schema) is the
  table the ADR asks for. Two structures, deliberately: a rule can be
  registered without a table entry, and that gap is the bug the test must
  catch — with a single structure carrying the schema, the gap cannot exist
  and the test would prove nothing. Validation consults the table by name on
  the read side, so the completeness test is simply
  `set(_RULES) == set(_RULE_FROM_SCHEMA)` — it fails the moment a rule is
  checked without an entry (or an entry names no rule). A lookup that comes
  back empty is fail-closed on read: an unregistered rule is skipped, never
  silently applied to history.
- **Read and write share one iteration; the record's own schema selects the
  rules.** `_validate_record(record, *, for_write)` runs the registry in
  order. The first registered rule is the schema check; once it has run, the
  record's number is known, and on the read side a rule whose bound schema
  exceeds it is skipped. On the write side the flag short-circuits the
  filter entirely — every rule runs on every record, which is exactly
  today's single-function behaviour. No rule list is duplicated for the two
  sides; the side is one parameter, and the gate-bound rules keep their
  numbers in the same table that drives both.
- **Each conditional check keeps its own condition inside its predicate.**
  The write path must not start refusing records it accepted today: a
  schema-1 record is still writable (a test pins it), so the provenance
  predicate keeps its `schema >= 2` guard — the rule's text is "for records
  of schema 2 and above, `source` must name a capture", and the table's 2
  says from which schema a reader applies it. Gates like
  `reviewed_contract`-requires-5 keep their explicit check for the message;
  a record carrying the field at a lower schema is still refused on read —
  by the field-admission rule (bound 1), which admits the field only to
  records of schema 5 and above.
- **Field admission is data, not rules.** `_FIELD_FAMILIES` lists
  `(schema, record_type-or-None, fields)`: the schema-2 provenance fields
  (and `usage` on sessions) from 2, `reviewed_contract` from 5. The fields
  rule (bound 1) computes the admitted set from the record's own schema, as
  today. The schema-4 binding fields stay base fields whose *use* is gated,
  exactly as `needs_schema_4` has it today. A later schema registers its
  family as one tuple — admission stays a data edit.
- **Rules are split at today's check boundaries, no finer.** One entry per
  check group: the schema and record-type checks, the reviewed_contract and
  finding-binding gates, field admission, the required-string and timestamp
  checks, one entry per record type's shape check (with the session shape
  split so the coordination gate keeps its number 6 in today's error order),
  provenance (2), the `recorded_by` pair (1). The control-character checks
  ride inside their record-type rules at schema 1 — decision 6 binds every
  existing check to 1 anyway, so finer granularity would buy nothing.
- **The synthetic later rule lives in the test only.** Criterion: a rule
  bound to one schema above the highest supported shows a record of the
  highest schema accepted on read and refused on write. The test
  monkeypatches `_RULES` and `_RULE_FROM_SCHEMA`; production code carries no
  schema-7 anything.
- **Minimum schema derives from the record, not per-writer literals.**
  `_minimum_schema(record)` starts at the baseline 3 — the schema the
  current record model is written under — and raises it for each thing a
  later schema introduced: a finding record or a finding-binding field to 4,
  `reviewed_contract` to 5, a coordination activity to 6. Every `create_*`
  builds its record, then stamps `_minimum_schema(record)`;
  `session_record_schema` delegates to the same derivation for the live
  writer and for backfill alike. The stamped numbers are what they are today
  (3, 4, 5, 6 where they occur) — pinned by a parametrized test.

## Risks

- [A hand-forged low-schema record carrying a gated field or value is now
  read under its own schema's rules — e.g. a coordination session stamped 5
  is no longer refused on read] → intended by ADR-0015 decision 1: no lawful
  writer produces such a record (write still refuses it), the journal is
  append-only so it cannot appear in a real journal, and output-forging
  values are still refused by schema-1 rules; escaping on display (decision
  5) covers the rest in its own task.
- [Rule registration order silently changes error precedence] → the registry
  is declared in exactly today's check order; the coordination gate is split
  out of `_validate_session_record` at its original position so the first
  failure a malformed record reports is unchanged.
- [A rule added without a table entry silently passes review] → the
  completeness test compares the registry keys to the table keys; the
  read-side lookup is fail-closed (unregistered rules are skipped, not
  applied).
