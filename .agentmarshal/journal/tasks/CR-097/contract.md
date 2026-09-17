+++
schema = 2
id = "CR-097"
title = "The reviewer command's contract is documented, its rejected placeholder is named, and it can be exercised without recording"
scope = [
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/cli.py",
  "tests/test_review_launcher.py",
  "tests/test_cli.py",
  "docs/quickstart.md",
  "openspec/changes/document-the-reviewer-contract/",
  "openspec/changes/archive/",
  "openspec/specs/reviewer-adapter/",
]
acceptance = [
  "every scenario in openspec/changes/document-the-reviewer-contract/specs/reviewer-adapter/spec.md is demonstrated by a test whose docstring names it, except the two documentation scenarios, which are demonstrated by the documentation itself; the implementation follows design.md's decisions or records in design.md why it departed",
  "a dry run writes nothing: no record, no artifact, no directory under the journal, and it needs neither a task nor a commit; a test asserts the journal is unchanged after one",
  "the dry run and the recorded path build their prompt from the same module constant, and the pinned 0.3.0 prompt test passes with its expectations unmodified",
  "the placeholder refusal names the token it rejected, and the message is exercised by a test that does not assert the whole sentence",
  "the quickstart states all four things the spec requires of it — working directory, relative-path resolution, prompt-file placeholder, and that bounding what the command may read belongs to the adapter — and tasks.md's checkboxes are ticked for the work that landed",
]
decisions = ["ADR-0001", "ADR-0005"]
documents = ["openspec/changes/document-the-reviewer-contract/", "openspec/specs/reviewer-adapter/"]
+++

# CR-097: the reviewer command's contract

## Context

An adopter lost three review launches to properties of the reviewer command that
no documentation states, and read the launcher's source to learn them. The
digest of their report is proposal 015 in this repository.

The same undocumented fact has a second half this project found on itself while
reviewing its own work: the snapshot sets where the command starts, not what the
process may read. Both halves belong in the same paragraph, because an operator
who learns the first without the second will assume an isolation the tool does
not provide.

## Objective

An operator can configure a reviewer command from the documentation, learn what
the command may and may not assume, be told which token was rejected when one
is, and exercise the command before the first real review.

## Acceptance Criteria

As in the header.

## Threat model and boundaries

The reviewer command is operator-configured and trusted to produce the verdict
that gates a merge. What the tool can promise about it is where it starts and
what it is handed; what it may read is the harness's to bound
([ADR-0001](../../../docs/adr/ADR-0001-governance-plane.md)). Saying so is the
point of this task: an unstated boundary reads as a guarantee.

A dry run must not be mistaken for evidence. It records nothing and says so.

## Non-Goals

- Confining the reviewer process: that is the adapter's, and this task documents
  the responsibility rather than taking it.
- Shipping a confined adapter as a template; that is its own task.
- Any change to what a recorded review does or to the gate.
- `doctor` checks and the provider template: proposals 014 and 017 are the next
  task, not this one.
