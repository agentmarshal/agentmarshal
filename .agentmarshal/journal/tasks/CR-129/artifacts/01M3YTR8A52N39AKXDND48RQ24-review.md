I reviewed the diff against the contract, the merged spec, design.md, and the surrounding code in `review.py`, `capture.py`, `gate.py`, `cli.py` and the test suite.

**What I verified**

- `launch_review` now captures the diff with `_run_git_bytes` and decodes it through `decode_diff_per_file(..., name_all_losses=True)` (`src/agentmarshal/journal/review.py:1168`), the same helper `leak_scan_diff` uses, with `--src-prefix=a/ --dst-prefix=b/` pinned so `_diff_path`'s `b/`-stripping stays true under `diff.mnemonicPrefix`.
- `name_all_losses` is additive: it only widens the naming rule for sections that already failed strict decode, and `leak_scan_diff` passes nothing, so the gate and `leak-scan` keep CR-127's narrower rule (`gate.py:572`).
- Reviewer-facing note rides `{diff_note}` ahead of `Diff:`; with no losses it renders `""`, so the byte-for-byte pinned prompt test at `tests/test_review_launcher.py:2118` and the `"\n\nDiff:\n"` split at `tests/test_review_launcher.py:698` are unaffected.
- Operator-facing note rides `diagnostics_note`, which `cli.py:752` prints to stderr, is masked through `render_undecodable_files`/`safe_path` with markers read exactly as the gate reads them (sidecar config vs. merge-base tree), and survives later rejections via `_with_diagnostics`. The self-cause bug (`raise error from error` when the note is `None`) is fixed and tested.
- Every git read in `review.py` is now byte-capturing: `_run_git` escapes with `backslashreplace`, `_extract_snapshot`'s error detail too, and the `ls-tree` fallback goes through `_run_git`. `markers_from_tree`'s own `GateError` is caught and re-raised as `ReviewLaunchError`.
- All six delta-spec scenarios have a test whose docstring names them. `_header_name`'s quoted branch now returns `"…"` with `b/` gone (traced by hand against the new capture test's expectation `'"\\303\\251.bin"'`). `docs/sidecar.md` matches `gate.py:1178-1191` line for line, and both `\x0c` docstrings are now `r"""`.
- No import cycle from `review.py` → `gate.py` (gate imports no module that reaches review).

I could **not** execute `pytest`, `ruff` or `mypy`: Python execution is blocked in this sandbox (`python3 -V` was refused). My read on the "full CI sequence passes" criterion is therefore static only — I checked line lengths in the new code by hand, the `r"""` docstrings, bugbear's `raise ... from` rule, and that mypy strict does not enable `possibly-undefined` (which the new `try` around `snapshot_builder`/`prompt_builder` would otherwise trip).

**Advisory findings**

`review-diff-unpinned-against-diff-drivers` — `review`'s `git diff` at `src/agentmarshal/journal/review.py:1169-1177` pins the prefixes but not `--no-textconv`/`--no-ext-diff`, which `leak_scan_diff` pins (`src/agentmarshal/journal/gate.py:567-568`) precisely so a repo's own diff driver cannot rewrite or redact what the checker sees. design.md reasons about `--text` and the prefixes but is silent on these two, so a configured textconv/external driver can still change the text the reviewer judges. Low exploitability (the driver command must already be in local config, and the reviewer also gets the full tree snapshot), and out of this task's encoding scope — worth a line in design.md or a follow-up rather than a change here.

`marker-read-refusal-untested` — the new refusal at `src/agentmarshal/journal/review.py:1206-1209` turns a malformed or unreadable base-side `project.json` into an outright `ReviewLaunchError`, but only when the diff also has an undecodable section. That is a deliberate design.md decision and a genuine behaviour change (the gate degrades the same failure to a warning), yet no test exercises it; tasks.md 5.3 only claims the masking test.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "6fc466c806f1b6e0e050bc701559395c7a5d35f9", "verdict": "approved", "findings": [], "advisory_findings": ["review-diff-unpinned-against-diff-drivers", "marker-read-refusal-untested"]}
AGENTMARSHAL_VERDICT_END
