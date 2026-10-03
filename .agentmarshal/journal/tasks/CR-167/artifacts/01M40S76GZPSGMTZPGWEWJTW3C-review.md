I reviewed the full diff against the contract, the two named specs, ADR-0022 §3/§8, and the surrounding registry/rule machinery (`attestation.py`, `records.py`, `status.py`, `gate.py`, `status_view.py`).

**What checks out**

- `RECORD_TYPES["check"]` is one declaration: predicate URI, `projects_to=None`, `admitted_after_terminal={"done","abandoned"}`, writable by default, `requires_recorded_by=True`. The projection's four tables and the gate's admission (`gate.py:815`) all derive from it — the gate keeps no second list, and `test_attestation.py` pins the derived sets and the two hand-written places (`_RECORD_FIELDS`, `WritableRecordType`) to the registry.
- The field family `(7, "check", _SCHEMA_7_CHECK_FIELDS)` is the only field admission; `_RECORD_FIELDS["check"]` holds the envelope alone, so a schema-6 check carrying its fields dies on `fields`, and the `check` rule bound to 1 catches the bare case on read as well as at write. `excerpt` is registered in `_TEXT_BYTE_LIMITS` at 4096 and measured on UTF-8 (`records.py:749`) — refused, never truncated. Exactly the four named fields register in `_FORGEABLE_TEXT_FIELDS`; `commit` and `result` correctly carry none.
- `check-fields-7` is bound to 7 like `session-fields-7`, and `test_todays_rules_apply_from_schema_1_except_the_gates` gained that binding. `_minimum_schema` raises on the type, and `test_every_record_factory_writes_the_current_schema` plus the minimum-schema parametrization pin 7.
- No other record type's admitted fields, rules or limits change — every new rule returns early on a foreign `record_type`, and all four registration tables are keyed by (record type, field). `tests/fixtures/` is untouched. `status_view.py` already falls back to a generic line for a type with no renderer, so nothing crashes on display.
- Both delta specs match what landed in `openspec/specs/`, the two MODIFIED headers in `record-lifecycle` are byte-identical to the existing ones, and all sixteen new scenarios have a test whose docstring names them (12 in `tests/test_check.py`, 2 lifecycle, 2 in `tests/test_gate.py`).

I did not re-run the suite (no executable Python in this sandbox), so the CI claim stands on the coordinator's note.

**Advisory finding**

ADV-167-01: `openspec/changes/archive/2026-10-03-check-record/proposal.md:31` labels the capability `- added: \`review-evidence\``, but `openspec/specs/review-evidence/spec.md` already existed and this change only appends requirements to it. The repo's convention reserves `added:`/`### New Capabilities` for a capability the change creates (`read-rules-by-schema` → `added: record-schema`, which carries the `## Purpose` header; `outbox-new-and-check` → `### New Capabilities`) and uses `modified:` for ADDED requirements on an existing capability (`contract-hash` → `modified: contract-governance`, `record-session-schema-7-flags` → `modified: session-activity`, both with pure `## ADDED Requirements` deltas). The contract itself describes this as "review-evidence gains the check record (ADDED requirements)", so the archived proposal now misreports review-evidence as new.

One non-finding note, since the contract defers it explicitly: a check-only append now prints `PASS: measurements-only append to a task closed at base (session records accrue post-terminal)` though no session record is present. That wording is named a later task in the contract's Context, and the new gate tests assert only the prefix, so I am not counting it against this change.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "4783ce19d9cd51f6646caea80bc4882172a0e085", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-167-01"]}
AGENTMARSHAL_VERDICT_END
