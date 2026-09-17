I read the implementation in `src/agentmarshal/journal/{brief,review,records,submit_review}.py`, the promoted specs, the archived change, and the tests, and checked each of the nine scenarios against a named test.

**What holds.** All nine scenarios in `openspec/changes/archive/2026-09-17-render-amendment-history/specs/` have a test whose docstring names them. The block is suppressed entirely when a task has no amendment records, so the pinned 0.3.0 prompt test at `tests/test_review_launcher.py:979` keeps its expectations byte for byte and only gained a docstring line. `launch_review` reads records from `journal_root` — the sidecar's journal when `--host` resolves one, the working tree otherwise — while the contract still comes from the reviewed commit's snapshot, which is exactly the asymmetry ADR-0011 D1 asks for. Schema 5 is stamped only when `reviewed_contract` is present, `5 >= 4` keeps the `needs_schema_4` binding check satisfied, and the `reviewed_contract`-before-`unexpected_fields` ordering in `_validate_record` means the refusal message names the field rather than degrading to the generic one. `submit-review` has no caller that supplies the field, `review --reviewed-finding` is still refused at `cli.py:575`, and no gate file is touched in any placement or lane. The rendering is built from JSON records throughout — nothing parses `contract.md` for history, per ADR-0004 D3.

Advisory findings follow.

**A-001** — `build_brief` at `src/agentmarshal/journal/brief.py:319` and `launch_review` at `src/agentmarshal/journal/review.py:398` each call `read_records(...)`, but both already hold `load_task_status`'s return value, and `status.py:89` shows that call has already read, parsed and validated every record file in the same task directory into `task.records`. Every `brief` and every `review` now walks the task's record directory twice.

**A-002** — `_CONTRACT_HASH_PATTERN` at `src/agentmarshal/journal/records.py:150` is character-for-character the same regex as `_ARTIFACT_HASH_PATTERN` on the line above it; both are used only with `fullmatch`, where the trailing `$` is redundant as well.

**A-003** — `test_review_record_hashes_the_contract_text_in_its_prompt` in `tests/test_review_launcher.py` recovers the contract by slicing the prompt between `"Task contract:\n"` and `"\n\nDiff:\n"`, but that is precisely the region this change widened to also hold the amendment block; the assertion agrees with the record only because the fixture records no amendment, so the test stops being a check of what it names as soon as the feature it accompanies is active.

**A-004** — the refusal `record schema 5 is only supported for review records` at `src/agentmarshal/journal/records.py:214` is a new closed-world constraint on every other record type, and it is neither exercised by a test nor mentioned among design.md's decisions, which describe schema 5 only as a field set, a supported-schemas entry and a stamping rule.

**A-005** — the three-branch trailing-newline separator expression now appears three times: `brief.py:259` (pre-existing, in `_append_named_material`), `brief.py:321` and `review.py:137`, with no shared helper.

**A-006** — a new record schema lands with no upgrade note: `UPGRADING.md`'s "0.3.0 → 0.4.0" section still tells operators of a shared journal that "the record schema do not change", and an older install reading a schema-5 record fails the whole task with "unknown or missing schema version". `UPGRADING.md` and `CHANGELOG.md` are outside the contract's declared scope, so this is recorded rather than fixable here.

**A-007** — `test_brief_renders_the_same_amendment_history` in `tests/test_brief.py` is the test for the spec clause "in the order the records were written", but its two fabricated `created_at` values ascend in the same direction as the record ids, so it cannot distinguish write order from timestamp order; reversing one relative to the other is what would pin the clause.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "8ffbfaa00799905b438c77c649f910ba9a73d1cf", "verdict": "approved", "findings": [], "advisory_findings": ["A-001", "A-002", "A-003", "A-004", "A-005", "A-006", "A-007"]}
AGENTMARSHAL_VERDICT_END
