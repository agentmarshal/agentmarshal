## 1. The record type

- [x] 1.1 `RECORD_TYPES["agreement"]` declares the predicate type, no
  projected state, admission after no terminal record, writable,
  `recorded_by` with `recorded_by_source` required — verify: the
  registry pinning test in `test_attestation.py` gains the literals
  (pytest).
- [x] 1.2 `_RECORD_FIELDS["agreement"]` and the `WritableRecordType`
  `Literal` gain the type — verify: the pinning tests stay green.

## 2. The field family and its rules

- [x] 2.1 The `_FIELD_FAMILIES` entry `(7, "agreement",
  _SCHEMA_7_CONTRACT_FIELDS)` admits `contract` on agreements from
  schema 7 — verify: a schema-7 agreement round-trips; below 7 refused
  at write and on read (pytest).
- [x] 2.2 `("agreement", "contract")` registers into
  `_FORGEABLE_TEXT_FIELDS`; no length bound applies — verify: a
  forgeable value refused (pytest).
- [x] 2.3 The `agreement` rule, bound to 1, refuses the type below
  schema 7; the `agreement-fields-7` rule, bound to 7, refuses an
  agreement carrying no `contract`, while `contract-hash-7` owns the
  field's 64-hex shape — verify: pytest, and
  `test_todays_rules_apply_from_schema_1_except_the_gates` gains the
  `agreement-fields-7` binding.
- [x] 2.4 `_minimum_schema` raises to 7 on the type and
  `create_agreement_record` builds the record — verify: the
  minimum-schema parametrization gains the agreement case (pytest).

## 3. Nothing that worked changed

- [x] 3.1 A closed task refuses an agreement through the same projection
  every other record answers to, with no new list — verify: the test
  whose docstring names the closed-task scenario (pytest).
- [x] 3.2 `status` and `validate` handle a task carrying an agreement
  without failing, and the gate admits a candidate adding one as it
  admits the other schema-7 types — verify: the tests whose docstrings
  name those scenarios (pytest).
- [x] 3.3 No other record type changes and the gate's fixtures are
  unchanged — verify: the full suite stays green, `tests/fixtures/`
  untouched.
- [x] 3.4 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
