## Context

AUD-gate-journal-1 (confirmed by reproduction): `run_gate` loads the
judged task's projection through `load_task_status` and holds its diff
to a closed-at-base admission; for every other task the candidate
appends to, the only check was a duplicate `opened` scan over the union
of the base tree and the candidate's added paths. A record the
projection refuses — the audit's case is a `reopened` on a task
abandoned at base — passed, and the merged journal failed `validate`
from then on.

## Goals

- One rule, everywhere it applies: the same `project_status`
  projection and the same closed-at-base admission for every task the
  candidate adds records to — no second lifecycle table that the judged
  task alone gets.
- One FAIL line per refusing task, naming the task and the
  projection's reason.

## Non-Goals

- The CR-210 warning about another task's `opened` or `amendment`
  records — unchanged.
- Any other gate rule.

## Decisions

### The merged record set is the union of paths, read by filename

`project_status` reads each record's `record_type` and nothing else,
and the filename-record-type rule makes the name authoritative — so
the merged set is the union of the base tree's record paths and the
candidate's added record paths under the task's records directory,
sorted: the record id leads the filename, so path order is stored
order. No record's bytes are read here — the check owes the projection
the record types in order, nothing more.

### The judged task is one of the affected tasks

The projection runs for every task the candidate adds records to, the
judged one included — the same union the duplicate-opening scan
covered, which is what caught a second `opened` on the judged task
when the gate ran on a checkout that was not the candidate. The judged
task's closed-at-base admission still runs where it ran, at the top of
the transcript; the other tasks get the same rule here, computed over
the same base tree and change statuses.

### A record set with no opened record is a refusal like any other

A task directory the candidate creates out of stray records — the
common case is a session riding the wrong transaction — is a record
set the projection refuses ("task records do not contain an opened
record"), and the gate refuses it like any other. The gate-lanes WARN
about `opened`/`amendment` records still fires before this check is
reached where it applies; the test that wrote a session into a task
with no opening now opens the other task at base first.
