## Context

CR-154 laid down how a record type is declared once — `RECORD_TYPES` in
`attestation.py`, everything else derived or pinned — and how a field
family registers: a `_FIELD_FAMILIES` entry, the shared validator tables
keyed by (record type, field), and the minimum-schema derivation. CR-160
registered the first family through that mechanism; CR-167 the first new
record type. This change registers ADR-0021's and ADR-0022 section 3's
`acknowledgement` record type the same way: one registry entry, one
field family, the validator registrations it needs and nothing more.

## Goals

- An `acknowledgement` record type exists from schema 7: a claim
  admitted after no terminal record, writable, `recorded_by` with
  `recorded_by_source` required.
- Its fields: `commit` (required, 40 lowercase hex), `file` (required,
  the path as the scan prints it — masked, non-empty), exactly one of
  `signature` (a built-in signature id the scan knows) or `marker` (an
  integer of at least 1), and `reason` (required, at most 1000
  characters).
- An `acknowledgement` record on a schema below 7 is refused at write
  and on read; writing one stamps 7.

## Non-Goals

- The `acknowledge` command — a later task.
- The leak scan and the gate reading acknowledgements and marking
  acknowledged hits; `status` showing who acknowledged; the command's
  exit status changing — all later tasks.
- Self-acknowledgement marking — derived on display, never stored; the
  display is a later task.

## Decisions

- **The type declares once in `RECORD_TYPES`.** Predicate
  `https://agentmarshal.dev/attestations/acknowledgement/v1`,
  `projects_to=None` — an acknowledgement changes no task state —
  `admitted_after_terminal` empty, `writable`,
  `requires_recorded_by=True`, the claim of who as on `finding` and
  `check`: an acknowledgement names who acknowledged (ADR-0021 decision
  4), and any declared actor may write it, so admission is the pair the
  registry already expresses. Everything else derives:
  `PREDICATE_TYPES`, the projection's state, terminal and after-terminal
  tables, the writable set the guard and the write path consult. The two
  hand-written places a new type still touches get theirs:
  `_RECORD_FIELDS` gains `"acknowledgement"`, `WritableRecordType` gains
  `"acknowledgement"`, and the pinning tests gain the literals.
- **The acknowledgement fields register as a schema-7 field family** —
  `(7, "acknowledgement", _SCHEMA_7_ACKNOWLEDGEMENT_FIELDS)` — the
  admission mechanism a new record type shares with the old ones.
  `_RECORD_FIELDS["acknowledgement"]` holds the envelope alone; below 7
  the family's fields are not admitted, so a record carrying them is
  refused at write and, on read, by the field-admission rule of the
  record's own schema — and the `record-schema` requirement "a writer
  stamps 7 exactly when its record carries a field a schema-7 family
  admits" stays literally true. `reason` is a field name older record
  types already carry; it enters the family's set all the same — the
  family admits it on *this* type, and the bound that guards it keys on
  the type.
- **The record-type gate is its own rule bound to 1.** The contract
  asks that an acknowledgement record on a schema below 7 be refused at
  write and on read, and a rule bound to 7 cannot reach a schema-6
  record on read at all — the field family covers a record that carries
  its fields, but the type itself needs a guard. So `acknowledgement` —
  registered with the other per-type rules, beside `check` — refuses
  `record_type: acknowledgement` below schema 7 whatever the record
  carries, for the same reason `fields` itself binds to 1: it guards
  admission, not history, and no legitimate history can carry the type.
- **The family's own shape rule, `acknowledgement-fields-7`, is bound
  to 7** like `check-fields-7` and `session-fields-7`. It validates
  `commit`'s 40-lowercase-hex shape (the `_REVIEWED_COMMIT_PATTERN` the
  binding fields already measure by), the required `file` and `reason`
  non-empty measured after `strip()` as the other schema-7 strings are,
  the exactly-one-of `signature`/`marker` pair — a record carrying both
  or neither is refused with a message naming the two fields, the
  `_validate_binding` phrasing — and the pair's shapes: `signature` a
  string naming a built-in signature id, `marker` an integer of at
  least 1 (`type(marker) is int`, as the token counters already check,
  so a boolean is not a number).
- **`signature` validates against the scan's own table.** The ids the
  record admits are the names `_LEAK_PATTERNS` in `capture.py` carries —
  derived once into a frozenset at module load, never a second list: a
  new built-in signature joins the vocabulary the record admits by
  joining the scan's table, and a stale string the scan never prints is
  refused. A marker's position is a number, not a name, so `marker`
  carries no list to agree with — the configured list it numbers is the
  project's own, and a renumbered list is exactly what ADR-0021 wants to
  fail visible.
- **`reason` registers the character bound; `file` and `reason`
  register the forgeable-text rule — for exactly this record type and
  field.** `_TEXT_CHAR_LIMITS[("acknowledgement", "reason")] = 1000` —
  ADR-0022 section 8's bound, a character count as the ADR states, not
  the byte measure `excerpt` takes. `file` and `reason` are the family's
  displayed strings, so they register into `_FORGEABLE_TEXT_FIELDS`
  keyed `("acknowledgement", field)`. `commit`'s hex shape, the
  signature vocabulary and `marker`'s integer shape admit no character
  the rule refuses, so they carry no registration — the same accounting
  `check` made for its own non-text fields.
- **`_minimum_schema` raises to 7 on the type** — `record_type ==
  "acknowledgement"`, the `check` and `finding` precedent — and
  `create_acknowledgement_record` builds the record through the same one
  derivation, stamping 7; its `signature`/`marker` pair follows the
  `reviewed_commit`/`reviewed_finding` pattern — a nullable positional
  and a keyword-only alternative — and refuses both-or-neither up
  front, as `create_review_record` refuses its own pair.

## Risks

- [A hand-made `acknowledgement` record stamped below 7 with none of
  its fields reads] → the `acknowledgement` rule bound to 1 refuses the
  type below its schema, and one carrying its fields is refused by
  `fields` anyway.
- [An `acknowledgement` record a candidate adds names no recorder] →
  `requires_recorded_by` makes the recorded-by rule refuse it; the write
  path stamps the pair from the environment before writing.
- [A `signature` id added to the scan could leave the record's
  vocabulary behind] → the ids are derived from `_LEAK_PATTERNS`, not
  listed again, so the two cannot drift.
- [The registry pinning tests enumerate the types literally] → they are
  updated with the new literals in the same change, so the drift the
  pins exist to catch cannot pass silently.
