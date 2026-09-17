I reviewed the diff against the contract, the two named documents, and ADR-0005/ADR-0008, reading the working-tree source rather than the patch alone. Python execution is blocked in this sandbox, so verification is static: I traced the parser and renderer by hand against every new and pre-existing assertion in `tests/test_capture.py`, `tests/test_gate.py`, `tests/test_review_launcher.py` and `tests/test_project.py`.

What holds up:

- All ten scenarios in `openspec/changes/archive/2026-09-17-adopter-small-defects/specs/` are demonstrated by a test whose docstring names them, and the archived deltas match `openspec/specs/leak-scan/spec.md` and the `reviewer-adapter` addition verbatim.
- No output path carries a secret. `identification` is a signature name or a position; `safe_path` (`capture.py:299`) masks only the offending span, which is what keeps two files under one marker-named directory distinct rather than collapsing into one set member.
- The gate and the standalone command both go through `render_leak_hits`, and `tests/test_gate.py:1761` pins both lines in one test, so they cannot drift.
- The suppression key compares the *raw* parsed path against `PROJECT_CONFIG_RELPATH` while the reported path is masked — the right way round. The sidecar cases pass `config_path=""`, which suppresses nothing, the safe direction. `sidecar and journal_root is not None` in `gate.py:1119` is equivalent to `sidecar` because `journal_root` is reassigned at `gate.py:601`, so the two conditions in that block cannot disagree.
- The `--src-prefix`/`--dst-prefix` flags are applied after config in git's option parsing, so they do beat `diff.srcPrefix`/`diff.dstPrefix`/`mnemonicPrefix`; `tests/test_gate.py:1827` exercises that, and even if `diff.noprefix` won, `_diff_path` would leave a prefixless path intact rather than eat a character.
- `diagnostics_note` is bound on every path that reaches the code after the `with` block in `launch_review`, matching how `review_result` and `reviewer_output` already work. The `/dev/null` destination still scans its added lines (`capture.py:_diff_path` → `"(unknown file)"`), which is the fail-open direction that matters.
- The byte-for-byte 0.3.0 transcript test and the pinned prompt tests use benign content and an unchanged prompt, so they pass unmodified; `tests/test_placement.py:286` was updated only for the headline the amendment authorised.
- The departure from the contract's "sole occurrence" bound is recorded in `design.md`, which acceptance criterion 1 permits.

One advisory finding:

**leak-scan-self-match-only-in-the-diff-scan** — the new "not matched against its own declaration" rule lives only in `scan_diff_for_leaks` (`src/agentmarshal/journal/capture.py:406`). `scan_for_leaks`/`assert_no_leaks` (`capture.py:343`, `capture.py:362`) still accept a `private_markers` tuple and still report `private-marker` for a marker that occurs only in the config that declares it — and that is the entry point that *refuses* rather than warns, which is the shape proposal 020 actually reported ("a journal transaction was refused"). The published requirement is worded unconditionally ("The scan SHALL NOT report a private-marker hit whose only occurrence..."), and `design.md` explains why the artefact refusal keeps a category-only *shape* but never says why the self-match rule does not reach it. This is not a live defect: the only caller, `backfill.py:187`, passes no markers at all, so the self-match is unreachable in this codebase today — it becomes reachable the moment any capture path passes markers. Worth a sentence in `design.md` or a follow-up rather than a change here.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e7a6074430a6173df7076c71ccabde21498f277f", "verdict": "approved", "findings": [], "advisory_findings": ["leak-scan-self-match-only-in-the-diff-scan"]}
AGENTMARSHAL_VERDICT_END
