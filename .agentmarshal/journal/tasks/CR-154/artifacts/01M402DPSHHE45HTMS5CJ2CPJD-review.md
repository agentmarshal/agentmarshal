I reviewed the diff against CR-154 and read the full implementation, the derived tables, the archived change, and the applied spec.

**What I verified**

- **Registry (criterion 3):** `RECORD_TYPES` in `attestation.py` carries all five declared attributes; `PREDICATE_TYPES` is a comprehension over it (`attestation.py:94`), and `status.py:39-58` derives `_RECORD_TYPE_STATES`, `_TERMINAL_RECORD_TYPES`, `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` and `_WRITABLE_RECORD_TYPES`. `tests/test_attestation.py:81` pins every derived surface against literals (not recomputed values), and `WritableRecordType`'s `get_args` against the writable set. The direction `attestation ← records ← status` keeps the import graph acyclic.
- **`finding` onto the flag:** `_validate_recorded_by` (`records.py:1014`) raises the byte-identical message the inline check raised, ahead of the pair's own shape checks, so accept/refuse for finding records is unchanged; `tests/test_findings.py:322` and the new `test_a_type_requiring_its_recorder_refuses_a_record_naming_none` both pin it. `RECORD_TYPES[record_type]` cannot KeyError because `record-type` and `record-type-predicate` are bound to schema 1 and run first.
- **Schema 7 (criterion 2):** `_SUPPORTED_SCHEMAS` gains 7; `_minimum_schema` is untouched and is the only stamping path (`backfill.py:151` goes through `session_record_schema`), so no writer can reach 7 — asserted per-writer by `record["schema"] < 7`. The unknown example moved to 8 and now pins the refusal at write *and* read.
- **Validators (criterion 4):** three separate `_RULES` entries, three `_RULE_FROM_SCHEMA` entries at 7, three empty production tables, registrations keyed `(record type | None, field)` so ADR-0022's `reason` bound cannot leak onto the four existing `reason` fields — and a test proves that isolation. Dict tables give reproducible refusal order, also tested.
- **Nothing older changes (criterion 5):** no rule bound below 7 was touched, no fixture changed, no other module or spec hardcodes the schema ceiling, and the only `_SUPPORTED_SCHEMAS` reader in tests computes the max. I could not run `pytest`/`ruff`/`mypy`/`validate` here (command execution was declined), so I checked the sequence by reading: every new/changed line is within the 88-column limit and formatted as ruff-format would emit it, and I traced each new test's expected path by hand.

Two non-blocking notes follow.

`_canonical_json` at `src/agentmarshal/journal/records.py:690` leaves `allow_nan` at its permissive default, so a float `nan`/`inf` — which `json.load` happily produces from the `NaN`/`Infinity` tokens a hand-edited record file may carry — is encoded as the non-JSON token `NaN` and measured at 3 bytes, instead of falling into the rule's own "must be a JSON value" refusal; the docstring's promise of "one byte count for one value" does not hold for that input. It is latent, since no production field is registered in `_JSON_BYTE_LIMITS` yet, and `allow_nan=False` closes it before the first field family arrives.

Task 4.1 in `openspec/changes/archive/2026-10-03-record-schema-7/tasks.md` is checked off claiming the scenario line was "renamed to match the delta", but the scenario header in both the delta and the applied `openspec/specs/record-schema/spec.md:85` still reads "except the gates bound to 2, 4, 5 and 6" while its own THEN now names schema 7 as well — the title undersells what the scenario asserts.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "1ee5272abc944e00f17e7524ea5552184d91a8af", "verdict": "approved", "findings": [], "advisory_findings": ["advisory-canonical-json-allows-nan-and-infinity", "advisory-stale-rule-binding-scenario-title"]}
AGENTMARSHAL_VERDICT_END
