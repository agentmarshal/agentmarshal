I reviewed the diff against the contract and the merged `record-schema` spec, reading `records.py`, `attestation.py`, `status.py` and the touched tests in full. Test/lint/mypy execution was blocked in this sandbox, so AC 5's "full CI sequence passes" is verified by reading only — I traced each new and changed test by hand against the code paths it exercises and found no failure.

What holds up:

- Schema 7 is in `_SUPPORTED_SCHEMAS` (`records.py:150`), `_minimum_schema` is untouched, and `test_each_writer_stamps_the_minimum_schema_its_record_needs` now asserts `< 7`, so nothing stamps it. The unknown-schema example moved to 8 and now pins the refusal at both write and read.
- `RECORD_TYPES` in `attestation.py:57` carries all five declared attributes; `PREDICATE_TYPES` and all three `status.py` tables are genuine comprehensions over it, and `record_type_is_admitted_after_terminal` reads the spec's state set. I checked the derived values element by element against the literals they replace — `_RECORD_TYPE_STATES`, `_TERMINAL_RECORD_TYPES` and `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` are identical, and `session`'s old "any terminal state" behaviour is preserved because only `done` and `abandoned` exist. `test_gate.py:1942-1946` still pins the admission matrix with hardcoded values independently of the registry, so the derivation cannot silently drift.
- The `RECORD_TYPES[record_type]` lookup in `_validate_recorded_by` cannot `KeyError`: `record-type` and `record-type-predicate` both run earlier and are both bound to schema 1, and `test_every_accepted_record_type_is_registered` pins the key sets equal.
- The three validators are their own `_RULES` entries registered last and bound to 7, the tables are empty in production, and all fourteen delta scenarios have a test whose docstring names them.

Three advisory notes:

`reason-bound-cannot-be-scoped-to-new-record-types` — `_TEXT_CHAR_LIMITS` and `_FORGEABLE_TEXT_FIELDS` (`src/agentmarshal/journal/records.py:285-287`) are keyed by bare field name with no record-type qualification. ADR-0022 §8's only shared-name limit is "`reason` in the new record types at 1000 characters … The existing `reason` fields are untouched", and `reason` already exists on `acceptance`, `abandoned`, `reopened` and `amendment`. A later task cannot register it by registration alone — it would have to change this mechanism, which is the one thing the objective says later tasks should not do.

`finding-refusal-message-precedence-moved` — moving the recorder check out of `_validate_finding_record` into `_validate_recorded_by` (`records.py:1001`) moves it from the `finding` rule to the `recorded-by` rule, which sits after `provenance`. A finding record that is missing its recorder *and* carries a bad `source` now reports the source error where it used to report the recorder error. Accept/refuse is unchanged and the design doc reasons about this explicitly, but AC 3's "no change in behaviour" is not literally true for message precedence, and no test pins either order.

`forgeable-text-field-order-is-hash-ordered` — `_check_forgeable_text` (`records.py:602`) iterates a `frozenset`. The bounded-text and bounded-JSON rules iterate dicts and so report fields in registration order; this one reports in string-hash order, which Python randomises per process. Once more than one field is registered, a record carrying forgeable text in two of them names a different field run to run.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "1355e7ba80cd11f3847b0df5441df02b7d1ae599", "verdict": "approved", "findings": [], "advisory_findings": ["reason-bound-cannot-be-scoped-to-new-record-types", "finding-refusal-message-precedence-moved", "forgeable-text-field-order-is-hash-ordered"]}
AGENTMARSHAL_VERDICT_END
