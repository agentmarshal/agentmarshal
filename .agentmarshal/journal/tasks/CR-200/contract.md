+++
schema = 2
id = "CR-200"
title = "status says none on the ran side of the declared assignment when nothing has run, instead of printing nothing"
scope = [
  "src/agentmarshal/journal/status_view.py",
  "tests/",
  "openspec/changes/status-assignment-none-ran/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change status-assignment-none-ran has a proposal, a design.md and a delta spec on the capability contract-governance (MODIFIED for the requirement CR-191 added); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "in the declared-assignment section of `status <task>`, when the contract declares implementers and no implementer session has been recorded, the ran side says so with one line reading as the scope section's `(none)` does; the same for reviewers and reviews",
  "everything else `status` prints is unchanged — the existing tests of the assignment section and the byte-for-byte pin of a task without the schema-3 fields pass unchanged except for the tests that pinned the silent case, which are updated to the new line",
  "no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
decisions = ["ADR-0018"]
+++

# status says none when nothing ran

## Context

CR-191's review left an advisory finding, deferred: in the declared
assignment `status` prints the declaration and, when no implementer session
or review has been recorded, nothing on the side of what ran — while the
section's own rule says an absence is stated rather than omitted, and the
scope section prints `(none)` in the same situation.

## Objective

The assignment section says plainly that nothing has run yet.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any other change to the assignment section or to `status`.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
