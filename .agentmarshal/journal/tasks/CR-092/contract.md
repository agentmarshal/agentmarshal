+++
schema = 2
id = "CR-092"
title = "Review evidence, hardened: one copy of the prose, no foreseeable orphan, artifacts under the collision rule"
scope = [
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/submit_review.py",
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/cli.py",
  "tests/test_review_launcher.py",
  "tests/test_journal.py",
  "tests/test_gate.py",
  "tests/test_findings.py",
  "docs/quickstart.md",
  "openspec/changes/retire-review-temp-copy/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "every scenario in openspec/changes/retire-review-temp-copy/specs/review-evidence/spec.md is demonstrated by a test whose docstring names it; the tests that pinned a temp copy on an accepted verdict are replaced by the scenario that supersedes them, and the rejected-verdict test passes unmodified; the implementation follows design.md's decisions or records in design.md why it departed",
  "the refusals a record writer can apply before writing — shape, finding binding, task, recorder identity — are stated in one function in records.py that write_record and submit_review both call; the reviewed-finding message exists in one place",
  "the gate's base-tree collision check covers artifact paths with the line it prints for records; the byte-for-byte 0.3.0 transcript test and the sidecar transcript tests pass unmodified",
  "the change is archived in the same candidate: the baseline openspec/specs/review-evidence/spec.md carries the modified requirements, openspec/changes/archive/ holds the change, and openspec validate --all passes",
  "tasks.md's checkboxes are ticked for the work that landed, and the quickstart's review step no longer describes a temporary file on the accepted path",
]
decisions = ["ADR-0005", "ADR-0008", "ADR-0009"]
documents = ["openspec/changes/retire-review-temp-copy/", "openspec/specs/review-evidence/"]
+++

# CR-092: review evidence, hardened

## Context

The second product task run with an OpenSpec delta spec under the research
protocol, and the first that modifies an existing capability's requirements:
`review-evidence` from CR-091. The reviews of CR-091 named the edges this
task closes; proposal.md — Why lists them. The spec, design and task list
reach the implementer through `brief` as named documents; this contract bounds
what may change and what counts as done.

## Objective

One copy of the reviewer's prose, in the journal; a record refused for a
foreseeable reason leaves no artifact; artifacts and records under the same
collision rule; the baseline spec true to what `report` shows.

## Acceptance Criteria

As in the header. The spec's scenarios are the behaviour; design.md's
decisions are the shape; tasks.md is the checklist the implementer ticks.

## Threat model and boundaries

Prose outside the journal escapes the placement that decides publication
(ADR-0008); this task removes the copy on the path where a pinned copy
exists and leaves it where none does. An orphan left by a filesystem failure
is named, not deleted: deleting under an append-only directory is the wrong
reflex.

## Non-Goals

- A capture-policy switch for prose; pinning the implementer brief.
- Any change to the rejected-verdict path.
- Removing orphans: a failure after the artifact is written is reported with
  the artifact's path, and that is the whole of it.
- The operator's `am-land` driver, which lives outside this repository.
