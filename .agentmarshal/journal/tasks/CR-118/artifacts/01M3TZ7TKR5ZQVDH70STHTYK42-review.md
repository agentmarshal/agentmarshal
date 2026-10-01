## Review of CR-118 @ `f28ec091ab9a53bce4b3c349cc7489c754e7aeb4`

I checked every claim in the digest against the code and the published docs in the snapshot: `_reject_control_characters` / `forges_rendered_text` in `src/agentmarshal/journal/records.py:489-544`, `read_records` (`records.py:1079-1131`, sorted read, raises on the first invalid record with the path appended), `validate_journal` (`validate.py:182-211`, one `FAIL` line per task then `continue`), the gate's single-task read (`gate.py:94`), `cli.py:766` for `validate: journal invalid`, CHANGELOG 0.4.1, UPGRADING's `0.4.0 → 0.4.1` section, and the archived CR-114 openspec change.

What holds up:

- The mechanism matches the code and the published CR-114 proposal: validation runs on read, the check predates 0.4.0 (acceptance party/reason/finding ids, as `_reject_control_characters`' docstring and the 0.2.0 gate rendering have it), 0.4.0 extended it to review `findings`/`advisory_findings` plus the schema-4 finding summary and artifact refs, and `str.isprintable()` was the old test. The "one failure line per task, the second record never read" account is exactly what `read_records` + `validate_journal` do, and it reconciles CR-114's "three records" with CR-115's "two refused".
- The 0.4.1 set (`Cc`, `Cs`, `Zl`, `Zp` + U+061C, U+200E, U+200F, U+202A–U+202E, U+2066–U+2069) and the "one predicate" claim match `records.py` and `contracts.py`. The two additions over the reporter's list are described correctly.
- Dispositions cover all four proposals in the shape the contract asks; the "straight to 0.4.1" claim is backed by `UPGRADING.md:9-14`; CR-114/CR-115 and 0.4.1 are all published; no adopter task identifier appears.
- The reporter line uses A's existing short profile (as 001 and 012 do), the index batch is dated 2026-09-24, sits above 2026-09-18, carries disposition and *where*, A's attribution (001–007, 010, 012) matches the 2026-08-30 table, and `docs/README.md` has its line.

Two limits on this review, neither a defect: the private source file is not in the snapshot, so I could not verify the measurements are quoted verbatim or that the sha256 is the file's (it matches the contract exactly, and the table's internal arithmetic is consistent — 6+3+2 = 11 occurrences, 282 − 2 = 280 `OK`); and the CI sequence could not be executed here (the commands needed approval in this non-interactive session), though nothing in this docs-only diff is read by `validate`, pytest, ruff or mypy.

Two advisory points:

`CR-118-A001` — `docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md:104` states the open question as "how a reader knows which rules a record was written under — nothing in a record says so today", but every record carries `schema` and `tool_version`; the digest's own evidence table quotes both (`2`, `0.1.0`) and infers from them that an earlier release wrote these records, and CR-114's design.md frames the undecided mechanism as "rules scoped to the schema that introduced them". The gap is that no rule set is bound to a schema or a version, not that a record lacks the provenance — as written it points a reader at a missing field that exists.

`CR-118-A002` — `docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md:22-24`: "That is the shape of the run's output: three records carry the character, across two tasks — they are the table listing the three records below." reads as an unfinished edit (the records are not the table), and the colon promises the output's shape then states a fact about records. It is the sentence that ties the run's two failure lines to the three-row table, so it is the one a reporter matching the digest to their own run will stop at.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "f28ec091ab9a53bce4b3c349cc7489c754e7aeb4", "verdict": "approved", "findings": [], "advisory_findings": ["CR-118-A001", "CR-118-A002"]}
AGENTMARSHAL_VERDICT_END
