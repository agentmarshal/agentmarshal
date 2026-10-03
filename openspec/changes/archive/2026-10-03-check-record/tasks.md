## 1. The record type

- [x] 1.1 `RECORD_TYPES["check"]` declares the predicate type, no
  projected state, admission after `done` and `abandoned`, writable,
  `recorded_by` with `recorded_by_source` required — verify: the
  registry pinning test in `test_attestation.py` gains the literals
  (pytest).
- [x] 1.2 `_RECORD_FIELDS["check"]` and the `WritableRecordType`
  `Literal` gain the type — verify: the pinning tests stay green.

## 2. The field family and its rules

- [x] 2.1 `_SCHEMA_7_CHECK_FIELDS` and the `_FIELD_FAMILIES` entry
  `(7, "check", …)` admit the six fields from schema 7 — verify: a
  schema-7 check round-trips; below 7 refused at write and on read
  (pytest).
- [x] 2.2 `_TEXT_BYTE_LIMITS[("check", "excerpt")]` bounds the excerpt
  at 4 KiB of UTF-8; `name`, `failed_step`, `excerpt` and `run_url`
  register into `_FORGEABLE_TEXT_FIELDS` keyed `("check", field)` —
  verify: an over-bound or forgeable value refused (pytest).
- [x] 2.3 The `check` rule, bound to 1, refuses the type below schema 7;
  the `check-fields-7` rule, bound to 7, refuses a malformed `commit`, a
  missing or empty `name`, a `result` outside the vocabulary and an
  empty optional string — verify: pytest, and
  `test_todays_rules_apply_from_schema_1_except_the_gates` gains the
  `check-fields-7` binding.
- [x] 2.4 `_minimum_schema` raises to 7 on the type and
  `create_check_record` builds the record — verify: the minimum-schema
  parametrization gains the check case (pytest).

## 3. Nothing that worked changed

- [x] 3.1 The projection and the gate admit a check append after a
  completed and after an abandoned task through the one registry, with
  no second list — verify: tests whose docstrings name the
  record-lifecycle scenarios (pytest).
- [x] 3.2 No other record type changes and the gate's fixtures are
  unchanged — verify: the full suite stays green, `tests/fixtures/`
  untouched.
- [x] 3.3 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
