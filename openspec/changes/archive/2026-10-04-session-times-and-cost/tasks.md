## 1. The field family

- [x] 1.1 `_SCHEMA_7_SESSION_FIELDS` gains `started_at`, `ended_at`,
  `resets_at` and `cost` — the one `(7, "session", …)` `_FIELD_FAMILIES`
  entry admits all ten fields from schema 7 and the existing
  `_minimum_schema` clause stamps a record carrying any of them 7 —
  verify: each new field round-trips under schema 7, and is refused below
  7 at write and on read (pytest).
- [x] 1.2 `created_at`'s UTC ISO-8601 rule is factored into
  `_utc_timestamp` and the `session-fields-7` rule — bound to 7 — reuses
  it for the three timestamps, refuses a lone `started_at` or `ended_at`,
  an `ended_at` earlier than `started_at` and a `resets_at` on any
  outcome but `provider-limit`, and validates `cost` — an object of
  exactly `amount` (a decimal string), `currency` (three uppercase ASCII
  letters) and `source` (`reported` | `estimated`), each refusal naming
  the field and the key at fault — verify: pytest.
- [x] 1.3 `create_session_record` accepts the four as optional keyword
  arguments — verify: the minimum-schema parametrization gains the cases
  (pytest).

## 2. The delta and nothing that worked changed

- [x] 2.1 The delta modifies `session-activity`: ADDED requirements for
  the fields, and the below-7 requirement MODIFIED in place with its
  exact header where the family's enumeration made it untrue — every
  scenario demonstrated by a test whose docstring names it — verify:
  openspec validate, pytest.
- [x] 2.2 A session carrying none of the fields is validated and stamped
  exactly as before; no other record type changes; the gate's fixtures
  and every documented transcript a test pins are unchanged — verify:
  the full suite stays green, `tests/fixtures/` untouched.
- [x] 2.3 The change is archived with the archive command — verify:
  `openspec/changes/archive/` gains the dated directory and
  `openspec/specs/session-activity/spec.md` gains the requirements.
- [x] 2.4 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
