## Why

ADR-0019 decision 4 decided that `report` sums a session's `cost` per
currency and converts nothing; ADR-0017 decision 3 that it counts the
candidates the pipeline rejected, next to rounds and cost; ADR-0016
decision 3 that `report --findings` shows the finding classes across
tasks, with counts and examples, and decision 1 that `status` and
`report` show the deferrals still open. The fields these decisions read
landed with CR-174 (`classes`), CR-175/CR-192 (`advisory_dispositions`),
CR-167/CR-183 (`check` records) and CR-176/CR-188 (`cost`), and CR-196
put lead time into `report`. What the journal records, the report still
does not say: a task or a journal answers what the work cost only in
tokens, how often the pipeline refused not at all, and which defects
recur or were left for later nowhere.

## What Changes

- `report --task <id>` prints, after the round lines it prints today,
  the task's cost: one `Cost` line per currency carrying the `reported`
  and `estimated` sums as decimals — two currencies are two sums, never
  converted or blended — and the count of the task's sessions carrying
  no cost. A task with no cost shows none rather than zero.
- `report` prints the same cost sums and no-cost count over every
  task's sessions, after the `Lead` line it prints today.
- `report --task <id>` prints, next to the review rounds, the count of
  distinct commits a `check` record marked `failed` or `error`;
  `report` prints the count in aggregate. The report says once that a
  check record is the observer's declaration of what the pipeline found
  on the commit, not proof of it.
- `report --findings` prints, instead of the economics report, the
  finding classes recorded on reviews across tasks — each with a count
  and up to three example finding ids — and the deferred advisory
  dispositions of the tasks' completed records still open: a deferral
  is open while its `follow_up` names no task or a task the journal
  does not hold as completed, and each prints with task, finding id,
  reason and follow-up. `--task` scopes the view to the one task.
- What `report` and `report --task` print today stays first and
  unchanged; every value the new lines take from a record is escaped on
  display. No other command changes.

## Capabilities

- modified: `session-activity` — the cost and refused-check sums the
  report derives from session and check records.
- modified: `finding-lifecycle` — the `report --findings` view of
  classes and open deferrals.

## Impact

`report.py` gains the cost summation (amounts are strings in the
record, summed as `decimal.Decimal` and printed as decimals, never
floats), the distinct-failing-commit count, the `--findings`
projection and its rendering; `cli.py` gains the `--findings` flag on
the `report` parser. `records.py` does not change. `docs/sidecar.md`'s
`report --task` example shows an older output and is outside this
change's scope — a documentation task catches it up.
