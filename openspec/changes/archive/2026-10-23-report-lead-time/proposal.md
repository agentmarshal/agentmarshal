## Why

ADR-0019 decision 2 decided what `report` shows about time: per task and
in aggregate, opened → the start of the first implementer session → the
first review → approval → completion, and the review rounds with their
durations; a boundary a record cannot supply is shown as **unknown**,
never substituted with `created_at`. CR-176 landed `started_at` and
`ended_at` on session records and CR-188 the `record-session` flags that
write them, so the journal now holds the times the decision reads. What
it does not yet do is print them: `report` still answers only what a
task cost in tokens and reviews, and the lead-time question of proposal
032 — how long a task took and where the time went — still has no
journal answer.

## What Changes

- `report --task <id>` prints, after the task line it prints today, the
  task's lead-time boundaries in order — `opened`, `implementer` (the
  first implementer session's `started_at`), `review`, `approval` (the
  first approving review) and `completed` — and the durations between
  consecutive boundaries. A boundary a record cannot supply prints
  `unknown` where a record exists but lacks the time, `not yet` where
  the event has no record; a session's `created_at` never stands in for
  its `started_at`.
- The same view lists the task's review rounds in order, each with its
  verdict and the time since the previous review — since the first
  implementer start for the first — `unknown` where that start cannot
  be supplied.
- `report` without `--task` prints, after what it prints today, an
  aggregate over completed tasks: the count with a fully known lead
  time, their median and maximum, and the count whose lead time is
  unknown — counted, never averaged in.
- What `report` prints today stays first and unchanged; every value
  taken from a record is escaped on display. No other command changes.

## Capabilities

- modified: `session-activity`

## Impact

`report.py` gains the boundary projection over a task's already-loaded
records and the aggregate over the already-listed statuses; `build_report`
and `format_report` keep their signatures and every line they print
today. Durations render in the `--deadline` duration spelling the step
commands already use. The gate's fixtures and every other documented
transcript are untouched; `docs/sidecar.md`'s `report --task` example
gains the lines the command now prints for it. Money per currency is a
later task, as the contract's non-goals state.
