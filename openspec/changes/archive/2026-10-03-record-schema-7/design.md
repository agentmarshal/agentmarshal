## Context

`records.py` knows schemas 1 to 6, and the record types are declared in
three places at once: `_RECORD_FIELDS` in `records.py`, `PREDICATE_TYPES`
in `attestation.py`, and `_RECORD_TYPE_STATES` /
`_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` / `WritableRecordType` in
`status.py` — plus `finding`'s inline requirement that `recorded_by` and
`recorded_by_source` be present. ADR-0022's four new record types would
be the fourth place a type is added by hand, and its limits (section 8)
would each be a new rule somewhere. ADR-0022 puts the model under one
schema, 7; ADR-0015's table is where its rules land.

## Goals

- Schema 7 is supported; schema 8 stays refused; no writer stamps 7.
- One registry declares every record type and all five of the attributes
  the contract names.
- The shared validators exist as their own rule-table entries bound to 7.
- Zero change to what schemas 1 to 6 accept or refuse.

## Non-Goals

- Any new field or record type — each later task registers its own.
- A writer stamping 7 (the contract-hash task does that).
- Escaping on display (ADR-0015 decision 5).
- Moving `_RECORD_FIELDS` into the registry: field admission stays
  `records.py`'s own table, pinned to the registry's keys by the
  predicate test that already runs.

## Decisions

- **The registry lives in `attestation.py` — the small module both
  sides import.** The import direction is `attestation.py` ←
  `records.py` ← `status.py`. A registry in `records.py` would make
  `attestation.py`'s `PREDICATE_TYPES` depend on `records.py` — a cycle.
  `attestation.py` is the leaf both import, so the registry lands there
  and `PREDICATE_TYPES` is derived from it. `status.py` derives its
  tables the same way. The alternative the contract names — keeping the
  tables where they are and pinning them equal by test — is kept only
  where derivation is impossible.
- **`RecordTypeSpec` carries the five declared attributes.**
  `predicate_type` (the URI the projection would carry), `projects_to`
  (the task state, `None` for non-lifecycle records),
  `admitted_after_terminal` (a `frozenset` of the terminal states the
  type is still admitted after — `{"done", "abandoned"}` for `session`,
  `{"done"}` for `reopened`, empty otherwise, so `reopened`'s done-only
  admission is a declaration rather than a special case in
  `record_type_is_admitted_after_terminal`), `writable`, and
  `requires_recorded_by`.
- **What can be derived is derived; what cannot is pinned.**
  `PREDICATE_TYPES` becomes a comprehension over the registry in the same
  module. `status.py` derives `_RECORD_TYPE_STATES`,
  `_TERMINAL_RECORD_TYPES` (types projecting to a terminal state) and
  `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` from it, and
  `record_type_is_admitted_after_terminal` reads the state set off the
  spec. `WritableRecordType` is a `Literal`: mypy needs the names written
  out, so it stays a literal and a test pins its arguments equal to the
  registry's writable types; the record guard's runtime refusal reads the
  derived `_WRITABLE_RECORD_TYPES`, so the flag decides what a writer may
  write, not only what the type checker sees. The same test pins every
  derived surface — against literals, not values recomputed from the
  registry, so a shared drift of registry and derivation cannot pass.
- **`finding` moves onto `requires_recorded_by` inside the recorded-by
  rule.** `_validate_recorded_by` reads the flag off the record's type
  and raises the same "requires a resolvable recorder" message when
  either field is missing; `_validate_finding_record` drops its inline
  copy. The check stays ahead of the pair's own shape checks, so a
  half-present pair still reports the same error. Accept/refuse is
  unchanged — the rule that raises it sits later in the registry, which
  can only reorder the message on a record already failing an earlier
  rule.
- **Schema 7 joins `_SUPPORTED_SCHEMAS`; `_minimum_schema` is
  untouched.** No field requires 7, so the derivation still tops out at
  6 and every `create_*` stamps what it stamped — the carried advisory
  to derive `_minimum_schema` from one source is not triggered, since the
  function is not touched.
- **Three shared validators, three rule-table entries bound to 7.**
  `bounded-text` reads `_TEXT_CHAR_LIMITS` ((record type, field) →
  maximum characters); `bounded-json` reads `_JSON_BYTE_LIMITS`
  ((record type, field) → maximum bytes after canonical encoding —
  `json.dumps` with sorted keys, compact separators, UTF-8 output,
  non-ASCII unescaped, and `allow_nan=False` so `NaN`/`Infinity` —
  tokens `json.loads` accepts but JSON does not define — meet the
  rule's own "must be a JSON value" refusal rather than a 3-byte token
  a strict parser could not read back); `forgeable-text` reads
  `_FORGEABLE_TEXT_FIELDS` and applies `forges_rendered_text` to a
  string the field carries. Each is its own entry in `_RULES` and
  `_RULE_FROM_SCHEMA` — the carried review advisory: a tightening
  folded into a schema-1 rule would apply to old records, so nothing
  is shared but the mechanism. All three tables are empty in
  production; tests register a test-only field into the validator's
  table and into `_FIELD_FAMILIES` to exercise the rule end to end.
- **`forgeable-text` refuses a non-string — the rule owns the type
  itself.** `bounded-text` already refuses a non-string value;
  `forgeable-text` first skipped one silently on the grounds that the
  field's own shape rule owns the type refusal — but a field family
  registers into only the validators it needs, so a registered field
  may carry no shape rule at all, and the skip was fail-open at the
  registration. Of the two options the review named — constrain
  registrations to string fields, or refuse the non-string in the rule
  — the rule refuses: the siblings stay fail-closed alike, and no
  registration can pass unguarded.
- **A registration keys on (record type, field), never the field
  alone.** ADR-0022 section 8 bounds `reason` at 1000 characters in the
  *new* record types only — "the existing `reason` fields are
  untouched" — and `reason` is already a field of `acceptance`,
  `abandoned`, `reopened` and `amendment`. A key of the field name alone
  could not express that bound without tightening those four record
  types too, so every registration names the record type whose field it
  guards, the same `only_type` shape `_FIELD_FAMILIES` already uses. A
  later task still registers and nothing more. The explicit "every
  type" form — `None` in the record-type slot — exists for a field the
  rule guards on every type that carries it; a field name an older
  record type already has is never that case, and a registration that
  reaches for `None` must say why the bound is genuinely type-blind.
- **The tables are dicts, so refusal order is registration order.**
  A set would report whichever field string-hash order yielded first —
  stable neither within a process nor across runs. Registration order
  is the order a reader of the module sees, and the field a refusal
  names is reproducible.
- **The validators sit last in registration order.** They guard fields
  no schema-1-to-6 record carries, so their position changes no error
  precedence for existing records.

## Risks

- [A test-only field registration leaking between tests] → the tables
  are monkeypatched (`setitem` on the registration dicts, `setattr` for
  `_FIELD_FAMILIES`), so pytest restores them.
- [A schema-7 record is refused by a 0.4.x installation] → intended by
  ADR-0022's upgrade rule: every clone and CI goes to 0.5.0 before the
  first 0.5.0 record is written, and nothing in this task writes one —
  the schema is known, never stamped.
- [Deriving `status.py`'s tables changes lookup semantics] → the
  derivations are one-to-one comprehensions over the registry; the
  pinning test asserts the exact values, not just the keys.
- [The rule-table scenario's title names only the older gates] → a
  MODIFIED requirement replaces the whole block and may not rename or
  drop a scenario, so "the gates bound to 2, 4, 5 and 6" stands while
  its THEN also names the validators bound to 7; tasks.md 4.1 and the
  pinning test's docstring record the widening.
