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
