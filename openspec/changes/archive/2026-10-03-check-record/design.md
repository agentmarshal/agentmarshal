## Context

CR-154 laid down how a record type is declared once — `RECORD_TYPES` in
`attestation.py`, everything else derived or pinned — and how a field
family registers: a `_FIELD_FAMILIES` entry, the shared validator tables
keyed by (record type, field), and the minimum-schema derivation. CR-160
registered the first family through that mechanism. This change
registers ADR-0022 section 3's `check` record type the same way: one
registry entry, one field family, the validator registrations it needs
and nothing more.

## Goals

- A `check` record type exists from schema 7: a measurement admitted
  after any terminal record, writable, `recorded_by` with
  `recorded_by_source` required.
- Its fields: `commit` (required, 40 lowercase hex), `name` (required),
  `result` (required, `passed` | `failed` | `error` | `skipped`),
  optional `failed_step`, `excerpt` (4 KiB UTF-8) and `run_url`.
- A `check` record on a schema below 7 is refused at write and on read;
  writing one stamps 7.

## Non-Goals

- The `record-check` command and the leak scan of the excerpt at write —
  later tasks.
- The gate transcript's measurements-line wording, `brief` and `report`
  — later tasks.

## Decisions

- **The type declares once in `RECORD_TYPES`.** Predicate
  `https://agentmarshal.dev/attestations/check/v1`, `projects_to=None`,
  `admitted_after_terminal={"done", "abandoned"}` — the measurement set
  `session` already carries — `writable`, `requires_recorded_by=True`,
  the claim of who as on `finding`. Everything else derives:
  `PREDICATE_TYPES`, the projection's state, terminal and after-terminal
  tables, the writable set the guard and the write path consult. The two
  hand-written places a new type still touches get theirs:
  `_RECORD_FIELDS` gains `"check"`, `WritableRecordType` gains
  `"check"`, and the pinning tests gain the literals. The gate reads
  admission through `record_type_is_admitted_after_terminal`, so a
  check-only append after a terminal record passes the base-state check
  with no gate-side list.
- **The check fields register as a schema-7 field family** — `(7,
  "check", _SCHEMA_7_CHECK_FIELDS)` — the admission mechanism a new
  record type shares with the old ones. `_RECORD_FIELDS["check"]` holds
  the envelope alone; below 7 the family's fields are not admitted, so a
  check record carrying them is refused at write and, on read, by the
  field-admission rule of the record's own schema — and the
  `record-schema` requirement "a writer stamps 7 exactly when its record
  carries a field a schema-7 family admits" stays literally true.
- **The record-type gate is its own rule bound to 1.** The contract
  asks that a check record on a schema below 7 be refused at write and
  on read, and a rule bound to 7 cannot reach a schema-6 record on read
  at all — the field family covers a check that carries its fields, but
  the type itself needs a guard. So `check` — registered with the other
  per-type rules — refuses `record_type: check` below schema 7 whatever
  the record carries, the same reason `fields` itself binds to 1: it
  guards admission, not history, and no legitimate history can carry the
  type. The family's own shape rule — `check-fields-7`, bound to 7 like
  `session-fields-7` — validates `commit`'s 40-lowercase-hex shape, the
  required `name` and `result` (the four-value vocabulary), and the
  optional strings non-empty when present, measured after `strip()` as
  the other schema-7 strings are.
- **`excerpt` registers the byte bound, never a truncation.**
  `_TEXT_BYTE_LIMITS[("check", "excerpt")] = 4096` — the byte-bounded
  text rule of CR-154 measured on the field's UTF-8 encoding, refusing
  beyond, never truncating; truncation at write belongs to the later
  `record-check` task. `name`, `failed_step`, `excerpt` and `run_url`
  register into `_FORGEABLE_TEXT_FIELDS` keyed `("check", field)` —
  exactly the fields the contract names; `commit`'s hex shape and
  `result`'s vocabulary admit no character the forgeable-text rule
  refuses, so they carry no registration.
- **`_minimum_schema` raises to 7 on the type** — `record_type ==
  "check"`, the `finding` precedent — and `create_check_record` builds
  the record through the same one derivation, stamping 7.

## Risks

- [A hand-made `check` record stamped below 7 with none of its fields
  reads] → the `check` rule bound to 1 refuses the type below its
  schema, and a check carrying its fields is refused by `fields` anyway.
- [A `check` record a candidate adds names no recorder] →
  `requires_recorded_by` makes the recorded-by rule refuse it; the write
  path stamps the pair from the environment before writing.
- [The registry pinning tests enumerate the types literally] → they are
  updated with the new literals in the same change, so the drift the
  pins exist to catch cannot pass silently.
