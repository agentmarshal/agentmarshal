## Why

ADR-0014 decision 9 — as amended 2026-10-03 — has `status` and `doctor`
show a step past its deadline, and decision 13 obliges `doctor` and
`status` to print the actual paths — today `status` prints only the
placement kind. CR-157 shipped `step start` and `step end`, so the
`step-started` and `step-ended` events land in the process log, but
nothing reads them back: an operator cannot see which steps ran past
their deadline, nor where the journal, the process log and the local
state actually live. `doctor` is a separate task.

## What Changes

- One function next to the step commands computes a task's open steps
  and their overdue spans from the process log and the journal: a step
  is open when the log holds its `step-started` event and neither its
  `step-ended` event nor a journal record of the matching kind for the
  same task written after the step started closes it — an implementation
  step closes with an implementation session, a review step with a
  review record, a coordination or other step with a session of that
  activity, and any step with a `completed` or `abandoned` record
  (ADR-0022 section 7: `step end` is the optional addition for
  a step that ends with no record). A step is overdue when it is open
  and its deadline has passed; the comparison runs in UTC and the moment
  taken as now is injectable.
- `agentmarshal status <task>` prints, after the existing lines, one
  line per overdue step — step id, activity, deadline and how long past
  — each line saying it comes from this machine's process log, and
  nothing when there is none.
- `agentmarshal status` — the list — marks a task that has an overdue
  step.
- Both forms print, once and on stderr — one line each — the actual
  paths of the journal, the process log and the local state in use, each
  escaped like other displayed text, so stdout stays what the
  documentation promises a parser; in a sidecar the journal and the
  local state are the journal repository's; a missing process log is not
  an error, and one that cannot be read is named on stderr while
  `status` still answers.

## Capabilities

- modified: `process-log`

## Impact

- `src/agentmarshal/steps.py` (the computation beside the producers),
  `src/agentmarshal/journal/status_view.py` (the paths lines and the
  overdue-step lines), `src/agentmarshal/cli.py` (`_run_status`), and
  `tests/`; the two byte-exact `status` stdout pins do not change — the
  paths went to stderr.
- `openspec/specs/process-log/spec.md` on archive.
- Steps on other machines stay invisible — the log is local (ADR-0014
  decision 8); no watchdog or process control, which is a supplied
  component's job.
