## Context

CR-153 built the process log and CR-157 shipped the `step` commands that
write `step-started` and `step-ended` events into it. ADR-0014 decision 9
— as amended 2026-10-03 — says `status` and `doctor` show a step past its
deadline and that a step is closed by the record it already ends with,
`step end` being an optional addition (ADR-0022 section 7). ADR-0014
decision 13 obliges `status` and `doctor` to print the actual paths —
`status` today prints only `Placement: <kind>` on stderr. This change is
the `status` half of both; `doctor` is a separate task.

## Goals

- An operator sees, in `status <task>`, which steps ran past their
  deadline, and sees a task so marked in the `status` list.
- Both forms of `status` name where everything lives: the journal, the
  process log and the local state.
- A task without steps prints exactly what it printed before, apart from
  the paths line.

## Non-Goals

- `doctor` (a separate task).
- Stopping or signalling any process — the watchdog is a supplied
  component the harness runs.
- Steps on other machines — the log is local (ADR-0014 decision 8).
- Showing open-but-not-overdue steps: the decision shows the late ones.

## Decisions

- **The computation lives next to the step commands.** `steps.py` —
  where the producers and the event fields already live — gains
  `open_steps(task_id, records, events, *, now=None) -> list[OpenStep]`,
  and the views call it; nothing journal-side learns the event shapes.
  `records` is the task's journal records and `events` is the process
  log's events, both taken as data, so the function needs no filesystem
  and `now` is injectable for tests (the comparison runs in UTC).
  `OpenStep` carries the step id, the activity, the recorded deadline
  string and `overdue_by` — `None` while the step is inside its deadline
  and the span past it once `now` has crossed it.
- **A step's own events and the record it ends with close it.** For the
  task's `step-started` events — filtered to the task, each carrying a
  step id, an activity and a deadline it can name — a step is open until
  the task's `step-ended` event for the same step id or a journal record
  of the matching kind written after the step started closes it. The
  matching kind follows ADR-0014 decision 9's list: an `implementation`
  step closes with a session record of activity `implementation`, a
  `review` step with a `review` record, and any other activity —
  `coordination`, `other`, or one the vocabulary does not know — with a
  session record of that same activity. `created_at` and `at` compare as
  UTC instants; a naive one reads as UTC the way the writer reads a
  naive `at`, a record whose `created_at` cannot be read never closes a
  step — it cannot be shown "written after" — and a `step-started` event
  whose `at` cannot be read is treated like the reader treats it:
  ordered before the dated events, so started before any dated record.
  A `step-started` event that lacks a step id, an activity or a deadline
  is not a step the view can name and reads as no step at all.
- **`status <task>` prints the overdue lines after the existing lines.**
  `print_task_detail` is unchanged and keeps its signature; the paths
  line prints ahead of it and `print_overdue_steps` behind it, so the
  record renderers' pin (`print_task_detail`'s own output) does not
  move. Each overdue line reads
  `Overdue step (this machine's process log): step=<id> activity=<a>
  deadline=<iso> past=<span>` — one line per step, the line itself
  saying where it came from, as ADR-0014's one-machine log requires —
  and the whole line goes through `escape_for_display` like every other
  rendered line (ADR-0015 decision 5). The span past the deadline prints
  in the duration units `step start --deadline` already accepts —
  `1h30m`, `2h5m`, `1d3h4m7s` — so an operator reads "how long past" in
  the units a deadline is given.
- **The list marks a task with an overdue step.** The tab-separated line
  gains a fourth field, `overdue-step`, only when the task has one — the
  id, state and title fields are untouched, so consumers of today's
  three fields read them unchanged.
- **The paths line prints once, ahead of the task output.** Both forms
  print `Paths: journal=<journal root> process-log=<log dir>
  local-state=<local state root>` on stdout — the resolved paths
  `placement.journal_root` and `local_state(placement)` already name, so
  in a sidecar the journal repository's paths print and the host's never
  enter the call (ADR-0014 decisions 5 and 13) — each path escaped like
  other displayed text. Printing it ahead of the task output keeps it
  present on the empty list and on the paths where `status` answers with
  an error. When `local_state` cannot resolve — git cannot name the
  common directory — the line still prints with the journal's path and
  `process-log=unavailable local-state=unavailable (<reason>)`, and the
  command still answers: a `status` that needed no git yesterday is not
  made to fail for want of one today. A missing `log/` directory is no
  error either — its path prints and `read_events` already reads it as
  empty.

## Risks

- [One record closes several overlapping steps of its kind] → the rule
  is per-step — any matching record written after *its* start closes it —
  which is the only reading journal records admit: they carry no step id
  to pair with (that pairing is what `step end` adds, optionally).
- [A forged or stale `at`/`created_at` skews what counts as open] → the
  log promises no forgery protection (ADR-0014 decision 8); an
  unreadable `created_at` never closes, and an unreadable `at` reads as
  started before every dated record, the same treatment `read_events`
  gives it.
- [The paths line exposes local layout] → it prints on `status` for the
  same user who owns the clone and the log; the paths are already the
  operator's own (decision 13 asks for exactly this).
