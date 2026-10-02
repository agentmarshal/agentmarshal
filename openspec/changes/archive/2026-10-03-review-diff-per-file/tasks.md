## 1. The diff reaches the reviewer per file

- [x] 1.1 `review` captures the merge-base diff as bytes and decodes it
  through `decode_diff_per_file`, the helper the leak scan already uses —
  verify: reproduction test in `test_review_launcher.py` (a text file plus a
  file of non-UTF-8 bytes launches the reviewer and no traceback escapes).
- [x] 1.2 A file that did not decode is named in the prompt, which says how
  unreadable bytes are marked, and in the command's stderr — verify: tests
  asserting the prompt caveat and the `LaunchedReview` diagnostics note the
  CLI prints.

## 2. No other git output can traceback

- [x] 2.1 `_run_git` captures bytes and decodes stdout and error detail with
  escapes, so merge-base, ls-tree, rev-parse and error text surface a
  printable result or a named refusal; a non-UTF-8 path is named escaped —
  verify: tests feeding non-UTF-8 ls-tree output and non-UTF-8 error text.

## 3. Carried advisories from the leak-scan review

- [x] 3.1 The C-quoted branch of `_header_name` drops the `b/` prefix —
  verify: a capture test on an undecodable section whose only name is the
  C-quoted `diff --git` line.
- [x] 3.2 `docs/sidecar.md` lists the `WARN: leak-scan could not decode as
  UTF-8 (added bytes still searched)` line beside the other lines the scan
  can append — verify: read it against `gate.py`.
- [x] 3.3 The two docstrings that carry a literal `\x0c` state it as an
  escape — verify: `ruff`/`pytest` clean, docstrings read `\x0c` as text.

## 4. Change hygiene

- [x] 4.1 Every delta-spec scenario is demonstrated by a test whose docstring
  names it — verify: `pytest -q` and a read of the docstrings.
- [x] 4.2 Archive with `openspec archive` into
  `openspec/specs/reviewer-adapter/` — verify: the command's own output and
  the merged spec.
