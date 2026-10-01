I verified the digest line by line against the code, the journal and the published notes. Everything in the five acceptance criteria holds:

- **Mechanism** (`docs/proposals/025-…md:15-32`) matches the code: `read_records` validates each record as it loads and raises on the first invalid one (`src/agentmarshal/journal/records.py:1103-1121`), `validate_journal` turns that into one `FAIL:` line per task and continues (`src/agentmarshal/journal/validate.py:172-212`), the gate reads only its own task (`gate.py:94`), the check is `_reject_control_characters` (`records.py:526`), it predates 0.4.0 for acceptance fields and finding ids (CR-066's contract) and 0.4.0 extended it to review `findings`/`advisory_findings` (CR-114's contract names CR-086 for exactly that) plus the schema-4 finding record's summary and refs — fields no earlier release could write.
- **0.4.1 claims** match `records.py:498-523` (`Cc`, `Cs`, `Zl`, `Zp` + the twelve bidi codepoints, one `forges_rendered_text` called from `records.py:543`, `contracts.py:64`, `validate.py:72`), the CHANGELOG 0.4.1 section and `UPGRADING.md:9-47` (which does route a pinned 0.3.0 straight to 0.4.1 and says no allowlist exists).
- **Internal arithmetic** holds: 282 tasks − 2 failing = 280 `OK` (and `validate` does print `OK: <task> …`), 6+3+2 = 11 occurrences, 3 affected records, two refused and the third never read — the same shape CR-114's contract records.
- **Hygiene**: no Cyrillic, no reporter task ids, only CR-114/CR-115 and versions 0.1.0/0.3.0/0.4.0/0.4.1 — all published; header profile string is byte-identical to the one the other Adopter A files use; index batch table is dated 2026-09-24 with disposition and where, and `docs/README.md:55` has its line. CI is unaffected (no test reads real `docs/` files).

Two non-blocking notes:

The sentence at `docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md:22-25` stacks three appositives between subject and verb ("the record in the second row of the table below, the other one in the first task, sorted behind the refused record in that task's records directory, was never read by it"), so which of the first two rows was actually refused has to be inferred rather than read; one extra clause or a split sentence would make the output shape plain.

At `docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md:35` the records are attributed to "the model reviewer" with a definite article, but the profile the index carries for Adopter A ("Python web service, Git hosting provider, Linux runner, vendored wheel") establishes no such role — "a model reviewer" is the phrase the index attaches to Adopter D's three-role loop, so a reader comparing profiles could mis-attribute the finding.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "d8d91c796faa27bd5cc7b52c14364126b14125d4", "verdict": "approved", "findings": [], "advisory_findings": ["025-unread-record-sentence-hard-to-parse", "025-model-reviewer-not-in-adopter-a-profile"]}
AGENTMARSHAL_VERDICT_END
