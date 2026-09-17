I reviewed the launcher path, the shared resolver extraction, the gate refactor, the CLI wiring, the prompts, the specs and the docs against the contract's five acceptance criteria.

**What I verified holds:**

- The commit prompt is byte-identical after the refactor: `_prose_instruction()` and `_verdict_protocol("reviewed_commit", …)` reproduce the pinned text exactly (including the `"one line of "` + `"prose"` continuation seam), and `tests/test_review_launcher.py:1879` keeps its expectation unmodified.
- The findings-gate transcript is byte-stable: `finding_reviewer_identity_refusal` with `launching=False` returns the two old messages, and the `check(…)` fallback supplies the old pass wording (`src/agentmarshal/journal/gate.py:225`).
- `artifact_path` exists once (`src/agentmarshal/journal/artifacts.py:17`), read by both callers; `_artifact_path` is gone from `gate.py`. `validate.py`'s stricter journal-artifact check answers a different question and is untouched.
- All five pre-run refusals happen before `_run_reviewer`, and every scenario in the change's `specs/` is named by a test docstring. The displaced docstring on the commit-prompt test does not orphan its old scenario — `tests/test_brief.py:70` still names it.
- `reviewed_commit` stays in `_VERDICT_REQUIRED` for a reason: `tests/test_review_launcher.py:1624` pins the "missing required field(s): reviewed_commit" message, so the conditional in `_parse_verdict` is load-bearing rather than gratuitous.
- Sidecar finding review resolves the project root from `journal_root.parents[1]`, matching the gate, and needs no reachable host — consistent with the new `docs/sidecar.md` row.

**Advisory findings:**

ADV-001-design-oversized-artifacts-overclaim — `openspec/changes/archive/2026-09-18-review-binds-to-a-finding/design.md:51` heads a decision "Binary and oversized artifacts are named, not embedded", but nothing in `_finding_review_prompt` withholds content by size: only a `UnicodeDecodeError` suppresses embedding. The same document contradicts the heading at line 132 ("No limit is invented here"), as does the contract's Non-Goals. This is the exact "a spec that claims more than the code does" defect line 84 of that file says the project keeps finding in its own documents.

ADV-002-duplicate-contract-parse — `src/agentmarshal/journal/review.py:829` calls `parse_contract_text` on bytes that `load_task_status` has already parsed into `task.contract` two dozen lines earlier (`status.py:92`), giving the finding path two parses and two sources for `decisions`/`documents`/`extensions`. The commit path needs its second parse because the snapshot contract is a different file; the finding path reads the same `contract.md` the status projection read, so `task.contract` would do.

ADV-003-design-commit-template-untouched-claim — `design.md:59` states "The commit prompt template is untouched", and gives that as the reason the finding prompt is a separate template ("editing the shared one would change the pinned bytes"). `_REVIEW_PROMPT` was in fact edited into `{prose_instruction}`/`{verdict_protocol}` placeholders, which the same document's Risks section at line 126 describes as the intended shape. What is untouched is the rendered bytes, not the template; as written the decision's stated reason no longer matches what was done.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "06652af8e316cba4680e8fd639c5337fe8bfd201", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-001-design-oversized-artifacts-overclaim", "ADV-002-duplicate-contract-parse", "ADV-003-design-commit-template-untouched-claim"]}
AGENTMARSHAL_VERDICT_END
