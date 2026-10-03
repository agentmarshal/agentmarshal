## 1. The field family

- [x] 1.1 `_SCHEMA_7_SESSION_FIELDS` and the `_FIELD_FAMILIES` entry
  `(7, "session", …)` admit the six fields from schema 7 — verify: a
  schema-7 session carrying each round-trips; below 7 refused (pytest).
- [x] 1.2 The five string fields register into `_FORGEABLE_TEXT_FIELDS`
  keyed `("session", field)`; no entry in the length-bound tables —
  verify: a forgeable character refused; a long value passes (pytest).
- [x] 1.3 The `session-fields-7` rule, bound to 7, refuses a `commit`
  that is not 40 lowercase hex, an empty or non-string `model`, `trace`,
  `cli_session` or `fallback_reason`, and a non-boolean `report_ready` —
  verify: pytest.
- [x] 1.4 `_minimum_schema` raises to 7 on any family field and
  `create_session_record` accepts the six as optional keyword arguments —
  verify: the minimum-schema parametrization gains the field cases
  (pytest).

## 2. Nothing that worked changed

- [x] 2.1 A session without the family stamps 3, or 6 for coordination;
  no other record type changes; the gate's fixtures are unchanged —
  verify: `test_session.py` and the gate tests stay green.
- [x] 2.2 `test_todays_rules_apply_from_schema_1_except_the_gates`
  gains the `session-fields-7` binding — verify: pytest.
- [x] 2.3 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
