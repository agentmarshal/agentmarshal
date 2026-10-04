## 1. The field family

- [x] 1.1 `_SCHEMA_7_REVIEW_FIELDS` admits `verification` and `evidence`
  from schema 7 through the `_FIELD_FAMILIES` entry `(7, "review", …)` —
  verify: a schema-7 review carrying each round-trips; below 7 refused
  at write and on read (pytest).
- [x] 1.2 Neither field registers in `_FORGEABLE_TEXT_FIELDS` — both are
  objects, a table entry would fail-closed on the dict — and every
  string inside takes the same `_reject_control_characters` check inside
  the family's own rule, as `classes`' values do — verify: a forgeable
  value refused (pytest).
- [x] 1.3 The `review-fields-7` rule refuses a `verification` that is
  not an object, is empty or carries a key outside the three; a section
  that is not a non-empty array; an entry missing a key or carrying
  another; a `read` item that is not a string; any string inside empty
  or forgeable — each refusal naming the key and the position — and an
  `evidence` that is not an object or is empty, a key naming no finding
  of the record through the one `_check_review_keyed_field`, and a value
  empty, not a string or forgeable — verify: pytest.
- [x] 1.4 `_minimum_schema` raises to 7 on either field through the same
  `record.keys() & _SCHEMA_7_REVIEW_FIELDS` clause;
  `create_review_record` accepts the two as optional keyword arguments —
  verify: the minimum-schema parametrization gains the review cases
  (pytest).

## 2. The delta and nothing that worked changed

- [x] 2.1 The delta adds the requirements to `review-evidence`, every
  scenario demonstrated by a test whose docstring names it — verify:
  openspec validate, pytest.
- [x] 2.2 A review carrying neither field is validated and stamped
  exactly as before; no other record type changes and the gate's
  fixtures are unchanged — verify: the full suite stays green,
  `tests/fixtures/` untouched.
- [x] 2.3 The change is archived with the archive command — verify:
  `openspec/changes/archive/` gains the dated directory and
  `openspec/specs/review-evidence/spec.md` gains the requirements.
- [x] 2.4 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
