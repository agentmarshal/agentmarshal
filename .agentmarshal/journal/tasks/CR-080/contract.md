+++
schema = 1
id = "CR-080"
title = "A task's cost is known when it ends: record-session must admit post-terminal sessions"
scope = ["src/agentmarshal/journal/session.py", "tests/test_journal.py", "docs/quickstart.md", ".agentmarshal/journal/.gitignore"]
acceptance = [
  "`record-session` records a session against a task that is done or abandoned, as the record model and the gate already allow",
  "it still refuses a task that does not exist, and still refuses an invalid record",
  "the quickstart records the session after completion, where a task's cost is actually known, and says why",
  "the journal ignore rule is anchored so it stops matching `stats/runs/` by accident, and each ignored path carries the reason it is ignored",
]
+++

# CR-080: A task's cost is known when it ends

## Context

`record_session` refuses unless a task is `open`. Everything else in the design
says the opposite:

- ADR-0005 Decision 3 states that a session record projects to no state and
  **may accrue after a terminal record**;
- `project_status` implements that — a session is the one record type permitted
  after a terminal one, alongside a reopening;
- the gate has a whole **measurements-only lane** for it: a task closed at base
  still admits a strictly additive candidate that adds session records.

So the gate maintains a lane that the command cannot reach. Found by asking why
this project's own journal has no live session records at all: **not one** of
its 113 session records was captured live — every one arrived in the CR-031
backfill — and 48 consecutive tasks since have none.

The reason is this guard. The moment a task's cost is known is the moment it
finishes, and at that moment the task is `done`, so the command refuses. Adopter
proposal 008 reported the same shape from outside — "usage has to be
reconstructed afterwards from provider logs" — and *afterwards* is precisely
what the tool declines to accept.

Second, unrelated but found in the same investigation: the journal's ignore rule
is the bare pattern `runs/`, which is unanchored and therefore matches at any
depth. It was written for `journal/runs/` (raw transcripts, private by ADR-0005)
and silently swept up `journal/stats/runs/` as well. Whatever we decide about
that store, it should be a decision and not a pattern collision.

## Objective

Let a session be recorded when its cost is known, and make the ignore rule say
what it means.

## Acceptance Criteria

- `record-session` records a session against a task in any state the record
  model permits, including `done` and `abandoned`.
- It still refuses an unknown task, and record validation is unchanged.
- The quickstart records the session **after** completion — where the cost is
  actually known — and says why that is the honest moment.
- The journal ignore rule is anchored so `runs/` no longer matches
  `stats/runs/`, and every ignored path carries a comment saying what it is and
  why it is ignored.

## Threat model and boundaries

No adversary. This removes a guard that contradicts the model it guards, in a
command writing to the operator's own journal.

The property that must not weaken: **a session record still changes no state**.
The projection treats it as measurement, the gate's measurements-only lane
requires the candidate to be strictly additive and confined to the task's own
records, and neither is touched here. Removing the open-only guard must not make
a session able to revive, mutate or complete anything — that is what the
projection and the lane enforce, and this task must leave both alone.

Not defects in this task: whether the ignored stores *should* be published,
which is a separate decision; the `imported-from-host` provenance value being
v1-flavoured for what is simply a backfill, which is a naming debt the published
format cannot cheaply change.

## Non-Goals

- **Publishing any ignored store.** This task makes the ignore rule deliberate
  and commented; it changes no file's published status.
- Automatic session capture, or any hook. Proposal 009 was re-read on
  2026-09-01 and remains deferred; the call belongs in the operator's wrapper.
- Backfilling this project's own missing records — operational work that
  follows, not a change to the tool.
- Changing `record-session`'s flags, the record shape, or the report.
