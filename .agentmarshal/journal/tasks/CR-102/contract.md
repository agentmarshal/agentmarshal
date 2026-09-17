+++
schema = 2
id = "CR-102"
title = "A writer refuses a record the projection would refuse to read"
scope = [
  "src/agentmarshal/journal/status.py",
  "src/agentmarshal/journal/submit_review.py",
  "src/agentmarshal/journal/acceptance.py",
  "src/agentmarshal/journal/session.py",
  "src/agentmarshal/journal/complete.py",
  "src/agentmarshal/journal/open_task.py",
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/cli.py",
  "tests/test_journal.py",
  "tests/test_findings.py",
  "tests/test_review_launcher.py",
  "openspec/changes/writer-refuses-a-closed-task/",
  "openspec/changes/archive/",
  "openspec/specs/record-lifecycle/",
]
acceptance = [
  "every scenario in openspec/changes/writer-refuses-a-closed-task/specs/ is demonstrated by a test whose docstring names it; the implementation follows design.md's decisions or records in design.md why it departed",
  "for each terminal state, every command that writes a record into a task refuses, writes nothing, and leaves the journal valid — one test per command",
  "the set of record types admitted after a terminal record is read from the projection's own constant, and no second list of it exists in the tree",
  "record-session after completion and reopen after completion both still work, each pinned by a test",
  "a launched review of a closed task starts no reviewer process and writes no prompt file, for both the commit and the finding binding",
]
decisions = ["ADR-0005", "ADR-0004"]
documents = [
  "openspec/changes/writer-refuses-a-closed-task/",
  "openspec/specs/record-lifecycle/",
]
+++

# CR-102: a writer refuses a record the projection would refuse to read

## Context

The projection refuses to read a task whose records carry work after a terminal
record; the writer never refused to write one. Probed on a throwaway journal
2026-09-18: after `abandon`, `submit-review` exits 0 and the record lands, and
from then on `status` reports "task has a lifecycle record after a terminal
record" and `validate` calls the whole journal invalid. One ordinary command,
reachable by a person today, and irreversible in an append-only journal.

It was found while CR-101 argued about refusing a finding review on a closed
task — that task closed the launcher's door; this one closes the writer's.

## Objective

Every command that writes a record into a task asks the projection whether the
task still admits one, and refuses when it does not.

## Acceptance Criteria

See the `acceptance` field above; the scenarios it refers to are in the delta
spec, and the decisions the implementation follows — or departs from with a
recorded reason — are in that change's `design.md`.

## Non-Goals

- Changing what the projection admits: the reader's rule is the rule.
- Repairing journals already corrupted this way; nothing in this release removes
  a record, and a repair path is its own decision.
- A new record type, a new field, or a schema bump.
