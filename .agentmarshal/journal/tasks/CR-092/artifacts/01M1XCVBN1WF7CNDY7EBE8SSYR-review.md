I reviewed the diff statically against the contract, the delta spec, design.md, and the surrounding code. **I could not execute anything** — `uv run pytest`, `python3 -m pytest`, `python3 -m compileall`, and `npx openspec validate --all` all required approval that was not granted. So acceptance criteria 1 ("tests pass unmodified"), 3 ("byte-for-byte 0.3.0 transcript test"), and 4 ("`openspec validate --all` passes") are verified by reading, not by running. I traced each of them by hand below.

## What I checked

**Criterion 1 — every scenario demonstrated by a named test.** All nine scenarios in `openspec/changes/archive/2026-09-07-retire-review-temp-copy/specs/review-evidence/spec.md` map to a docstring: `test_review_launcher.py:554`, `:636`, `:777`, `:832`, `:982`; `test_journal.py:564`, `:618`, `:698`; `test_report.py:269`; `test_gate.py:953`, `:1021`; `test_findings.py:521`; `test_validate.py:126`. The two CR-054 temp-copy tests (`test_blocking_verdict_keeps_the_reasoning_behind_its_findings`, `test_advisory_findings_on_an_approval_keep_the_reasoning_too`) are replaced by one parametrized test covering both shapes, and the rejected-verdict test at `:636` is untouched.

**Criterion 2 — one pre-write refusal.** `validate_record_for_write` (`records.py:653`) is a faithful lift: the supplied-`recorded_by` rejection, identity derivation, `_validate_record`, task match, finding binding, and the ULID check run in the same order they did inside `write_record`, and `write_record` now calls it with an already-generated identifier so the generated-id case is still checked. `"must name a finding in the same task"` exists exactly once (`records.py:690`). Moving `generate_ulid()` ahead of validation only burns a monotonic id on refusal — harmless.

**Criterion 3 — collision check.** `evidence_changes` is a strict superset of `added_records` in the embedded case and is zeroed in the sidecar branch (`gate.py:655`), so the sidecar transcript line is unchanged; the printed text is still the record line, as the contract asked. The check sits outside the `journal_only` lane, so the new gate test — whose candidate touches only a journal path — actually reaches it. `base_tree` is the full `ls-tree` of the base commit, so artifact paths are visible to it.

**Criterion 4 — archive.** The baseline `openspec/specs/review-evidence/spec.md` carries the MODIFIED requirement text verbatim, both new ADDED requirements, and the split of the old combined `status`/`report` scenario. The archive directory name and `.openspec.yaml` match the sibling `2026-09-06-keep-review-prose`.

**The orphan window.** `_prepare_artifact_directory` calls `_prepare_record_directory` first, so a symlinked or non-directory records path fails before any artifact byte is written; `_record_path`'s task-id and record-type guards are already covered by `write_artifact` and `_validate_record`. The residual window really is only the exclusive-create failure the design names.

---

`ADR-STALE-TEMP-COPY` — `docs/adr/ADR-0005-evidence-capture-and-format.md:29-30` still says reviewer output "is now preserved best-effort in a temporary file when a verdict is refused **or names findings**", and `docs/adr/ADR-0004-journal-data-model.md:109-110` repeats it as "reviewer output that names findings is also preserved best-effort in a temporary file"; this change deletes exactly the "names findings" behaviour, so both status notes now describe shipped behaviour that no longer exists — a contradiction with ADR-0005, which this contract names as a decision. It is advisory only because `docs/adr/` is outside the contract's scope and the gate would have refused the edit; it needs a follow-up.

`TAUTOLOGICAL-TEMP-COPY-ASSERT` — `tests/test_review_launcher.py:139` `_kept_findings_outputs` globs `agentmarshal-verdict-findings-*.txt`, but the only call site that ever passed that prefix to `_preserve_output` was deleted, leaving `review.py:214` with a `prefix` parameter that no caller overrides; the three `assert _kept_findings_outputs(...) == []` checks at `:794`, `:821` and `:842` are therefore true by construction and would not notice a temp copy written under any other prefix. The companion `"kept at" not in captured.err` assertions are what actually pin the scenario; the glob and the now-dead parameter are residue worth removing.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "a002e6b064e74b741f9e5b759fd78a4f1679107d", "verdict": "approved", "findings": [], "advisory_findings": ["ADR-STALE-TEMP-COPY", "TAUTOLOGICAL-TEMP-COPY-ASSERT"]}
AGENTMARSHAL_VERDICT_END
