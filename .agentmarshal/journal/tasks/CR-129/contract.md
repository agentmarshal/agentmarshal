+++
schema = 2
id = "CR-129"
title = "review reaches the reviewer with a diff that is not wholly UTF-8, and names what it could not show"
scope = [
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/capture.py",
  "tests/",
  "docs/sidecar.md",
  "openspec/changes/review-diff-per-file/",
  "openspec/changes/archive/",
  "openspec/specs/reviewer-adapter/",
]
acceptance = [
  "every scenario in the change's delta spec is demonstrated by a test whose docstring names it, and the implementation follows design.md's decisions or records in design.md why it departed; the change is archived with the archive command into openspec/specs/reviewer-adapter/",
  "a commit adding a text file and a file of bytes that are not UTF-8 no longer ends `review` in a traceback: the reviewer is launched, the diff reaches it per file through the helper the leak scan already uses, and the file that does not decode is named both in what the reviewer is given and in the command's own output — how its content is shown or replaced is decided in design.md, and nothing about it is dropped in silence; the reproduction is a test",
  "no other git output `review` reads (merge-base, ls-tree, rev-parse, error text) ends in a traceback on bytes that are not UTF-8, and a path whose bytes are not UTF-8 is named in an escaped printable form",
  "the points carried from the leak-scan task are closed: the quoted branch of the diff-header name helper drops the destination prefix as its docstring says, with a test; docs/sidecar.md lists every line the gate's scan can append, including the one for files that did not decode; the two test docstrings that carry a literal control character state it as an escape",
  "the full CI sequence passes",
]
documents = ["openspec/specs/reviewer-adapter/"]
+++

# CR-129: review on a diff that is not wholly UTF-8

## Context

Proposal 037: `agentmarshal review` fails with a traceback on a diff that is
not UTF-8 — its git helper decodes the merge-base diff strictly before the
reviewer is launched. The leak-scan half of the same root cause landed in
CR-127, which built a helper that reads git's diff as bytes and decodes it
per file, naming what does not decode. This task brings `review` onto it.
The published disposition: a diff that is not wholly text must still reach
the reviewer, or be refused — per file, naming it.

CR-127 landed with three small review advisories carried here because they
touch the same helper and its documentation.

## Objective

`review` never fails on a diff because of encoding, and the reviewer knows
which files it could not be shown.

## Acceptance Criteria

As in the header.

## Non-Goals

- A diff-size limit (deferred).
- Changing the verdict protocol or what the reviewer is asked.
