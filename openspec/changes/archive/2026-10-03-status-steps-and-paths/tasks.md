## 1. The open/overdue computation

- [x] 1.1 `steps.py` gains `open_steps(task_id, records, events, *,
  now=None) -> list[OpenStep]` — a step is open when the task's
  `step-started` event is in the log and neither its `step-ended` event
  nor a journal record of the matching kind for the same task written
  after the step started closes it (implementation session for
  `implementation`, review record for `review`, a session of the
  activity for `coordination`, `other` or an unknown one); `overdue_by`
  is `None` inside the deadline and the UTC span past it once `now` has
  crossed it — verify: a unit test per closing case, per non-closing
  case and per overdue boundary, each naming its scenario.
- [x] 1.2 `steps.py` gains the overdue-span formatter spelling the span
  in `--deadline`'s duration units — verify: the format test.

## 2. The views

- [x] 2.1 `status_view.py` prints the paths line — journal, process log
  and local state, each escaped, `local_state` failure degrading to
  `unavailable (<reason>)` — and the overdue-step lines, each saying it
  comes from this machine's process log — verify: the unit tests of the
  line shapes, the escape included.
- [x] 2.2 `cli.py`'s `_run_status` resolves the local state, prints the
  paths line once ahead of the task output, reads the events, prints the
  detail's overdue lines and marks list tasks that have an overdue step
  — verify: the command-level tests, sidecar included.
- [x] 2.3 The two byte-exact `status` pins change only by the paths line
  — verify: `test_status_view.py` and `test_display.py` diffs.

## 3. The change itself

- [x] 3.1 `openspec/changes/status-steps-and-paths/` carries proposal,
  design and the process-log delta — verify: `openspec validate` (or
  `status`) reads it clean and the archive lands it under
  `openspec/changes/archive/` with `openspec/specs/process-log/` updated
  by the archive command.
