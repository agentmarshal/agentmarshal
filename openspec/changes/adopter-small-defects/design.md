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
- **The reviewer's error stream is kept, not printed.** It can be long, and the
  command's own output is read by callers that parse it. It goes beside the
  rejected-verdict copies, outside any journal, and the path is named — the
  shape CR-097 settled for the dry run.
- **The outbox README gains a sentence and a pathspec.** Proposal 023 lists
  three fixes and asks for the cheapest first; the command it also proposes is a
  release later. The sentence is what would have prevented all eight of the
  reported cases.

## Risks

- [A hit that names a file makes an operator trust the scan] → the existing
  sentence stays: an empty result is not proof of safety, and this change adds
  detail to hits rather than certainty to their absence.
- [Naming a marker by position couples output to config order] → the operator
  reads the position against the same file the scan read; nothing else consumes
  it.
