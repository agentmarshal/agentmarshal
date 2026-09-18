+++
schema = 1
id = "CR-110"
title = "Release notes cover prose publication, doctor output and the 0.4.0 status"
scope = ["README.md", "UPGRADING.md"]
acceptance = [
  "UPGRADING.md's 0.3.0 -> 0.4.0 section says that the reviewer's output recorded by agentmarshal review is now committed with the journal — in 0.3.0 it was kept only in a temporary file, and only when the verdict named a finding — so in an embedded journal of a public repository it becomes public, and says what an operator can do about that before the first review",
  "UPGRADING.md's 0.3.0 -> 0.4.0 section names the change in doctor's and init's output: doctor prints TODO lines for unmet preconditions and its summary line counts them instead of reading 'all N checks passed', an unmet precondition does not change doctor's exit status, and init prints the list of preconditions",
  "README.md's Status section says what is new in 0.4.0, citing no task it does not describe, and keeps the 0.3.0 sidecar sentence as history",
  "every statement added is checked against the code of this tree or of the v0.3.0 tag; the full CI sequence passes",
]
+++

# CR-110: Release notes cover prose publication, doctor output and the 0.4.0 status

## Context

CR-109 prepared 0.4.0 and was approved, leaving three advisory findings on
its last round. Each is a gap in what an existing installation is told:

- 0.4.0 commits the reviewer's output as a journal artifact. In 0.3.0 it
  lived in a temporary file, and only for a verdict that named a finding.
  An embedded journal in a public repository therefore publishes text that
  0.3.0 never published — the upgrade guide tells the operator how to stage
  it, but not that staging it publishes it.
- `doctor`'s output changed (CR-098): `TODO` lines and a summary that counts
  preconditions. A script matching the old summary line breaks. The upgrade
  guide names the leak-scan output change and not this one.
- README's Status section, which becomes the PyPI project page, names only
  what was new in 0.3.0.

The tag has not been pushed, so the fix can ship in the release it describes.

## Objective

A 0.3.0 operator reading the upgrade guide learns every output change and
the one publication change before they meet them, and the README's status
describes the release it ships in.

## Acceptance Criteria

As in the header.

## Non-Goals

- Publishing. Pushing the version tag is an outward action the operator
  authorises after this task lands.
- Any change in behaviour, in CHANGELOG.md, or in the documentation under
  docs/.
- A capture policy or redaction for reviewer output: the guide states the
  consequence and the operator's options, it does not add a mechanism.
