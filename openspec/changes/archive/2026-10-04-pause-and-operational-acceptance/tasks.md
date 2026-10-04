## 1. The record

- [x] 1.1 `_SCHEMA_7_ACCEPTANCE_FIELDS` and the `_FIELD_FAMILIES` entry
  `(7, "acceptance", …)` admit `accepted_pause` and `operational` from
  schema 7 — verify: a schema-7 record round-trips; below 7 refused at
  write and on read (pytest).
- [x] 1.2 `_validate_acceptance_record` requires exactly one of
  `findings`, `accepted_pause` and `operational` — the refusal names the
  three — and keeps the `findings` validation for the findings form; the
  `acceptance-fields-7` rule, bound to 7, refuses a new form bound by
  `accepted_finding`, an `accepted_pause` that is not exactly an
  `extension` object, an `extension` failing the extension-name or
  forgeable-text rule, and an `operational` that is not `true` — verify:
  pytest, and `test_todays_rules_apply_from_schema_1_except_the_gates`
  gains the `acceptance-fields-7` binding.
- [x] 1.3 `_minimum_schema` raises to 7 on the family's fields, and
  `create_acceptance_record` builds the new forms — verify: the
  minimum-schema parametrization gains the cases (pytest).

## 2. The readers

- [x] 2.1 The gate's two lanes judge acceptance over findings by the
  latest acceptance carrying `findings` — verify: the shadowing tests on
  both bindings (pytest).
- [x] 2.2 `status` renders the new forms — `accepted_pause=<extension>` /
  `operational` where the findings form names its findings, with the same
  binding and self-acceptance marking — and `report` derives
  `accepted-over-findings` only from an acceptance carrying `findings` —
  verify: pytest.
- [x] 2.3 Outputs for an acceptance carrying `findings` are unchanged —
  verify: the gate fixtures, the status-view pin and the quickstart test
  stay green untouched.

## 3. Checks

- [x] 3.1 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
