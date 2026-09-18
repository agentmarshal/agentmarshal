+++
schema = 2
id = "CR-105"
title = "A reopening lands through the gate"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/status.py",
  "tests/test_gate.py",
  "openspec/changes/gate-lands-a-reopening/",
  "openspec/changes/archive/",
  "openspec/specs/record-lifecycle/",
]
acceptance = [
  "every scenario in the change's delta spec is demonstrated by a test whose docstring names it; the implementation follows design.md's decisions or records in design.md why it departed",
  "a candidate whose only change is a reopening record on a task completed at base passes the gate's base-state check — tested with the reopening in the candidate's diff, not committed into the base",
  "what a closed task admits is read by the gate from status.py; no list of admitted record suffixes remains in gate.py",
  "the byte-for-byte gate transcript tests pass with their expectations unmodified",
]
decisions = ["ADR-0005"]
documents = [
  "openspec/specs/record-lifecycle/",
]
+++

# CR-105: a reopening lands through the gate

## Context

`reopen` shipped in CR-067 and its record is admitted by the projection. The
transaction carrying it cannot merge. Probed on master 2026-09-18 with a task
completed at base and a candidate whose only change is the reopening record:
`FAIL: task CR-001 is already closed at base (candidate state: open)`. The
gate admits a closed task only a strictly additive candidate of session
records; the projection also admits a reopening. The existing test commits the
completion and the reopening together into the base, so it never exercised
the case where the reopening is the diff.

CR-102's reviewers named the gate's second encoding of the admitted set as
drift in waiting. It had already drifted, and the drift is a command whose
transaction is refused.

## Objective

The gate admits after a terminal record what the projection admits, from the
projection's own rule.

## Acceptance Criteria

See the `acceptance` field above; scenarios in the delta spec, decisions in
design.md.

## Non-Goals

- Changing what the projection admits.
- Relaxing the lane's other strictness: additions only, inside the task's own
  subtree.
- The sidecar placement, where the gate already asks the journal's projection.
