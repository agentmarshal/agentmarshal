I reviewed commit `1ec3e82cf67f13c9de3f1861f168b2e5825241bf` against contract CR-092, the named decisions (ADR-0005, ADR-0008, ADR-0009), the archived change under `openspec/changes/archive/2026-09-07-retire-review-temp-copy/`, and the baseline `openspec/specs/review-evidence/spec.md`.

## What I verified

**Acceptance 1 — scenario coverage.** Every scenario in the delta spec has a test whose docstring names it: `the model review path keeps its output` (`tests/test_review_launcher.py:556`), `an accepted verdict keeps no copy outside the journal` (`:779`), `a rejected verdict still keeps the prose` (`:638`, untouched by the diff), `a refusal the writer cannot foresee is named as a limit` (`:834` and `tests/test_journal.py:698`), `the human review path attaches prose` (`tests/test_journal.py:564`), `report totals the prose` (`:618`), `status names the prose` (`tests/test_report.py:269`), `a binding to an unknown finding writes nothing` (`tests/test_findings.py:521`), `two candidates add the same artifact path` (`tests/test_gate.py:953`). The two CR-054 temp-copy tests are replaced by the parametrized superseding test; the rejected-verdict test is unmodified.

**Acceptance 2 — one statement of the pre-write refusals.** `validate_record_for_write` (`src/agentmarshal/journal/records.py:653`) holds shape, task match, finding binding, recorder identity and ULID; `write_record` (`:715`) and `submit_review` (`src/agentmarshal/journal/submit_review.py:72`) both call it. `"must name a finding in the same task"` now exists at exactly one site (`records.py:690`). Error precedence is preserved — the ULID check still runs last, and passing the generated identifier keeps `record_id=None` behaviour identical.

**Acceptance 3 — collision rule.** `gate.py:1027` now filters `evidence_changes`, which is `_is_append_only_evidence_path` (records ∪ artifacts), and is emptied under sidecar at `:655`, so the sidecar transcript is untouched. Both the PASS and FAIL strings are byte-identical to before, so the 0.3.0 transcript test cannot shift. `base_tree` (`:609`) is unfiltered in non-sidecar mode, so an artifact collision is genuinely reachable, and `journal_only` only short-circuits the review/scope lane at `:734`, not the collision check.

**Acceptance 4 — archive fidelity.** The baseline spec faithfully absorbs both MODIFIED requirements (all four scenarios restated in order) and both ADDED requirements; `.openspec.yaml` matches the sibling archive's layout.

**Acceptance 5 — tasks and docs.** All checkboxes ticked; `docs/quickstart.md:72-79` and `:283-287` no longer describe a temp file on the accepted path; `docs/overview.md:158` was already accurate, matching tasks.md 4.2's "overview unchanged".

**Orphan window.** `write_artifact` failure and record-validation refusal both yield `artifact_ref=None`, so `_reject` still preserves prose to a temp file — which is why `test_record_validation_failure_also_keeps_the_output` (approved + non-empty findings, caught by the preflight) still passes. Only a post-pin write failure sets `artifact_ref`, and `launch_review` (`review.py:434`) then raises without a second copy. That is exactly ADR-0008's placement rule and the design's "named, not deleted".

## Findings

`ADV-001-stale-adr-status-notes` — `docs/adr/ADR-0005-evidence-capture-and-format.md:29` and `docs/adr/ADR-0004-journal-data-model.md:109` still state that reviewer output is preserved best-effort in a temporary file when a verdict "is refused **or names findings**". The findings half is now false: only the rejected-verdict path keeps a temp copy. ADR-0005 is a named decision of this contract, and `docs/adr/` is outside the contract's `scope`, so the implementer was right not to edit it — but design.md's Risks section does not record the departure either, which acceptance criterion 1 asks for.

`ADV-002-design-overstates-the-preflight` — `openspec/changes/archive/2026-09-07-retire-review-temp-copy/design.md:23` states the pre-write refusal "checks what `write_record` would refuse **without touching the filesystem**". The shipped `validate_record_for_write` necessarily touches it: it calls `read_records` for the finding binding and `resolve_recorded_by(_project_root_for(...))` for identity. The implementation is correct — the binding cannot be checked any other way — but the archived design record, now permanent, mis-describes it and no departure note was added.

`ADV-003-unreachable-except-clause` — `src/agentmarshal/journal/submit_review.py:87`, the `except ReviewSubmitError: raise` guard is unreachable by construction: `ReviewSubmitError` derives from `Exception` and is not a subclass of `JournalRecordError`, `TaskStatusError`, `OSError` or `ValueError`, so the following clause could never have swallowed it. It reads as load-bearing to the next reader of this function.

## One limitation in this review

I could not execute `uv run pytest -q` or `openspec validate --all` — Bash approval was declined and the snapshot has no `.venv`. The test-pass and validator claims in acceptance criteria 3 and 4 are verified by inspection of the transcript strings, the report line format (`report.py:141-151`, task-scoped output omits the Summary line and `decision` stays `None` without a completed record), and the archive layout — not by running them.

None of the three findings is a defect in the shipped behaviour; two are documentation truth, one is dead code.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "1ec3e82cf67f13c9de3f1861f168b2e5825241bf", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-001-stale-adr-status-notes", "ADV-002-design-overstates-the-preflight", "ADV-003-unreachable-except-clause"]}
AGENTMARSHAL_VERDICT_END
