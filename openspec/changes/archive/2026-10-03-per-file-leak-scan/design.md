## Context

`git diff` output is a byte stream: paths may be arbitrary non-NUL bytes and,
with `--text`, file contents are emitted raw. Both the gate (`_run_git` in
`gate.py`) and the `leak-scan` command (`_leak_scan_git` in `cli.py`) decode
the whole stream strictly as UTF-8, so a single file's undecodable bytes —
anywhere in the diff — discard the scan for every file. Proposal 026's fourth
finding and proposal 037 are that defect observed by two adopters.

The scanner itself, `scan_diff_for_leaks` in `capture.py`, already attributes
hits per file from a decoded unified diff and is pure: it parses the text it
is given and runs nothing. The decode failure happens before it ever runs.

## Goals

- One file that does not decode costs its own readability, not every file's
  scan.
- A file that could not be decoded is named, never passed over in silence.
- One helper fetches and decodes the diff for both callers, so the gate and
  the command cannot degrade differently.
- No matched text, no marker value, and no secret-carrying path is printed —
  the existing guarantees hold on the lossy path too.

## Non-Goals

- `review`'s diff handling, which shares the root cause — a separate task
  that can reuse the byte-capturing helper added here.
- A diff-size limit (deferred).
- Changing the built-in signatures or the marker configuration.
- Decoding non-UTF-8 *paths* earlier in the gate: `diff --name-status` still
  refuses them before the scan runs, unchanged by this task.

## Decisions

- **The diff is fetched as bytes and split on `diff --git` boundaries.** A
  unified diff's file sections always start with `diff --git `, and hunk body
  lines are always prefixed (`+`, `-`, space, `\`), so no content line can
  begin a section falsely. Each section is decoded strictly on its own; only
  the sections that fail are handled specially, so a clean diff takes exactly
  the path it took before.
- **An undecodable file's bytes are still searched.** The section's content
  lines are decoded with `errors="replace"`: every valid UTF-8 span — all
  ASCII — survives unchanged, and the U+FFFD replacement character is a
  non-word character, so a signature running right up against an undecodable
  byte still has its word boundary and still matches. (`backslashreplace`
  was tried first and rejected for content: its `\xNN` escapes end in hex
  digits, which glue onto an adjacent token and hide it.) Searching anyway is
  the scan's whole purpose: a secret must not slip through unseen, and
  refusing to look at the file would reproduce the blind spot this change
  exists to remove, one file narrower. What is lost is real but small — a
  signature split by an invalid byte, or a secret held in a non-UTF-8
  encoding — which is exactly why the file is still *named* as not fully
  readable rather than treated as clean.
- **The scanner splits on "\n" only.** git's patch output uses "\n" as the
  sole line separator, so `scan_diff_for_leaks` splits the decoded text on
  it — not `str.splitlines()`, which also breaks on `\x0b`, `\x0c`,
  `\x1c`–`\x1e`, `\x85`, U+2028/29. Those bytes are valid UTF-8 and survive
  the lossy decode inside a `+` line; a split there produces a prefix-less
  fragment that drains both hunk counters as a context line, ends the body
  early, and leaves every later added byte unscanned while the output claims
  they were searched. Neutralising the characters in the lossy decode was
  the alternative and was rejected: it rewrites content before matching —
  one more lossy transformation, where keeping git's framing verbatim loses
  nothing.
- **The same decode names the file.** The section's header lines
  (`diff --git`, `---`, `+++` — which always precede the hunks) are decoded
  with `backslashreplace` before the text reaches the scanner, so an
  undecodable path lands in the scan text in escaped printable form; a hit
  against the file and the not-decoded note name it the same way. Escaping —
  not `replace` — is what makes "named" rather than "mangled" true for a path
  whose bytes are not UTF-8.
- **A file is named only when it lost bytes the scan reads.** Naming covers
  undecodable added lines and undecodable pre-hunk lines (which carry the
  path). A section whose undecodable bytes sit only in removed or context
  lines — a deleted binary — gave the scan nothing to read, so it is not
  named: warning about it would report a file the scan never needed, on
  every diff that deletes an image.
- **Undecodable names are rendered like hit paths.** A name can itself be
  the secret — a key-named file that failed decode, or an asset under a
  marker-named directory — so both callers render the list through one
  helper, `render_undecodable_files` in `capture.py`, a sibling of
  `render_leak_hits`: it passes each name through `safe_path` and owns the
  bounded caller's "and N more not shown" phrasing, so the gate's transcript
  and the command's stderr cannot drift apart. `decode_diff_per_file` stays
  marker-free; masking is the caller's job at the one shared render site.
- **A file that only fails decode is not a hit.** Undecodable files are
  collected as a separate list beside the scan's hits, not folded into
  `LeakHit`s: they are places the scan could not fully read, not places a
  signature matched. That keeps both callers' reporting honest — the gate
  warns about them separately from the "possible leak" line, and the command
  prints them as a caveat, not as results.
- **The command's exit status reports hits only.** When the only thing to
  report is files that did not decode, `leak-scan` names them and exits 0.
  The command exists so any CI can run it on a plain checkout, and an
  ordinary binary file — an image, a vendored wheel — in a diff must not fail
  every such run; the scan is best-effort by design (ADR-0005), the file's
  bytes were still searched, and the file is named, so nothing is silent. A
  hit found inside an undecodable file is a hit like any other and fails the
  run as before.
- **One helper runs the pinned diff for both callers.** `leak_scan_diff` in
  `gate.py` captures `git diff --text --no-textconv --no-ext-diff` with the
  pinned prefixes as bytes and hands it to `decode_diff_per_file` in
  `capture.py`; the gate and the command both call it. The flag rationale —
  `--text` so "binary" files still emit content, no diff drivers rewriting
  what the scanner sees, pinned prefixes so the parser's `b/` strip cannot be
  configured away — moves onto the helper with the call. `decode_diff_per_file`
  stays pure like the scanner it feeds: it parses bytes and runs nothing,
  which is also what the later `review` task reuses.
- **The gate's scan stays advisory.** Undecodable files are a `WARN` line in
  the transcript and are bounded like the hit list, because the transcript is
  a document people read; the command names all of them on stderr, beside the
  best-effort caveat, because an undecodable file is a caveat about the scan,
  not a place to look.

## Risks

- [A signature hidden across an undecodable byte boundary goes unreported] →
  inherent to lossy decode; mitigated by still naming the file, so the reader
  knows which files were only partially read.
- [A non-git diff fed to `decode_diff_per_file` has no `diff --git`
  boundaries] → the whole input is one section; if it fails decode it is
  escaped wholesale and reported as "(unknown file)" — a degraded answer, not
  a silent one. Both real callers only ever pass `git diff` output.
- [The `diff --git` fallback name for a section with no `+++` header misreads
  an exotic header] → that case is a deletion or mode change (no added
  content to scan anyway); worst case is a wrong name in a warning.
