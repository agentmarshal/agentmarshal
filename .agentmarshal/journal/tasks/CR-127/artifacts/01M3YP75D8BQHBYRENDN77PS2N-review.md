I reviewed the implementation against `openspec/specs/leak-scan/spec.md`, the archived delta, `design.md`, and the contract's acceptance criteria.

**What I verified**

- `decode_diff_per_file` (`src/agentmarshal/journal/capture.py:526`) splits on a zero-width `^(?=diff --git )` boundary, so sections reassemble byte-exactly and a clean diff takes the old strict-decode path unchanged. The boundary cannot be forged from content: every hunk-body line carries a `+`/`-`/space/`\` prefix.
- `_decode_section_lossy` matches design.md on both decisions: headers via `backslashreplace` (so a raw `\xff` path is named printably and the name agrees with the path a hit reports), content via `replace` (U+FFFD is non-word, so `\b(?:ghp|…)_[A-Za-z0-9]{36}\b` still matches a token abutting an invalid byte). `must_name` is set only for pre-hunk or `+` lines, so a deleted binary is not named — matching the spec's "a file whose undecodable bytes are all removed is not named".
- The `splitlines()` → `split("\n")` change in `scan_diff_for_leaks` is correct and necessary: `\x0b`, `\x0c`, `\x1c`–`\x1e`, `\x85` are valid UTF-8, survive the lossy decode inside a `+` line, and as prefix-less fragments would drain both hunk counters and end the body early. Header parsing is unaffected because git terminates patch lines with `\n` only.
- One helper now owns the pinned flags: `grep` finds `--no-textconv`/`--dst-prefix` only in `leak_scan_diff` (`gate.py:535`); both `run_gate` and `_run_leak_scan` call it, and the `_run_leak_scan` comment was refreshed. `_run_git` still strict-decodes, so the gate's existing non-UTF-8 path refusal via `diff --name-status -z` (pinned at `tests/test_gate.py:1505`) is intact — design.md records that as an explicit non-goal.
- Masking holds: `render_undecodable_files` routes every name through `safe_path`, same as hit paths, and both callers use it (gate bounded at 20, command unbounded) — so the marker-named-directory and key-named-file cases print `<private marker #1>` / `<aws-access-key-id>`.
- All ten delta scenarios have a test whose docstring names them, across `tests/test_capture.py`, `tests/test_gate.py` and `tests/test_leak_scan.py`, including the proposal-026 reproduction for both the gate and the command and the real-git `bytes(range(256))` fixture. The change is archived under `openspec/changes/archive/2026-10-03-per-file-leak-scan/` and the requirement is appended verbatim to `openspec/specs/leak-scan/spec.md`.

**Findings**

`docs-enumeration-stale`: `docs/sidecar.md:245-252` enumerates what the gate's leak scan can append to the transcript — nothing, a hit line, or `WARN: leak-scan skipped (<reason>)` — and that list is now incomplete, since the gate can also append `WARN: leak-scan could not decode as UTF-8 (added bytes still searched): …`. `docs/` is outside the contract's scope, so not editing it was right, but AGENTS.md asks for such a path to be named as a departure in the final report.

`header-name-quoted-prefix-not-stripped`: in `_header_name` (`src/agentmarshal/journal/capture.py:446`) the C-quoted branch does not do the job its docstring claims. For `marker = ' "b/'`, `marker.strip()` is `"b/`, so `token` begins with a quote, `token.startswith("b/")` is false, and the `b/` prefix the function exists to drop is returned as part of the name (`"b/path` instead of `path`). It is near-unreachable with real git output — a C-quoted path is pure ASCII, so such a section decodes strictly and never reaches this fallback — which is why it is advisory rather than blocking.

**One thing I could not do:** the sandbox refused `uv run pytest` / `ruff` / `mypy`, so I could not execute acceptance criterion 5 ("the full CI sequence passes"). My review of it is static: I traced each new test's fixture through the implementation by hand and checked line lengths, imports, and strict-typing of the new signatures, and found nothing that should fail, but I did not observe a green run.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "d3c200db9dce8c000f8484c7932171c544076a43",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["docs-enumeration-stale", "header-name-quoted-prefix-not-stripped"]
}
AGENTMARSHAL_VERDICT_END
