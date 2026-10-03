+++
schema = 2
id = "CR-162"
title = "status shows a step past its deadline and prints where the journal, the process log and the local state actually are"
scope = [
  "src/agentmarshal/journal/status_view.py",
  "src/agentmarshal/steps.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/status-steps-and-paths/",
  "openspec/changes/archive/",
  "openspec/specs/process-log/",
]
acceptance = [
  "the change status-steps-and-paths has a proposal, a design.md and a delta spec modifying the process-log capability (MODIFIED requirements keep their exact headers, ADDED for new ones); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "a step is open when the process log has its `step-started` event and neither its `step-ended` event nor a journal record of the matching kind for the same task written after the step started (an implementation step closes with an implementation session, a review step with a review record, a coordination or other step with a session of that activity); a step is overdue when it is open and its deadline has passed; one function computes this for a task and is tested on each case",
  "`agentmarshal status <task>` prints, after the existing lines, one line per overdue step (step id, activity, deadline, how long past) and nothing when there is none; `agentmarshal status` (the list) marks a task that has an overdue step; the step lines say they come from this machine's process log",
  "both forms of `status` print, once, the actual paths of the journal, the process log and the local state in use (ADR-0014 decision 13), each escaped like other displayed text; in a sidecar the journal and the local state are the journal repository's; a missing process log is not an error",
  "a task without steps prints exactly what it prints today apart from the paths line, existing status tests change only by that line, and the full CI sequence passes",
]
documents = ["openspec/specs/process-log/"]
+++

# CR-162: status shows overdue steps and the actual paths

## Context

ADR-0014 decision 9 (as amended 2026-10-03): the core records step events
in the process log, and `status` and `doctor` show a step past its
deadline; a step is closed by the record it ends with, `step end` being an
optional addition (ADR-0022 section 7). Decision 13: `doctor` and `status`
print the actual paths — today `status` prints only the placement kind.
CR-157 shipped `step start` and `step end`. `doctor` is a separate task.

## Objective

An operator sees, in `status`, which steps ran past their deadline and
where everything lives.

## Acceptance Criteria

As in the header.

## Non-Goals

- `doctor` (a separate task).
- Stopping or signalling any process (the watchdog is a supplied component).
- Steps on other machines (the log is local; ADR-0014).
