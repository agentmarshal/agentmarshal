## Context

`status_view.py`'s `print_task_detail` prints the task's header lines,
the acceptance trail, the scope block, the optional assignment section,
one line per record through the renderer registry, then the agreement
and drift notices. `task.records` already carries everything the new
lines need: the review records with their `verdict` and optional
`reviewed_finding`, and the `completed` record's `advisory_dispositions`
(CR-175). The threshold is read through `changes_required_threshold`
(`settings.py`) — the same reader the gate uses.

ADR-0016 decision 4 pairs `status` with the gate's count line (CR-168);
ADR-0016 decision 1 says `status` and `report` show the deferrals still
open — `report` is a later task; this one is `status` only.

## Goals

- A task with at least one `changes_required` verdict gets one line
  naming the count and the threshold, marked when reached; a task with
  none gets no line.
- A task whose `completed` record carries `advisory_dispositions` gets
  a `Deferrals` section: each `deferred` finding listed with reason and
  follow-up state; `fixed` and `rejected` counted on one line.
- A task with neither prints today's view byte for byte.

## Non-Goals

- `report` showing deferrals and classes across tasks (a later task).
- Review-by dates on deferrals (pending an operator decision).
- Blocking anything — the count is a signal, never a verdict.

## Decisions

- **The count is computed in `status_view.py` with exactly the gate's
  definition.** `gate.py` is not in this task's scope, so the counting
  is replicated rather than shared: the gate's counting block at the
  end of `run_gate` (`gate.py`, lines 1492–1507) counts `record_type` is
  `review`, `verdict` is `changes_required` and `reviewed_finding` is
  absent — every review of the task's candidates, whatever commit it
  names; a review bound to a research finding (ADR-0009) is not a
  candidate's return. `status_view.py` sums over `task.records` with
  those same three conditions.
- **Same threshold, same reader.** `changes_required_threshold(project_root)`
  — the same `settings.py` reader the gate calls. An unreadable or
  malformed setting is named on the line
  (`threshold unreadable: <error>`), as on the gate's line; the view
  does not fail.
- **The line wording mirrors the gate's** minus the level prefix:
  `changes_required verdicts for <task>: N (threshold T)`, and
  `(threshold T reached — stop and revisit the contract)` when
  `count >= threshold`. A parser comparing the two surfaces reads the
  same figures.
- **Dispositions come from every `completed` record that carries the
  field.** A reopened task can complete again with its own
  `advisory_dispositions`; the open deferrals of the task are those
  recorded on its completions, in record order.
- **The follow-up's state comes from `load_task_status`.** An id the
  journal does not hold raises — that is an ordinary answer, not an
  error: the line says `not held by the journal`. A held task shows
  `state: <state>`.
- **The section reads `Deferrals:` then one line per deferred finding**
  — `- <id>: reason=<reason>` plus `follow_up=<task> (<state or
  not held>)` when present — then the counts line `fixed=N rejected=M`,
  always printed so the section is complete even when the counts are
  zero.
- **The new lines trail the view**, after the agreement and drift
  notices: the deferrals section first, then the count line. Header,
  acceptance, scope, assignment and record lines are untouched, and a
  task producing neither addition is byte for byte what it was — the
  pinned detail views and the `status` example in `docs/sidecar.md`
  stay true without an edit.
- **Every line is escaped whole at print** through
  `escape_for_display`, like every rendered line — a reason or a
  finding id carrying a refused character can neither add a line nor
  reorder one (ADR-0015 decision 5).

## Migration

None — display-side only. Journals written before the field existed
carry no `advisory_dispositions` and no new lines.

## Risks

- [The count could drift from the gate's] → the conditions are copied
  verbatim from `gate.py`'s counting block and pinned by tests over
  mixed verdicts and a `reviewed_finding`-bound review; the count and
  threshold the line prints are the same figures the gate prints.
- [A hostile `advisory_dispositions` shape] → entries are checked for
  the dict shape and the disposition vocabulary before listing, and
  every line is escaped; a `reason` that is absent or not a string
  shows `(absent)` like other displayed fields.
- [A follow-up id that fails task-id validation] → `load_task_status`
  raises `TaskStatusError`/`JournalRecordError` (a `ValueError`), which
  the view catches as "not held by the journal".
