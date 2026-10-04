## 1. The record type

- [x] 1.1 `RECORD_TYPES["ext"]` declares the predicate type, no
  projected state, admission after no terminal record, writable,
  `recorded_by` with `recorded_by_source` required — verify: the
  registry pinning test in `test_attestation.py` gains the literals
  (pytest).
- [x] 1.2 `_RECORD_FIELDS["ext"]` and the `WritableRecordType`
  `Literal` gain the type — verify: the pinning tests stay green.

## 2. The field family and its rules

- [x] 2.1 `_SCHEMA_7_EXT_FIELDS` and the `_FIELD_FAMILIES` entry
  `(7, "ext", …)` admit `kind`, `commit`, `payload` and
  `payload_sha256` from schema 7 — verify: a schema-7 ext record
  round-trips; below 7 refused at write and on read (pytest).
- [x] 2.2 `_JSON_BYTE_LIMITS[("ext", "payload")]` bounds the canonical
  form at 64 KiB; `kind`, `commit` and `payload_sha256` register into
  `_FORGEABLE_TEXT_FIELDS` keyed `("ext", field)` — verify: a
  64 KiB payload admitted, one byte more refused, a forgeable `kind`
  refused (pytest).
- [x] 2.3 The `ext` rule, bound to 1, refuses the type below schema 7;
  the `ext-fields-7` rule, bound to 7, checks `kind` against the
  manifest's own `_RECORD_KIND` imported (deferred — extensions.py
  stands on records.py through contracts.py), `commit`'s 40-hex shape,
  `payload`'s presence and `payload_sha256`'s 64-hex shape and equality
  with the sha256 of the canonical form — verify: pytest, and
  `test_todays_rules_apply_from_schema_1_except_the_gates` gains the
  `ext-fields-7` binding.
- [x] 2.4 `_minimum_schema` raises to 7 on the type and
  `create_ext_record` builds the record, computing `payload_sha256`
  over the canonical form — verify: the minimum-schema
  parametrization gains the ext case (pytest).

## 3. Nothing that worked changed

- [x] 3.1 A closed task refuses an ext record through the same
  projection every other record answers to, with no new list — verify:
  the test whose docstring names the closed-task scenario (pytest).
- [x] 3.2 `status` and `validate` handle a task carrying an ext record
  without failing, and the gate admits a candidate adding one as it
  admits the other schema-7 types — verify: the tests whose
  docstrings name those scenarios (pytest).
- [x] 3.3 No other record type changes and the gate's fixtures are
  unchanged — verify: the full suite stays green, `tests/fixtures/`
  untouched.
- [x] 3.4 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
