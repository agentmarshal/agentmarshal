## 1. One rule table in record validation

- [x] 1.1 `_RULES` registry (ordered, decorator-registered) and
  `_RULE_FROM_SCHEMA` table in `records.py`; every check `_validate_record`
  makes becomes a named rule — schema-1 bindings except provenance (2),
  finding bindings (4), `reviewed_contract` (5), coordination (6); field
  admission moves to `_FIELD_FAMILIES` — verify: the split validation runs
  green under pytest.
- [x] 1.2 `_validate_record(record, *, for_write)` applies all rules on
  write and the record's own schema's rules on read;
  `validate_record_for_write` passes `for_write=True`, `read_records` and
  `validate_record_content` `for_write=False` — verify: pytest on
  `test_journal.py`, `test_session.py`, `test_record_text_safety.py`,
  `test_findings.py` (all unchanged).

## 2. Tests pin the table and the sides

- [x] 2.1 Completeness test: `_RULES` keys equal `_RULE_FROM_SCHEMA` keys,
  first rule is the schema check, and the bindings are schema 1 except the
  four gates — verify: test fails if a rule lacks an entry.
- [x] 2.2 Test-only rule bound to `max(_SUPPORTED_SCHEMAS) + 1` (monkeypatch
  the registry and table): a record of the highest schema is accepted by
  `read_records`/`validate_record_content` and refused by
  `validate_record_for_write` — verify: pytest; the synthetic rule never
  appears in `records.py`.
- [x] 2.3 A rule registered with no table entry is never checked on read
  (fail-closed lookup) — verify: pytest.

## 3. Writers derive the minimum schema

- [x] 3.1 `_minimum_schema(record)` derivation; every `create_*` and
  `session_record_schema` use it — verify: grep that no writer writes a
  `schema` literal.
- [x] 3.2 Parametrized test pins each writer's stamp for the same input
  (3, 4, 5, 6 where they occur) — verify: pytest.

## 4. Nothing that worked changed

- [x] 4.1 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
