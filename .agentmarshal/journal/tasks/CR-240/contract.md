+++
schema = 2
id = "CR-240"
title = "The gate refuses an added record at a nested path under any task's records directory, the path read_records would refuse after the merge"
scope = [
  "src/agentmarshal/journal/gate.py",
  "tests/",
]
acceptance = [
  "the gate's added-records check refuses, with one FAIL line naming the path, any added path under `.agentmarshal/journal/tasks/<id>/records/` whose remainder contains a `/` — only `tasks/<id>/records/<file>` is a record path, the shape `read_records` accepts — for the judged task and for any other task alike (comparison audit finding AUD-whole-project-1: a journal-only candidate adding `tasks/CR-002/records/sub/<ULID>-session.json` passes today and leaves CR-002 unreadable after the merge, past repair through the append-only check)",
  "a nested path under the judged task's own records directory gives that FAIL line, not an unlabelled error or traceback",
  "tests with real temporary git repositories (tests/test_gate.py helpers) cover a nested path under another task and under the judged task, in the journal-only and the implementation lane; every existing gate transcript fixture stays byte-identical; the suite and the full CI sequence pass",
]
documents = []
decisions = ["ADR-0004"]
+++

# Gate: nested record paths

## Context

Comparison audit 0.6.0 (Claude Fable, whole project in one pass), finding
AUD-whole-project-1, reproduced: the gate validates an added record by its
file name only, while `read_records` refuses any non-file entry under a
task's `records/`. A candidate adding a record one directory deeper passes
the journal-only lane with "added records are valid"; after the merge the
task cannot be read by status or validate, and the append-only check
refuses moving the file back. docs/threat-model.md names a candidate the
gate admits although its documented checks should refuse it, and a
command that leaves a journal unreadable, as security defects.

## Objective

The gate admits only record paths the journal reader accepts.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any other gate rule; repairing journals that already hold such a path.
