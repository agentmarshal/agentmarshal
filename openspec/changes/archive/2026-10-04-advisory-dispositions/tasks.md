## 1. The field family

- [x] 1.1 `_SCHEMA_7_COMPLETED_FIELDS` and the `_FIELD_FAMILIES` entry
  `(7, "completed", …)` admit `advisory_dispositions` from schema 7 —
  verify: a schema-7 completed record carrying it round-trips; below 7
  refused at write and on read (pytest).
- [x] 1.2 The `completed-fields-7` rule, bound to 7, refuses the field on
  a `completed_finding` binding, an `advisory_dispositions` that is not a
  non-empty object, a key failing the finding-id rule, an entry that is
  not an object, a key outside `disposition`, `reason` and `follow_up`, a
  `disposition` outside the vocabulary, a `reason` missing on `deferred`
  or `rejected` or malformed on any, and a `follow_up` admitted on
  `deferred` alone that is not a task id — each refusal naming the
  finding id and the key at fault — and `reason` and `follow_up` take
  the `_reject_control_characters` check inside the rule — verify:
  pytest, and `test_todays_rules_apply_from_schema_1_except_the_gates`
  gains the `completed-fields-7` binding.
- [x] 1.3 `_minimum_schema` raises to 7 on the field and
  `create_completed_record` accepts `advisory_dispositions` as an
  optional keyword argument, refusing it with `completed_finding` —
  verify: the minimum-schema parametrization gains the case (pytest).

## 2. The delta and nothing that worked changed

- [x] 2.1 The delta creates `finding-lifecycle` — its Purpose written in
  the delta, covering ADR-0016's lifecycle of review findings — with
  ADDED requirements for the field, every scenario demonstrated by a
  test whose docstring names it — verify: openspec validate, pytest.
- [x] 2.2 A `completed` record without the field is validated and
  stamped exactly as before; no other record type changes, the gate's
  fixtures and every documented transcript a test pins are unchanged —
  verify: the full suite stays green, `tests/fixtures/` untouched.
- [x] 2.3 The change is archived with the archive command — verify:
  `openspec/changes/archive/` gains the dated directory and
  `openspec/specs/finding-lifecycle/spec.md` gains the requirements.
- [x] 2.4 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
