## Context

`build_report` already loads each task's validated records through
`load_task_status` (one task for `--task`, `list_task_statuses`
otherwise), and `format_report` renders the tab-separated lines —
`include_summary=False` marks the `--task` view. The records carry what
ADR-0019 decision 2 reads: the `opened`, `review` and `completed`
records are written as their event happens, so `created_at` is the
event's time; a session's `started_at` is the schema-7 field CR-176
landed and CR-188's flags write, and a session recorded before them
carries no such field. A review carries `verdict` — `approved`,
`changes_required`, `blocked` or `rejected`, the closed vocabulary the
record rule checks.

## Goals

- `report --task` prints, after the task line it prints today, the
  task's lead-time boundaries — `opened`, `implementer`, `review`,
  `approval`, `completed` — the durations between consecutive
  boundaries, and the review rounds in order with their verdicts and
  elapsed times.
- A boundary a record cannot supply prints `unknown` where a record
  exists but lacks the time, `not yet` where the event has no record;
  `created_at` never substitutes for a session's `started_at`
  (ADR-0019 decision 2).
- `report` without `--task` prints, after what it prints today, an
  aggregate over completed tasks: the count with a fully known lead
  time, their median and maximum, and the count whose lead time is
  unknown — counted, never averaged in.
- What `report` prints today stays first and unchanged; every record
  value is escaped on display; no other command changes.

## Non-Goals

- Money per currency, refused checks and finding classes in `report` —
  the contract's own non-goals, later tasks.
- Business-hours or wall-clock adjustments; durations are plain elapsed
  time between recorded instants.
- Session `ended_at`, `resets_at` and `cost` — recorded, nothing reads
  them here.
- Any check that a recorded time is true — what the journal checks is
  shape, not truth (docs/threat-model.md).

## Decisions

- **The boundaries are a projection over the task's records in their
  stored order.** `opened` is the `opened` record's `created_at`;
  `implementer` is the `started_at` of the first session record whose
  `role` is `implementer` — the codebase's own sense of the word
  (`status_view`'s assignment section reads the same field); `review`
  the first `review` record's `created_at`; `approval` the first review
  whose `verdict` is `approved`; `completed` the last `completed`
  record's `created_at` — a reopened task's most recent completion.
  A later implementer session's `started_at` is not the first one's:
  where the first lacks the field the boundary is `unknown` — the
  session's `created_at` is its write time, and substituting it would
  print a wrong number confidently (ADR-0019 decision 2). Where the
  event has no record at all the boundary is `not yet` — an
  un-started implementer run, an un-reviewed task, no approval, no
  completion.
- **A duration prints when both boundaries carry a time.** Where the
  later boundary is `not yet` the span is `not yet` — it is still
  open; where either boundary is otherwise missing the span is
  `unknown` — it is over but cannot be measured. A round's elapsed
  time is measured since the previous review, and since the first
  implementer start for the first round; it is `unknown` whenever that
  start cannot be supplied, because the round is over.
- **Durations render in `format_overdue`'s spelling** — `90m`,
  `1h30m`, `1d3h4m7s` — the `--deadline` duration spelling the step
  commands already print, so the report's figures and the process
  log's overdue lines say a span the same way. A span a clock skew or
  a retroactive `started_at` could make negative keeps its sign
  rather than clamping to `0s` — the wrong number is the failure
  ADR-0019 rules out.
- **The aggregate counts `done` tasks only, and a lead time is fully
  known when every boundary of the task's chain carries a time.** The
  lead time itself is `completed` minus `opened`; "fully known" is
  the stronger claim the criterion makes — the report can account for
  the whole span, not just its ends — so a completed task missing any
  boundary counts toward `unknown`, and the median and maximum run
  over the fully known ones alone. With none fully known the median
  and maximum are absent, the way `artifacts=` and `usage=` are
  absent when there is nothing to say.
- **The new lines append after today's.** `--task`'s `Phases`,
  `Durations` and `Round` lines follow the task line; the `Lead` line
  follows the summary. Today's lines are byte for byte what they were
  — a test pins the prefix — and every value taken from a record (a
  timestamp, a verdict) is escaped where it is interpolated, the same
  rule the task line already follows (ADR-0015 decision 5).
