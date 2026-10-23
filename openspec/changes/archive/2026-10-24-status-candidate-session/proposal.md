## Why

Proposal 036: a review can approve a candidate whose implementer run was
interrupted, because nothing linked the commit to the run. Its
disposition accepts the session's `commit` field (landed in CR-160,
written by `record-session --commit` since CR-166) and, with it, the
`status` display of which session produced the candidate head and how
that session ended — the read side of the link. The refusal in `review`
and the gate, with the operator's override, comes with a later record
schema (operator decision of 2026-10-23). When no session names the
commit, behaviour is as today.

## What Changes

- `status <task>` prints, after the lines it prints today, one line for
  the commit the task's latest review judged (`reviewed_commit`): the
  implementer session whose `commit` equals it — the session's id,
  `actor` and `outcome`, and `report_ready` when the record carries it.
- When the session's outcome is not `implemented` the line says the run
  did not end `implemented`; when several implementer sessions name the
  commit the latest is shown and the count of the earlier ones is given.
- A task whose latest review binds a finding (`reviewed_finding`), a
  task holding no review, and a task no implementer session names the
  commit of print exactly what they print today — a candidate produced
  by a runner that wrote no session is shown as before.
- Every value the line takes from a record is escaped on display, as
  every record value in the view is; the line reports and blocks
  nothing.

## Capabilities

- modified: `session-activity`

## Impact

`status_view.py`'s `print_task_detail` gains one derived line, appended
after the summary lines it already prints and escaped through the same
`escape_for_display` dispatch. No record schema, no reader, no command
besides `status` changes; `review` and the gate are untouched — the
refusal this decision pairs the display with is a later task.
