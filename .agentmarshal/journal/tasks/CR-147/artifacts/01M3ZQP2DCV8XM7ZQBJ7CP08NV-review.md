## Review — CR-147, commit `63138c55`

**What I verified**

- `src/agentmarshal/journal/contracts.py:190` admits schema 3; `src/agentmarshal/journal/contracts.py:200-205` refuses all three new fields under schema 1 or 2 with a message naming the field and schema 3, mirroring the existing schema-2 guard. `tests/test_journal.py:166` moves the unknown-schema example from 3 to 4.
- `_optional_unique_nonempty_array` (`contracts.py:66-95`) enforces absent-or-non-empty, distinct, non-empty-string entries and routes each entry through `reject_control_characters`, which delegates to `records.forges_rendered_text` — the same predicate the schema-2 string fields use, so the two sides cannot drift. Order is preserved (it returns the tuple from `_require_string_array`, not a set).
- The vocabulary check (`contracts.py:213-218`) runs *after* the shared refusals, so `independence = ['devin', 'other', 'devin']` reports the repeat rather than "not a known rule" — the design doc calls this ordering out and the parametrized test depends on it.
- Field names and the four-rule vocabulary match ADR-0022 §5 (`docs/adr/ADR-0022-…:185-198`) and ADR-0018 decision 3 (`docs/adr/ADR-0018-…:112-141`).
- All 12 scenarios in `openspec/specs/contract-governance/spec.md` have a test whose docstring names them verbatim. The archived delta and the published spec differ only in the headings `openspec archive` rewrites (`## Purpose` → `# … Specification` + `## Purpose`, `## ADDED Requirements` → `## Requirements`), so the archive is a real archive-command run.
- Nothing in the diff falls outside the contract's scope. No in-repo contract header carries `implementers`/`reviewers`/`independence` (the only textual hit is CR-147's prose body), so the new refusal does not break `agentmarshal validate`. No other spec, `open_task.py`, `status.py`, `brief.py` or `gate.py` path enumerates contract header schemas or iterates `ContractHeader`'s fields, so nothing silently changed.

**What I could not verify:** the "full CI sequence passes" criterion. This sandbox denied `uv run pytest`, `uv run ruff check` and the rest, so I reviewed the tests by reading them. Statically they look sound — the control-character fixtures use `\n` (Cc), U+2028 (Zl) and U+200F, all three of which `records._FORGEABLE_CATEGORIES`/`_BIDIRECTIONAL_CONTROLS` still refuse after the 2026-09-24 narrowing; every expected `match=` pattern is a substring of the message actually raised; added lines stay within the 88-column limit; and the new annotations satisfy mypy strict.

**Advisory finding**

`unknown-independence-rule-message-omits-the-vocabulary` — the refusal at `src/agentmarshal/journal/contracts.py:215-218` names the rule it did not know but never says which four it does know, whereas the codebase's other fixed-vocabulary refusal, `src/agentmarshal/journal/records.py:555-559`, appends `"must be one of " + ", ".join(sorted(...))`. `INDEPENDENCE_RULES` is right there; a writer who typed `distinct-vendors` gets no hint. The spec only requires naming the rule, so this is style, not a breach.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "63138c550689c85175e93efcfc3bd82adce9a754", "verdict": "approved", "findings": [], "advisory_findings": ["unknown-independence-rule-message-omits-the-vocabulary"]}
AGENTMARSHAL_VERDICT_END
