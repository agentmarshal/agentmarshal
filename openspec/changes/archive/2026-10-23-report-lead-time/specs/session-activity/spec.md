## ADDED Requirements

### Requirement: report --task shows the task's lead-time phases
`agentmarshal report --task <id>` SHALL print, after the task line it
prints today, the task's lead-time boundaries in order — `opened` (the
`opened` record's `created_at`), `implementer` (the `started_at` of the
first session record whose `role` is `implementer`), `review` (the
first `review` record's `created_at`), `approval` (the first `review`
whose `verdict` is `approved`, its `created_at`) and `completed` (the
task's last `completed` record's `created_at`) — and the durations
between consecutive boundaries. A boundary the records cannot supply
SHALL print `unknown` where a record exists but lacks the time — a
first implementer session carrying no `started_at` — and `not yet`
where the event has no record; a session's `created_at` SHALL NOT
stand in for its `started_at` (ADR-0019 decision 2). A duration SHALL
print when both its boundaries carry a time, `not yet` when its later
boundary has no record, and `unknown` otherwise.

#### Scenario: every boundary's time prints, with the durations between them
- **WHEN** `report --task` runs for a task whose records supply every
  boundary
- **THEN** the task line prints first, unchanged, then a line naming
  each boundary's time in order and a line of the durations between
  consecutive boundaries

#### Scenario: an implementer session without started_at is an unknown boundary
- **WHEN** the first implementer session carries no `started_at`
- **THEN** the `implementer` boundary prints `unknown`, the spans on
  either side of it print `unknown`, and the session's `created_at`
  appears nowhere as a boundary

#### Scenario: a boundary without a record is not yet
- **WHEN** a task has no implementer session, no review, no approving
  review or no completion
- **THEN** the matching boundary prints `not yet`, and a span whose
  later boundary is the missing one prints `not yet`

### Requirement: report --task lists the task's review rounds
`agentmarshal report --task <id>` SHALL list the task's `review`
records in their stored order, each numbered, with its `verdict` and
the elapsed time since the previous review — since the first
implementer session's `started_at` for the first — the elapsed time
`unknown` where that start is unknown or absent.

#### Scenario: rounds list in order with verdicts and elapsed times
- **WHEN** `report --task` runs for a task with review records
- **THEN** each round prints in order with the review's verdict and the
  time since the previous review — since the first implementer start
  for the first

#### Scenario: a first round after an unknown start is unknown
- **WHEN** the first implementer session carries no `started_at`, or
  the task holds no implementer session
- **THEN** the first round's elapsed time prints `unknown`

### Requirement: report aggregates lead time over completed tasks
`agentmarshal report` without `--task` SHALL print, after what it
prints today, an aggregate over the tasks whose projected state is
`done`: the count whose lead time is fully known — every boundary of
the task's phase chain carrying a time — with the median and the
maximum lead time among them, the lead time being `completed` minus
`opened`, and the count of completed tasks whose lead time is unknown.
A task whose lead time is unknown SHALL be counted, never averaged in;
with no fully known lead time the median and maximum SHALL be absent.

#### Scenario: the aggregate prints after today's output
- **WHEN** `report` runs over completed tasks, some with a fully known
  lead time and some without
- **THEN** after what it prints today it prints the count of fully
  known lead times, their median and maximum, and the count of unknown
  lead times

#### Scenario: an unknown lead time is counted, never averaged in
- **WHEN** `report` runs over a completed task missing a boundary — an
  implementer session without `started_at`, no review or no approval
- **THEN** the task counts toward the unknown count and contributes
  nothing to the median or maximum

#### Scenario: with no fully known lead time the median and maximum are absent
- **WHEN** `report` runs and no completed task has a fully known lead
  time
- **THEN** the aggregate prints no median and no maximum

### Requirement: the new lines leave today's output first and unchanged
Every line `report` and `report --task` print today SHALL print first
and unchanged, the new lines appended after; every value the new lines
take from a record SHALL be escaped where it is displayed, as every
record value in the view is.

#### Scenario: today's output is the new output's prefix
- **WHEN** `report` or `report --task` runs
- **THEN** every line the command printed before this change prints
  first and unchanged, and the new lines follow

#### Scenario: a record value in the new lines is escaped on display
- **WHEN** a value the new lines take from a record carries a
  character that could forge a line
- **THEN** it is escaped on display, as every record value in the view
  is
