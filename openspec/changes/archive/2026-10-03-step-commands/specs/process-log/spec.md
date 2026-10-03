## MODIFIED Requirements

### Requirement: A writer appends events to a file of its own under the log directory

A writer SHALL append each event under the local state's `log/` directory as
one JSON object on one line carrying `"format": 1`, `"at"` — the UTC ISO-8601
timestamp of the write — `"event"` naming the event kind, and `"task"` only
when a task id is given; the event kind's own fields SHALL be carried as
given, except that a field naming an envelope key — `format`, `at`, `event`
or `task` — SHALL be refused with a `ProcessLogError` rather than override
the envelope. An event that cannot be encoded as strict JSON — a non-finite
number or a value whose type JSON cannot carry — SHALL be refused with a
`ProcessLogError` before any line lands, and an `OSError` while appending
SHALL reach the caller as an error naming the log file and what to do. The
file SHALL be the writer's own — named so that no second writer in any
process appends to it — and each event SHALL be written by opening the file
in append mode and writing one line per call, so that two processes writing
at once never interleave or tear each other's lines. The `log/` directory
SHALL be created through the local state's explicit creation call.

#### Scenario: an event lands as one JSON object on one line
- **WHEN** a writer appends events
- **THEN** its file holds one line per event, each line a JSON object with
  `"format": 1`, a UTC ISO-8601 `"at"` and `"event"` naming the kind

#### Scenario: a task id rides along only when given
- **WHEN** a writer appends one event with a task id and one without
- **THEN** the first line carries `"task"` and the second does not

#### Scenario: the writer's file sits under the local state's log directory
- **WHEN** a writer is opened against a resolved local state
- **THEN** its file sits under the local state's `log/` directory and that
  directory exists

#### Scenario: two writers never share a file
- **WHEN** two writers are opened — in one process or in two
- **THEN** each appends to a different file

#### Scenario: an event field naming an envelope key is refused
- **WHEN** a writer appends an event whose own fields name `format`, `at`,
  `event` or `task`
- **THEN** the write is refused with a `ProcessLogError` and no line lands

#### Scenario: concurrent writers never interleave or tear each other's lines
- **WHEN** two processes append events at the same time
- **THEN** every line of every file reads back as a complete JSON object and
  every event either process wrote is there

#### Scenario: an event that cannot be encoded as strict JSON is refused
- **WHEN** a writer appends an event carrying a non-finite number or a value
  whose type JSON cannot carry
- **THEN** the write is refused with a `ProcessLogError` and no line lands

#### Scenario: a failed append names the log file and what to do
- **WHEN** appending an event's line fails with an `OSError`
- **THEN** the caller gets an error naming the log file and what to do —
  never a bare traceback

## ADDED Requirements

### Requirement: `step start` records a step's start and deadline

`agentmarshal step start` SHALL write one `step-started` event and print the
new step id on stdout. `--task` SHALL be given and validated as a journal
task identifier, `--activity` SHALL be given and taken from the session
activity vocabulary, and `--deadline` SHALL be given — an ISO-8601 time or a
duration such as `90m` measured from the command's run — recorded as a UTC
ISO-8601 timestamp. The event SHALL carry `step` — the fresh identifier the
command prints — `activity`, `pid`, `pid_started_at` and `deadline`, and
`actor` and `run_dir` only when `--actor` and `--run-dir` are given. Without
`--pid` the command SHALL record its own parent process. `pid_started_at`
SHALL be the process's real start time where the platform exposes it — Linux
`/proc`, and the portable fallback the design states — and a value naming it
unknown where it cannot be read, never a guess; the command SHALL work
either way.

#### Scenario: a started step lands as one step-started event and its id is printed
- **WHEN** a harness runs `step start` with task, activity and deadline
- **THEN** one `step-started` event lands carrying `step`, `activity`,
  `pid`, `pid_started_at` and `deadline`, and the command prints the step
  id on stdout

#### Scenario: the deadline accepts an ISO-8601 time or a duration
- **WHEN** `step start` is given `--deadline` as an ISO-8601 time, and
  again as a duration such as `90m`
- **THEN** each run records a UTC ISO-8601 deadline — the given time for
  the first, the duration measured from the run for the second

#### Scenario: without --pid the parent process is recorded
- **WHEN** `step start` runs without `--pid`
- **THEN** the event's `pid` is the command's own parent process

#### Scenario: pid_started_at is read where the platform allows and names itself unknown where it cannot
- **WHEN** `step start` records a process whose start time the platform
  exposes, and one it cannot read
- **THEN** the first event's `pid_started_at` is the process's start time,
  the second's names it unknown, and both commands succeed

#### Scenario: actor and run_dir ride along only when given
- **WHEN** `step start` runs once with `--actor` and `--run-dir` and once
  without them
- **THEN** the first event carries `actor` and `run_dir` and the second
  does not

#### Scenario: a malformed task id, an unknown activity or a missing deadline is refused
- **WHEN** `step start` is given a task id that is not a journal task
  identifier, an activity outside the session vocabulary, or no deadline
- **THEN** the command refuses and no event lands

### Requirement: `step end` records a step's close

`agentmarshal step end` SHALL write one `step-ended` event. `--task` SHALL
be given and validated as a journal task identifier, `--step` SHALL name
the step the event closes, and `--outcome` MAY be given — when it is, it
SHALL be a non-empty word, holding no whitespace, that cannot forge
rendered text. The event SHALL carry `step` and, when given, `outcome`.

#### Scenario: an ended step lands as one step-ended event
- **WHEN** a harness runs `step end` with task and step, and once with an
  outcome
- **THEN** each run lands one `step-ended` event carrying `step`, and
  `outcome` when it was given

#### Scenario: an outcome that is not a clean word is refused
- **WHEN** `step end` is given an `--outcome` that is empty, holds
  whitespace or could forge rendered text
- **THEN** the command refuses and no event lands

### Requirement: the step commands write only the journal repository's process log

Neither `step` command SHALL write the journal: they append events to the
process log and nothing else. Both SHALL open the log through the resolved
local state, so in a sidecar the event lands in the journal repository's
process log and the host is never written.

#### Scenario: a step command leaves the journal untouched
- **WHEN** `step start` and `step end` run against an initialized project
- **THEN** the journal holds exactly what it held before

#### Scenario: in a sidecar the step event lands in the journal repository's log
- **WHEN** `step start` runs inside a sidecar project
- **THEN** the event lands in the sidecar repository's process log and the
  host's local state is untouched
