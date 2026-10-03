## 1. The record type

- [x] 1.1 `RECORD_TYPES["acknowledgement"]` declares the predicate type,
  no projected state, admission after no terminal record, writable,
  `recorded_by` with `recorded_by_source` required — verify: the
  registry pinning test in `test_attestation.py` gains the literals
  (pytest).
- [x] 1.2 `_RECORD_FIELDS["acknowledgement"]` and the
  `WritableRecordType` `Literal` gain the type — verify: the pinning
  tests stay green.

## 2. The field family and its rules

- [x] 2.1 `_SCHEMA_7_ACKNOWLEDGEMENT_FIELDS` and the `_FIELD_FAMILIES`
  entry `(7, "acknowledgement", …)` admit the five fields from schema 7
  — verify: a schema-7 acknowledgement round-trips; below 7 refused at
  write and on read (pytest).
- [x] 2.2 `_TEXT_CHAR_LIMITS[("acknowledgement", "reason")]` bounds the
  reason at 1000 characters; `file` and `reason` register into
  `_FORGEABLE_TEXT_FIELDS` keyed `("acknowledgement", field)` — verify:
  an over-bound or forgeable value refused (pytest).
- [x] 2.3 The `acknowledgement` rule, bound to 1, refuses the type below
  schema 7; the `acknowledgement-fields-7` rule, bound to 7, refuses a
  malformed `commit`, a missing or empty `file` or `reason`, a record
  carrying both or neither of `signature` and `marker`, a `signature`
  the scan does not know and a `marker` that is not an integer of at
  least 1 — verify: pytest, and
  `test_todays_rules_apply_from_schema_1_except_the_gates` gains the
  `acknowledgement-fields-7` binding.
- [x] 2.4 `_minimum_schema` raises to 7 on the type and
  `create_acknowledgement_record` builds the record — verify: the
  minimum-schema parametrization gains the acknowledgement case
  (pytest).

## 3. Nothing that worked changed

- [x] 3.1 A closed task refuses an acknowledgement through the same
  projection every other record answers to, with no new list — verify:
  the test whose docstring names the closed-task scenario (pytest).
- [x] 3.2 No other record type changes and the gate's fixtures are
  unchanged — verify: the full suite stays green, `tests/fixtures/`
  untouched.
- [x] 3.3 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
