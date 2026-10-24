+++
schema = 2
id = "CR-235"
title = "The gate refuses a candidate that adds to another task a record that task's lifecycle does not admit, as it does for the task it judges"
scope = [
  "src/agentmarshal/journal/gate.py",
  "tests/",
  "openspec/changes/gate-other-task-lifecycle/",
  "openspec/changes/archive/",
  "openspec/specs/record-lifecycle/",
]
acceptance = [
  "for every task other than the judged one to which the candidate adds records, the gate projects that task's merged records (target plus candidate) with the same lifecycle projection it applies to the judged task and the same closed-at-base admission rule, and refuses with one FAIL line naming that task and the projection's reason when the projection refuses; release-audit finding AUD-gate-journal-1: a candidate for open CR-001 that adds a reopening to CR-002, abandoned at base, is refused",
  "the change gate-other-task-lifecycle carries a delta on the capability record-lifecycle (ADDED requirement, or MODIFIED with the full current text, heading byte for byte and every scenario) with a scenario for a reopening added to another task abandoned at base, demonstrated by a test whose docstring names it; archived with the archive command (OpenSpec 1.15.0)",
  "a candidate that adds valid records to other tasks, or none, gets exactly the transcript it gets today, which the existing gate tests and transcript fixtures demonstrate unchanged; the suite and the full CI sequence pass",
]
documents = ["openspec/specs/record-lifecycle/"]
decisions = ["ADR-0004", "ADR-0022"]
+++

# Gate: other tasks' lifecycle

## Context

Release audit 0.6.0, area gate-journal, finding AUD-gate-journal-1
(confirmed by reproduction): the gate projects only the named task; for
other tasks the candidate touches it checks only for a duplicate
opening, then prints that lifecycle records are consistent. A record the
projection refuses on another task passes the gate and leaves the journal
failing `validate` after the merge. docs/threat-model.md promises that an
abandoned task cannot be reopened through the gate; record-lifecycle
specifies the refusal.

## Objective

The gate applies the lifecycle projection to every task a candidate
changes.

## Acceptance Criteria

As in the header.

## Non-Goals

- The CR-210 warning about another task's opened or amendment records
  (unchanged).
- Any other gate rule.
