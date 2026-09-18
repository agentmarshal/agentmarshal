## Context

`scan_for_leaks` returns a sorted list of category names and nothing else; its
docstring states that it never echoes the matched secret. `scan_diff_for_leaks`
parses a unified diff's hunk headers and collects the added lines, so it already
walks the file headers it would need to name a file. The outbox README is a
string written by `project.py` at `init`.

## Decisions

- **The hit becomes a record, not a category string.** Each hit carries the file
  and an identification: the signature's name, or the private marker's position
  in the configured list. Both callers — the standalone command and the gate's
  added-content warning — render the same record, so the two cannot drift.
- **A private marker is named by position because its value is the secret.**
  Proposal 020 asks for the matched marker to be named. Taken literally that
  would print an internal hostname into a CI log, which is what the scan exists
  to prevent, and what CR-097 removed from the reviewer-command refusal. The
  position is enough to look it up in a config the operator already has.
- **Self-match is decided by where the marker occurs, not by what it is.** The
  scan drops a private-marker hit whose only occurrence is in the project
  configuration that declares the markers. An occurrence anywhere else is
  reported, including in the same content.
- **Departure from the contract's "sole occurrence" bound, and why.** The
  contract's threat model bounds the narrowing to an occurrence in the
  declaring configuration "and only when it is the sole occurrence", which
  reads as: beside a real hit elsewhere, the declaration's own occurrence is
  reported too. It is not. A review round found the defect in that shape —
  printing the declaration's path beside the real one sends the operator to
  where the marker is *defined*, which is never where it leaked, and it prints
  that path on every change to the marker list. The rule the code implements
  is therefore: occurrences inside the declaring configuration are never
  reported, every occurrence outside it always is. The departure only removes
  a line about the file the operator is already editing; the leak itself is
  still reported, naming its own file, which is what the acceptance criterion
  asks for. It follows that *how many times* a marker occurs inside that one
  file does not matter either — the rule counts locations, not occurrences —
  and a marker's value living in the file that declares it is deliberate.
- **A masked path keeps everything that is not the secret.** Only the marker's
  or the signature's own span is replaced by its description. Describing the
  whole path collapsed two leaking files under one marker-named directory into
  a single hit, because the hits are a set and both rendered identically: the
  scan lost the "where" it was built to add.
- **The diff is read with the prefix fixed and the quoting left alone.** Both
  callers pass `--src-prefix=a/ --dst-prefix=b/`, which wins over all four
  config knobs a repository can set (`diff.noprefix`, `diff.mnemonicPrefix`,
  `diff.srcPrefix`, `diff.dstPrefix`) — `-c diff.noprefix=false` alone does
  not, as `git 2.47` shows with `diff.dstPrefix` still in force.
  `core.quotePath` is deliberately *not* pinned off: unquoted output sends raw
  non-UTF-8 path bytes into a strict decode, which turns the whole advisory
  scan into a skip. A C-quoted non-ASCII path in a warning is noise; an
  unscanned diff is a hole.
- **Kept diagnostics are not cleaned up, like every other kept output.** A
  zero-exit run whose reviewer wrote to stderr leaves one temp file, and
  nothing deletes it — the same policy `_preserve_output` has had since
  CR-097. It is now on the success path, so the files accumulate wherever many
  reviews run. A retention rule for everything this tool leaves in the
  system's temporary directory is deliberately deferred because it must cover
  all of that output, not just this success-path file.
- **The rendered line is bounded.** A marker in two hundred files was one
  category token before this change and is two hundred records after it. The
  renderer shows the first twenty and counts the rest, because the merge
  transcript is a document people read and an advisory warning must not push
  the refusal that matters off the screen.
- **The reviewer's error stream is kept, not printed.** It can be long, and the
  command's own output is read by callers that parse it. It goes beside the
  rejected-verdict copies, outside any journal, and the path is named — the
  shape CR-097 settled for the dry run.
- **Keeping it is best effort, so the failure is a sentence, not a refusal.**
  The launcher carries a note rather than a path: either where the bytes were
  kept or why they could not be. A verdict the reviewer produced and the
  journal can hold is never discarded because a temporary file could not be
  written.
- **A path can be the secret in two ways, and both are described.** A path may
  contain a configured marker, and a file may be named after the key a
  built-in signature matches. Both are replaced by a description that names the
  marker's position or the signature — never the characters. Naming a
  signature discloses nothing; printing what it matched would.
- **One spelling of the project file.** The path whose occurrences the
  self-match rule ignores is a single constant in `project.py`. The renderer
  was unified so the two call sites cannot drift in what they print; the
  suppression key is unified for the same reason, so they cannot drift in what
  they drop.
- **Two output shapes, and the capability says so.** The added-content scan
  returns hit records that name a file, because it was given a diff of many.
  The artefact refusal keeps its category list: it was handed one artefact the
  caller already names, and widening it would change a refusal message every
  capture path depends on.
- **The outbox README gains a sentence and a pathspec.** Proposal 023 lists
  three fixes and asks for the cheapest first; the command it also proposes is a
  release later. The sentence is what would have prevented all eight of the
  reported cases.

- **The outbox sentence ships without a requirement of its own.** It is text
  this tool writes at `init`, not behaviour a scenario can name, so it lives in
  the task list and in this note rather than in a capability. The command
  proposal 023 also asks for is a release later, and that one will carry
  requirements.

## Risks

- [A hit that names a file makes an operator trust the scan] → the existing
  sentence stays: an empty result is not proof of safety, and this change adds
  detail to hits rather than certainty to their absence.
- [Naming a marker by position couples output to config order] → the operator
  reads the position against the same file the scan read; nothing else consumes
  it.
