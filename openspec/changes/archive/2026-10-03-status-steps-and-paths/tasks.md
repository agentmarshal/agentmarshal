## 1. The open/overdue computation

- [x] 1.1 `steps.py` gains `open_steps(task_id, records, events, *,
  now=None) -> list[OpenStep]` — a step is open when the task's
  `step-started` event is in the log and neither its `step-ended` event
  nor a journal record of the matching kind for the same task written
  after the step started closes it (implementation session for
  `implementation`, review record for `review`, a session of the
  activity for `coordination`, `other` or an unknown one, a `completed`
  or `abandoned` record for any step); `overdue_by` is `None` inside the
  deadline and the UTC span past it once `now` has crossed it — verify:
  a unit test per closing case, per non-closing case and per overdue
  boundary, each naming its scenario.
- [x] 1.2 `steps.py` gains the overdue-span formatter spelling the span
  in `--deadline`'s duration units — verify: the format test.
- [x] 1.3 `--deadline` accepts the compound durations the formatter
  prints — one or more `<n><unit>` pairs, a unit at most once, in the
  order `d`, `h`, `m`, `s` (`90m`, `1h30m`, `2h5m`, `1d3h4m7s`) —
  verify: the duration tests.

## 2. The views

- [x] 2.1 `status_view.py` prints the paths — `journal:`, `process log:`
  and `local state:`, one line each on stderr, each escaped,
  `local_state` failure degrading to `unavailable (<reason>)` — and the
  overdue-step lines on stdout, each saying it comes from this machine's
  process log — verify: the unit tests of the line shapes, the escape
  included.
- [x] 2.2 `cli.py`'s `_run_status` resolves the local state, prints the
  paths once on stderr, reads the events once per run and groups them
  by task once (`step_events_by_task`), so the list form's per-task
  lookups each scan only their task's slice — a log that cannot be
  read named on stderr, never a failure — prints the detail's overdue
  lines and marks list tasks that have an overdue step — verify: the
  command-level tests, sidecar and unreadable-log cases included.
- [x] 2.3 The two byte-exact `status` stdout pins keep their pre-change
  output, the paths asserted on stderr — verify: `test_status_view.py`
  and `test_display.py` diffs.

## 3. The change itself

- [x] 3.1 `openspec/changes/status-steps-and-paths/` carries proposal,
  design and the process-log delta — verify: `openspec validate` (or
  `status`) reads it clean and the archive lands it under
  `openspec/changes/archive/` with `openspec/specs/process-log/` updated
  by the archive command.
