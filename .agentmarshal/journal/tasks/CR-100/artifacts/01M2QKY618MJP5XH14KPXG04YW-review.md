I reviewed the working tree at the snapshot against CR-100's contract, the two named decisions, and the leak-scan / reviewer-adapter capabilities.

## What I verified

**Acceptance 1 — scenario coverage.** All eight scenarios in the archived change's `specs/leak-scan/spec.md` and both in `specs/reviewer-adapter/spec.md` have a test whose docstring names them verbatim (`tests/test_capture.py:241,337,353,377,485,502,521`, `tests/test_gate.py:1761`, `tests/test_review_launcher.py:654,730`). The one departure from the contract's threat model — the declaring configuration's own path is never reported, not merely when it is the sole occurrence — is recorded in `design.md` under an explicit heading, which acceptance 1 permits.

**Acceptance 2 — nothing secret in the output.** `LeakHit.identification` is a signature name or a one-based position; `safe_path` (`src/agentmarshal/journal/capture.py:299`) masks only the offending span in the path, so two files under one marker-named directory stay two hits. `tests/test_capture.py:485` asserts the marker value is absent from the rendering, and `tests/test_capture.py:377` does the same for a path that is itself a key.

**Acceptance 3 — one renderer.** `render_leak_hits` is the single call site for both `src/agentmarshal/cli.py:1308` and `src/agentmarshal/journal/gate.py:1163`, and `tests/test_gate.py:1761` pins the gate's line byte-for-byte alongside the standalone stdout.

**Acceptance 4 — self-match.** `config_path` defaults to the single `PROJECT_CONFIG_RELPATH` constant, read by the scan default, the gate and the CLI; in a sidecar both callers pass `""`, which suppresses nothing — the safe direction, and correct, since the declaring file lives in the sidecar while the diff is the host's.

**Acceptance 5 — reviewer diagnostics.** `_keep_diagnostics` returns `None` on empty stderr, so a silent command stays silent; the note reaches stderr on success and is appended to every later rejection through `_with_diagnostics`. The byte-for-byte 0.3.0 transcript test exercises a clean candidate, so no WARN line enters it, and the pinned prompt test (`tests/test_review_launcher.py:1259`) is untouched and does not use the stub. `_kept_any_outputs` globs `agentmarshal-*.txt`, which now also covers the new prefix — the existing "keeps nothing" tests still hold because their stubs write no stderr.

I could not execute the suite in this sandbox; the above is static verification against the sources.

## Findings

The comment at `src/agentmarshal/journal/capture.py:469-472` states that "any second occurrence, including one in the same candidate diff, leaves every hit reportable", but the loop it introduces does the opposite — `elsewhere` filters the declaring path out unconditionally, exactly as `design.md`'s recorded departure and `tests/test_capture.py:463` require; the comment is a leftover from the pre-departure draft and contradicts both the code below it and the design note.

The `-c core.quotePath=false` pin added at `src/agentmarshal/journal/gate.py:1136` and `src/agentmarshal/cli.py:1284` changes behaviour for a repository holding a path whose bytes are not valid UTF-8: git previously C-quoted such a header into ASCII and the scan ran, whereas now the raw bytes reach the strict UTF-8 decode in `_run_git`, so the gate degrades to `WARN: leak-scan skipped` and the standalone command exits 1 — a narrowing of a security control that neither acceptance criterion asks for and `design.md` does not mention (the quoted justification beside it covers `diff.mnemonicPrefix`, not quoting).

Neither is blocking: the first is a comment, and the second is a narrow, loudly-announced degradation consistent with the project's existing "non-UTF-8 is a controlled refusal" policy.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "b87481b02b9bd037eae16b5804a2806f93f6d4dd", "verdict": "approved", "findings": [], "advisory_findings": ["A-001-stale-self-match-comment", "A-002-quotepath-pin-narrows-scan"]}
AGENTMARSHAL_VERDICT_END
