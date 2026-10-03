## 1. One registry of record types

- [x] 1.1 `RecordTypeSpec` and `RECORD_TYPES` in `attestation.py` — per
  type: predicate type, projected state, terminal states admitted after,
  writable, `recorded_by` required; `PREDICATE_TYPES` derived from it —
  verify: `test_every_accepted_record_type_is_registered` stays green.
- [x] 1.2 `status.py` derives `_RECORD_TYPE_STATES`,
  `_TERMINAL_RECORD_TYPES` and `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`
  from the registry; `record_type_is_admitted_after_terminal` reads the
  spec's state set; `WritableRecordType` stays a `Literal` pinned equal
  by a test — verify: `test_journal.py`, `test_status_view.py` and the
  gate tests over closed tasks stay green.
- [x] 1.3 `finding` moves onto `requires_recorded_by` inside
  `_validate_recorded_by`; the inline check in `_validate_finding_record`
  is removed — verify: `test_findings.py` stays green, the
  resolvable-recorder message is unchanged.

## 2. Schema 7 is known, never stamped

- [x] 2.1 `_SUPPORTED_SCHEMAS` gains 7 — verify: a schema-7 record
  carrying only older fields is written and read (pytest).
- [x] 2.2 `test_unknown_schema_is_rejected` moves from 7 to 8 —
  verify: pytest.
- [x] 2.3 No writer stamps 7 — the minimum-schema parametrization keeps
  its numbers — verify: `test_record_schema.py`.

## 3. Shared validators as rules of schema 7

- [x] 3.1 `bounded-text` (`_TEXT_CHAR_LIMITS`), `bounded-json`
  (`_JSON_BYTE_LIMITS`, canonical encoding) and `forgeable-text`
  (`_FORGEABLE_TEXT_FIELDS`) registered in `_RULES`, each bound to 7 in
  `_RULE_FROM_SCHEMA`; the tables empty in production — verify: the
  completeness and binding tests stay green with the new entries.
- [x] 3.2 Tests exercise each validator through a test-only field
  registered in its table and in `_FIELD_FAMILIES`: over-bound refused,
  within-bound admitted, a schema-7-bound validator not reaching an
  earlier record on read — verify: pytest.

## 4. Nothing that worked changed

- [x] 4.1 `test_todays_rules_apply_from_schema_1_except_the_gates` gains
  the three schema-7 bindings — verify: pytest. The delta's scenario
  keeps its earlier title ("the gates bound to 2, 4, 5 and 6") while its
  THEN names the validators bound to 7: a MODIFIED requirement may not
  rename or drop a scenario, so the title stands as written.
- [x] 4.2 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
