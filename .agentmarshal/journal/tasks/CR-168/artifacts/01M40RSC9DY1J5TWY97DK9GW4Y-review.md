I reviewed the diff against the contract, the gate-lanes spec, the settings module, the fixtures, and the doc pins. Summary of verification:

**Implementation** (`src/agentmarshal/journal/gate.py:1248-1283`) — the count is computed over `task.records` (the record set `load_task_status` already validated, so no extra read), filtered to `record_type == "review"` and `verdict == "changes_required"`, which is exactly the vocabulary `records.py:168` validates. It is emitted through `say`, never `check`, so `violations` is untouched and the exit status cannot move; it is the last line before the CLI's verdict line (`cli.py:738-761`), in all three call sites that print `report.lines`. The guard is `not journal_only`, and `journal_only` is already forced false in a sidecar (`gate.py:753-760`), so the sidecar host-journal candidate takes the implementation lane and gets the line — matching ADR-0008 decision 2 and the amended contract. The threshold read is `changes_required_threshold(journal_root.parents[1])`, the same project-root resolution `markers_from_config` uses for a sidecar and equal to `project_root` when embedded. The `(OSError, ValueError)` catch genuinely covers every failure mode of that reader: missing file (`FileNotFoundError`), unparseable JSON (`JSONDecodeError`), bad encoding (`UnicodeDecodeError`), non-object file (`ValueError`), and `ProjectSettingsError` for a malformed key or a malformed `review` section.

**Spec and change artifacts** — the delta is an ADDED requirement with five scenarios, merged verbatim into `openspec/specs/gate-lanes/spec.md:82-120`; the "A default run is unchanged" requirement already licenses a deliberate fixture change and is correctly left unreworded. Each of the five scenarios has a test whose docstring names it (`tests/test_gate.py:589-712`), and the threshold test asserts both the `WARN` mark and that the run still exits 0.

**Fixtures and docs** — the fixture diff is exactly one added line on `embedded-implementation`, `sidecar-implementation` and `sidecar-journal-only`, with `embedded-journal-only` untouched and no `.stderr`/`.exit` change. `docs/quickstart.md:382` is pinned byte-for-byte by `test_the_main_path_prints_the_documented_gate_transcript`, and the other quickstart assertion (`endswith("gate: passed\n")`) still holds with the line inserted before the verdict.

Two advisory notes, neither blocking:

`docs/sidecar.md` is left describing a gate transcript that no longer exists: the block at `docs/sidecar.md:221-230` omits the new count line, and the prose at `docs/sidecar.md:285` says `complete` "prints the advisory notice and the same nine check lines the gate printed" when a sidecar run now prints ten. No test pins that page and `docs/sidecar.md` is outside the contract's scope list, so this is a follow-up rather than a defect in this change.

The count includes finding-bound review records, not only commit-bound ones: `gate.py:1256-1260` filters on `record_type`/`verdict` alone, so a `review --reviewed-finding` record with verdict `changes_required` (a verdict `records.py:_validate_review_record` permits on a finding review, and which `run_findings_gate` treats as blocking) increments the "times the task was returned" signal. This is within the letter of the requirement's "every review record of the task", so it is not a violation — but the requirement's qualifier "whatever commit it names" reads commit-bound, and the `status` count under the same ADR decision will need to make the same choice to stay consistent.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "cdb26d82c692ddb1299704e16a8998d98e384317",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "advisory-sidecar-doc-transcript-stale",
    "advisory-finding-bound-reviews-counted"
  ]
}
AGENTMARSHAL_VERDICT_END
