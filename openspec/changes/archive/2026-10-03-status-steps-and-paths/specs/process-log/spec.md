## ADDED Requirements

### Requirement: `status` shows a task's overdue steps

`agentmarshal status <task>` SHALL print, after the existing lines, one
line per overdue step of the task — carrying the step id, the activity,
the deadline and how long past it the step is — and nothing when the
task has none; each step line SHALL say it comes from this machine's
process log. `agentmarshal status` — the list — SHALL mark a task that
has an overdue step.

A step SHALL be open when the process log holds its `step-started`
event for the task and neither its `step-ended` event nor a journal
record of the matching kind for the same task written after the step
started closes it: an implementation step closes with an implementation
session record, a review step with a review record, a coordination or
other step with a session record of that activity. A `step-started`
event without a step id, an activity or a deadline is not a step the
view can name and SHALL read as no step. A journal record whose
`created_at` cannot be read as a time, or that was written no later
than the step started, SHALL NOT close the step. A step SHALL be
overdue when it is open and its deadline has passed; the comparison
runs in UTC, and one function SHALL compute a task's open steps and
their overdue spans for both forms of the command, the moment taken as
now being injectable so a test decides what has passed.

#### Scenario: an overdue step prints its line after the existing lines
- **WHEN** a task's step is open and past its deadline
- **THEN** `status <task>` prints, after the lines it prints today, one
  line per such step carrying the step id, the activity, the deadline
  and how long past it the step is — the line saying it comes from this
  machine's process log

#### Scenario: a task with no overdue step prints no step line
- **WHEN** a task has no step, or only steps inside their deadlines
- **THEN** `status <task>` prints no step line

#### Scenario: a step-ended event closes the step
- **WHEN** the log holds a step's `step-started` event and its
  `step-ended` event
- **THEN** the step is not open and prints no overdue line

#### Scenario: an implementation session closes an implementation step
- **WHEN** an implementation session record for the task was written
  after an implementation step started
- **THEN** the step is not open

#### Scenario: a review record closes a review step
- **WHEN** a review record for the task was written after a review step
  started
- **THEN** the step is not open

#### Scenario: a session of the activity closes a coordination or other step
- **WHEN** a session record of the step's activity for the task was
  written after a coordination or other step started
- **THEN** the step is not open

#### Scenario: a record written no later than the step started does not close it
- **WHEN** the only journal record of the matching kind was written no
  later than the step started
- **THEN** the step stays open

#### Scenario: an open step inside its deadline is not overdue
- **WHEN** a step is open and its deadline has not passed
- **THEN** it is not overdue and prints no line

#### Scenario: the task list marks a task that has an overdue step
- **WHEN** a task in the list has an overdue step and another does not
- **THEN** the first task's line carries the overdue-step mark and the
  second's does not

#### Scenario: another task's events are not its steps
- **WHEN** the log holds a `step-started` event naming another task
- **THEN** this task reads as having no such step

#### Scenario: a step-started event that cannot name a step reads as no step
- **WHEN** a `step-started` event lacks a step id, an activity or a
  deadline
- **THEN** it reads as no step

#### Scenario: both forms take the answer from one computation
- **WHEN** the detail and the list judge a task's steps
- **THEN** both take their answer from the one function that computes a
  task's open steps and their overdue spans

### Requirement: `status` prints the actual paths in use

Both forms of `agentmarshal status` SHALL print, once, the actual paths
of the journal, the process log and the local state in use — ADR-0014
decision 13 — each escaped like other displayed text. In a sidecar the
journal and the local state SHALL be the journal repository's. A
missing process log SHALL NOT be an error: the log's path still prints
and the task reads as having no steps. When the local state cannot be
resolved, the line SHALL name the journal's path and mark the local
state's paths unavailable with the reason, and the command SHALL still
answer.

#### Scenario: both forms of status print the three paths once
- **WHEN** `status` runs in either form
- **THEN** the actual paths of the journal, the process log and the
  local state print once each

#### Scenario: each path prints escaped like other displayed text
- **WHEN** a path holds a character the forgeable-text rule refuses
- **THEN** it prints escaped like any other displayed text

#### Scenario: in a sidecar the journal and local-state paths are the journal repository's
- **WHEN** `status` runs in a sidecar
- **THEN** the printed journal and local-state paths are the journal
  repository's, and the host's do not appear

#### Scenario: a missing process log is not an error
- **WHEN** the local state's `log/` directory does not exist
- **THEN** `status` still prints the log's path, reads no steps and
  does not fail

#### Scenario: a local state that cannot be resolved is named unavailable
- **WHEN** the local state cannot be resolved — git cannot name the
  repository's common directory
- **THEN** the line names the journal's path, marks the local-state
  paths unavailable with the reason, and `status` still answers

#### Scenario: a task without steps prints what it printed before, apart from the paths line
- **WHEN** a task has no steps at all
- **THEN** `status <task>` prints exactly the lines it printed before
  this change, apart from the one paths line
