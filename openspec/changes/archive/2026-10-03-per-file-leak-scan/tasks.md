## 1. The scan reads per file

- [x] 1.1 `decode_diff_per_file` in `capture.py` decodes a `git diff` byte
  stream per `diff --git` section; a section that fails strict decode is
  decoded lossily (headers escaped, content U+FFFD-marked) so its bytes are
  still searched, and its file is collected for naming — verify: capture
  tests, including an escaped non-UTF-8 path.
- [x] 1.2 One helper runs the pinned diff (`--text`, `--no-textconv`,
  `--no-ext-diff`, the fixed prefixes) for both callers and returns the
  decoded text plus the undecodable names — verify: grep that the gate and
  `_run_leak_scan` call the same function, and that no second copy of the
  flag list remains.
- [x] 1.3 Reproduction of proposal 026's fourth finding: a commit adding a
  text file with a GitHub-token-shaped string and a file of random bytes
  reports the string in both the gate's transcript and the `leak-scan`
  command — verify: one test each.

## 2. What could not be read is named

- [x] 2.1 The gate warns, naming each undecodable file, and the warning never
  becomes a violation — verify: gate test on a binary-only candidate.
- [x] 2.2 The command names every undecodable file; undecodable-only exits 0
  and never tracebacks — verify: command tests, including the non-UTF-8 path
  case updated from refusal to escaped naming.

## 3. The guarantees that were pinned stay pinned

- [x] 3.1 Existing leak-scan and gate tests pass unmodified except the one
  whose behaviour this change deliberately replaces — verify: pytest.

## 4. Fix round 1 — the scan reads all of an added line, and names stay safe

- [x] 4.1 `scan_diff_for_leaks` splits on `"\n"` only: a control byte inside
  an added line no longer ends the hunk early — verify: capture test with the
  token after `\x0c`, and a real-git command test with the token appended
  after `bytes(range(256))`.
- [x] 4.2 Only a section that lost bytes the scan reads is named — an
  undecodable deletion is not — verify: adjusted capture test.
- [x] 4.3 Undecodable names go through `safe_path` via one shared renderer
  (`render_undecodable_files`) at both callers, which also owns the bounded
  "and N more" phrasing — verify: marker-path and key-path tests on the gate
  and on the command.
- [x] 4.4 Refresh the stale `_run_leak_scan` comment (diff goes through
  `leak_scan_diff`; non-UTF-8 content is a named degradation, not a refusal)
  — verify: read the comment against the code.
