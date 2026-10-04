## 1. The field family

- [x] 1.1 `_SCHEMA_7_REVIEW_FIELDS` and the `_FIELD_FAMILIES` entry
  `(7, "review", …)` admit `previous_review` and `classes` from schema
  7 — verify: a schema-7 review carrying each round-trips; below 7
  refused at write and on read (pytest).
- [x] 1.2 `("review", "previous_review")` registers into
  `_FORGEABLE_TEXT_FIELDS` — its ULID shape never lets the entry fire —
  and each `classes` value and `reviewer.actor` take the same
  `_reject_control_characters` check inside the family's own rule —
  verify: a forgeable value refused (pytest).
- [x] 1.3 The `review-fields-7` rule, bound to 7, refuses a
  `previous_review` that is no record id, a `classes` that is not an
  object or is empty, a `classes` key naming no finding of the record,
  a class value or `reviewer.actor` that is empty, not a string or
  forgeable — verify: pytest, and
  `test_todays_rules_apply_from_schema_1_except_the_gates` gains the
  `review-fields-7` binding.
- [x] 1.4 `_validate_review_record` admits `actor` inside `reviewer`
  from the record's own schema 7 — below 7 the object stays exactly
  `role`, `vendor`, `model`, `email`, refused on read too — and
  `_minimum_schema` raises to 7 on `previous_review`, `classes` or
  `reviewer.actor`; `create_review_record` accepts the three as
  optional keyword arguments — verify: the minimum-schema
  parametrization gains the review cases (pytest).

## 2. The delta and nothing that worked changed

- [x] 2.1 The delta adds the requirements to `review-evidence`, every
  scenario demonstrated by a test whose docstring names it — verify:
  openspec validate, pytest.
- [x] 2.2 A review carrying none of the fields is validated and stamped
  exactly as before; no other record type changes and the gate's
  fixtures are unchanged — verify: the full suite stays green,
  `tests/fixtures/` untouched.
- [x] 2.3 The change is archived with the archive command — verify:
  `openspec/changes/archive/` gains the dated directory and
  `openspec/specs/review-evidence/spec.md` gains the requirements.
- [x] 2.4 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
