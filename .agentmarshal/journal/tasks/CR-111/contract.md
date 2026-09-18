+++
schema = 2
id = "CR-111"
title = "Review prose follows the capture policy, and is not published by default"
scope = [
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/capture.py",
  "src/agentmarshal/cli.py",
  "tests/",
  ".agentmarshal/project.json",
  "README.md",
  "UPGRADING.md",
  "CHANGELOG.md",
  "docs/",
  "openspec/changes/review-prose-capture-level/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "every scenario in the change's delta spec is demonstrated by a test whose docstring names it; the implementation follows design.md's decisions or records in design.md why it departed",
  "the level both review paths apply to the reviewer's prose is the capture policy's level for the reviews class, read through the existing parser in capture.py from the project file of the journal being written; no second setting for the same decision is introduced",
  "with no capture section a review writes nothing under the task's artifacts directory and its record carries no artifacts; with the reviews level at commit, both paths behave exactly as they did before this change, including the line agentmarshal review prints on stderr",
  "submit-review --prose is refused before anything is written when the reviews level is not commit, and the refusal names the level and the setting that permits it",
  "this repository's project file sets the reviews level to commit, so its own reviews keep publishing their prose",
  "every document that states what happens to a review's prose — README.md, UPGRADING.md, CHANGELOG.md's 0.4.0 section, docs/quickstart.md, docs/overview.md and ADR-0005's status note — states the default and the setting, and no document says that no setting turns it off",
]
decisions = ["ADR-0005"]
documents = ["openspec/specs/review-evidence/"]
+++

# CR-111: review prose follows the capture policy, and is not published by default

## Context

0.4.0, as prepared, commits the reviewer's output into the journal for every
review `agentmarshal review` records (CR-091). In an embedded journal of a
public repository that publishes it, and the reviewer process can read beyond
its snapshot, so the text can carry more than the diff. The operator decided
that 0.4.0 must not ship this without a way to turn it off, and that the
default must be not to publish.

ADR-0005 Decision 2 already designs the setting: a capture policy with a
`reviews` class whose level is `off`, `hash` (a private store) or `commit`,
with the default preset `attested` putting reviews at `hash`. `capture.py`
parses that policy from the project file; nothing reads the result. The
shipped behaviour is `commit` whatever the policy says. The private store is
not built.

## Objective

The capture policy's `reviews` level decides what happens to a review's prose
on both review paths, so the default keeps it out of the journal and `commit`
is an explicit choice.

## Acceptance Criteria

As in the header. The scenarios are the behaviour; design.md holds the
decisions, including what `hash` means while no private store exists.

## Non-Goals

- The private store, and a hash-pinned reference into it.
- The economics and sessions classes of the policy: `record-session` keeps its
  behaviour whatever their level says, and the documents say so.
- Rewriting or removing prose already committed to any journal.
- Changing what happens to a rejected verdict's raw output or to reviewer
  diagnostics: both stay local temporary files at every level.
- A doctor check or init output for the capture policy.
