## Context

`git diff` output is a byte stream, and `review`'s `_run_git` decoded it —
and every other git output it reads — strictly as UTF-8, so one undecodable
byte anywhere raised `UnicodeDecodeError` before the reviewer was launched
(proposal 037). CR-127 fixed the same defect for the leak scan and left a
helper shaped for reuse: `decode_diff_per_file` in `capture.py` splits a diff
byte stream on `diff --git` boundaries, decodes each file section on its own,
lossy-decodes a section that fails (header lines escaped, content bytes
marked with U+FFFD), and returns the names of the files that lost bytes.
Its decisions apply here unchanged: split on `"\n"` only, lossy decode of
undecodable content, escaped header names, `safe_path` for printed names.

## Goals

- `review` never fails on a diff because of encoding.
- The reviewer knows which files it could not be shown in full.
- The command's own output names the same files.
- No other git output the launch reads can raise a traceback on bytes that
  are not UTF-8; a path whose bytes are not UTF-8 is named escaped.

## Non-Goals

- A diff-size limit (deferred, as in CR-127).
- Changing the verdict protocol or what the reviewer is asked.
- `cli.py`: the command's output channels are what `_run_review` already
  prints — the undecodable-file note rides the existing diagnostics channel.

## Decisions

- **The diff is captured as bytes and decoded through
  `decode_diff_per_file`, not `leak_scan_diff`.** Both are the helper CR-127
  built, but `leak_scan_diff` pins `--text` so the *scanner* can read bytes a
  repository marks binary; a reviewer's diff is better served by git's usual
  rendering, where a binary file is already named as binary ("Binary files
  differ") instead of arriving as pages of U+FFFD. `review` therefore keeps
  the rendering it always used — no `--text` — and shares the per-file
  decode. What it no longer keeps is the unpinned prefixes: the name parser
  strips `b/`, which `diff.mnemonicPrefix` or `diff.dstPrefix` would bend
  into `c/name` or worse in the prompt and the note, so `review` pins
  `--src-prefix=a/ --dst-prefix=b/` exactly as the leak scan does — under
  default configuration the emitted diff is byte-identical to what it was.
- **A file is named whenever its section lost bytes, not only when the scan
  would have read them.** The helper's default rule is the scan's: name a
  section only when the loss hit headers or added lines, because a
  removed-only loss gave the scanner nothing to read. That rule is wrong
  for `review`, which shows the whole decoded text — a latin-1 line a
  commit removes still reaches the reviewer as a U+FFFD-marked `-` line and
  could be read as the file's real content. `decode_diff_per_file` grows a
  `name_all_losses` flag that names every section that lost bytes; the leak
  scan keeps the default rule, `review` passes the flag.
- **A file that does not decode is shown as the lossy text the helper
  produced, with a note naming it.** The open question — lossy text, a named
  placeholder with its size, or both — is settled by what the reviewer is
  for: judging the candidate. A placeholder with a byte count says only that
  something unreadable exists; the lossy text shows every byte that did
  decode — for a mostly-text file with a few stray bytes that is nearly all
  of it — and marks the spans that did not (U+FFFD in content, `\xNN` escapes
  in header lines). Shown alone it could mislead: a reviewer might read
  marked spans as the file's real content. So the prompt names each
  undecodable file ahead of the diff and says how unreadable bytes are
  marked — the text stays, and it cannot be mistaken for a faithful copy.
  Nothing is dropped in silence: the file is in the diff, is named in the
  prompt, and is named on stderr.
- **The operator is told through the diagnostics channel, with the names
  masked as the gate masks them.** `cli.py` prints
  `LaunchedReview.diagnostics_note` to stderr; the launcher composes the
  undecodable-file note into it ahead of any kept-stderr note, and attaches
  it to later launch rejections the way kept diagnostics already ride. The
  names render through `render_undecodable_files`, and the markers it masks
  with are read as the leak scan reads them — the sidecar's own config in a
  sidecar, the merge-base tree's `project.json` otherwise — because a file
  name can itself be the secret and stderr is where CR-127's no-secret-paths
  guarantee holds. The prompt's names stay raw: they must match the names
  inside the diff text the reviewer is shown, which masking could not change
  anyway. A marker read that fails is a named refusal rather than unmasked
  names on stderr — naming is required, so "cannot read the marker config"
  is the honest out. The gate's `GateError` is caught and re-raised as
  `ReviewLaunchError`, so the launcher's error surface is unchanged.
- **Every remaining git read decodes with escapes.** `_run_git` captures
  bytes and decodes stdout and stderr detail with `backslashreplace`: a SHA
  is unaffected, a listing or error message that carries a non-UTF-8 path
  names it as `\xNN` escapes, and an undecodable `merge-base`/`rev-parse`
  result degrades into the ordinary "did not resolve" refusal rather than a
  traceback. The diff is the one output decoded per file instead, because a
  whole-stream lossy decode would erase which file lost bytes.
- **The C-quoted branch of `_header_name` drops `b/` inside the quotes.**
  It rebuilt the destination token as `"b/…"` and then tried to strip a
  `b/` prefix the leading quote prevented from ever matching; the fix keeps
  the opening quote and returns `"…"` — the C-quoted path as git wrote it,
  prefix dropped as the docstring says.

## Risks

- [A signature or reviewable detail split by an invalid byte is not
  recoverable] → inherent to lossy decode; mitigated by naming the file, so
  neither the reviewer nor the operator believes it saw the file whole.
- [The stderr note rides `diagnostics_note`, which also carries kept reviewer
  stderr] → both are "what the operator should read"; the note is a line of
  its own, and a later rejection carries it through `_with_diagnostics`
  unchanged.
- [A diff that is not `git diff` output has no `diff --git` boundaries] → the
  helper already degrades such input to one section named "(unknown file)";
  `review` only ever feeds it `git diff`.
