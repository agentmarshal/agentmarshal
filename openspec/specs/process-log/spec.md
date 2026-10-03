# process-log Specification

## Purpose
The process log — a local working log under the clone's local state `log/`
directory: appended events, one JSON object per line with the envelope
`{"format": 1, "at": <UTC ISO-8601>, "event": <name>, "task"?: <id>, …}`.
ADR-0014 decisions 1, 6 and 7 and ADR-0022 section 7 make it not evidence and
not the journal: every writer appends to a file of its own, files rotate at a
bounded size with bounded retention, and one reader tolerates a torn tail and
event kinds it does not know. The gate never reads it (ADR-0014 decision 3).

## Requirements

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

### Requirement: A writer's file is rotated at a fixed bound

When a writer's file reaches the rotation size — a module constant of
10 MiB — it SHALL be renamed with a sequence suffix, the newest rotation
being `.1`; at most five rotated files per writer — a module constant —
SHALL be kept, the oldest deleted first, and later events SHALL land in a
fresh current file. A rotation whose renames fail SHALL NOT fail the write —
the event is already appended; the file keeps its name and the rotation is
retried at the next write.

#### Scenario: a file that reaches the limit is renamed with a sequence suffix
- **WHEN** a writer's file reaches the rotation size
- **THEN** it is renamed `<name>.jsonl.1` and the writer's current file is
  fresh

#### Scenario: at most five rotated files are kept, the oldest deleted first
- **WHEN** a writer rotates more than five times
- **THEN** only the five newest rotated files remain

#### Scenario: events keep flowing after a rotation
- **WHEN** a writer appends after its file has rotated
- **THEN** the new events land in the fresh current file

#### Scenario: a rotation that fails leaves the file and the event
- **WHEN** a writer's file reaches the rotation size but a rename fails
- **THEN** the event stays written, the file keeps its name and the next
  write retries the rotation

### Requirement: The log directory is bounded as a whole

Every process run is a writer of its own, so per-writer retention bounds
nothing: a writer that opens SHALL bound the `log/` directory as a whole.
While the regular files it holds total more than the directory cap — a
module constant of 50 MiB — the oldest files SHALL be deleted first, by
modification time. A rotated file — `<name>.jsonl.<n>` — SHALL be a
deletion candidate at any age, since no writer ever appends to one again; a
current `<name>.jsonl` file SHALL be a candidate only once its last write
is older than the abandonment age — a module constant — since a younger one
may still belong to a running writer. A file that is neither, and a
deletion that fails, SHALL be skipped: the bound is best-effort and SHALL
NOT fail the open that runs it.

#### Scenario: a directory over the bound sheds its oldest files first
- **WHEN** a writer opens against a directory holding more than the cap
- **THEN** files are deleted until the total fits, oldest by modification
  time first, and the open still succeeds

#### Scenario: a young current file is never deleted
- **WHEN** a writer opens against a directory over the cap whose current
  files were all written within the abandonment age
- **THEN** every current file stays — the bound gives way before a file a
  writer may still hold

#### Scenario: a rotated file is a candidate whatever its age
- **WHEN** a writer opens against a directory over the cap holding a
  freshly rotated file
- **THEN** the rotated file may be deleted even though it is young

### Requirement: The reader returns every event in order

The reader SHALL return the events of every file in the `log/` directory —
current files and rotated ones — as one list ordered by `at`, events sharing
an `at` keeping file-then-line order. A file's last line SHALL be skipped
unless it is newline-terminated, and a line that does not parse to a JSON
object SHALL be skipped. An event kind the reader does not know SHALL be
returned unchanged, as data. An event whose `at` is missing, not a string or
not a readable UTC timestamp SHALL be kept and ordered before the dated
events. A `log/` directory that does not exist SHALL read as empty.

#### Scenario: events come back in order of at, across files
- **WHEN** files hold events whose `at` values interleave
- **THEN** the reader returns them ordered by `at`, across all files

#### Scenario: an unfinished last line is skipped
- **WHEN** a file's last line is not newline-terminated
- **THEN** it is not returned, whether or not it parses, and every terminated
  line's event is

#### Scenario: a line that is not a JSON object is skipped
- **WHEN** a terminated line does not parse to a JSON object
- **THEN** it is skipped and the read does not fail

#### Scenario: an event kind the reader does not know is kept as data
- **WHEN** a file holds an event kind the reader does not know
- **THEN** the event is returned unchanged

#### Scenario: rotated files are read as well as current ones
- **WHEN** a writer's rotated files and its current file all hold events
- **THEN** the reader returns the events of all of them

#### Scenario: a missing log directory reads as empty
- **WHEN** the local state's `log/` directory does not exist
- **THEN** the reader returns no events

#### Scenario: an event without a readable at is kept, ordered first
- **WHEN** a file holds an event whose `at` is missing or unreadable
- **THEN** it is returned, ordered before the dated events

### Requirement: Creating a location is contained to the local state root

The local state's explicit creation call SHALL refuse, with a
`LocalStateError`, any location that is not the root itself or a path under
it — including a location that only comes under the root after `..` segments
or symlinks are resolved. A location under the root SHALL be created with any
missing parents.

#### Scenario: a location outside the root is refused
- **WHEN** a writer asks to create a directory outside the local state root
- **THEN** the call refuses with a `LocalStateError` and creates nothing

#### Scenario: a location that escapes through .. is refused
- **WHEN** a location is spelled under the root but resolves outside it
- **THEN** the call refuses with a `LocalStateError` and creates nothing

#### Scenario: a location under the root is created
- **WHEN** a writer asks to create the root or a path under it
- **THEN** the directory exists, along with any missing parents

### Requirement: The gate never reads the log

Nothing in the gate SHALL import the process-log module — the gate reads
nothing local (ADR-0014 decision 3).

#### Scenario: importing the gate does not import the process log
- **WHEN** `agentmarshal.journal.gate` is imported
- **THEN** `agentmarshal.process_log` is not in `sys.modules`

### Requirement: `step start` records a step's start and deadline

`agentmarshal step start` SHALL write one `step-started` event and print the
new step id on stdout — exactly the id and a newline. `--task` SHALL be
given and validated as a journal task identifier, `--activity` SHALL be
given and taken from the session activity vocabulary, and `--deadline`
SHALL be given — an ISO-8601 time or a duration such as `90m` measured from
the command's run — recorded as a UTC ISO-8601 timestamp. The event SHALL
carry `step` — the fresh identifier the command prints — `activity`, `pid`,
`pid_started_at` and `deadline`, and `actor` and `run_dir` only when
`--actor` and `--run-dir` are given; a given `--actor` or `--run-dir`
SHALL be non-empty and hold nothing that can forge rendered text.
Without `--pid` the command SHALL record its own parent process.
`pid_started_at` SHALL be the process's real start time where the
platform exposes it — Linux `/proc`, and the portable fallback the
design states — and a value naming it unknown where it cannot be
read, never a guess; the command SHALL work either way.

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
  identifier, an activity outside the session vocabulary, no deadline, or a
  deadline that is neither a readable ISO-8601 time nor a duration
- **THEN** the command refuses and no event lands

#### Scenario: an actor or run_dir that is empty or could forge rendered text is refused
- **WHEN** `step start` is given an `--actor` or a `--run-dir` that is
  empty or holds a character that could forge rendered text
- **THEN** the command refuses and no event lands

### Requirement: `step end` records a step's close

`agentmarshal step end` SHALL write one `step-ended` event and print the
step id on stdout. `--task` SHALL be given and validated as a journal task
identifier, `--step` SHALL be a step identifier of the form `step start`
prints, and `--outcome` MAY be given — when it is, it SHALL be a non-empty
word, holding no whitespace, that cannot forge rendered text. The event
SHALL carry `step` and, when given, `outcome`.

#### Scenario: an ended step lands as one step-ended event
- **WHEN** a harness runs `step end` with task and step, and once with an
  outcome
- **THEN** each run lands one `step-ended` event carrying `step`, and
  `outcome` when it was given, and prints the step id on stdout

#### Scenario: a step id that is not a step identifier is refused
- **WHEN** `step end` is given a `--step` that is not a step identifier of
  the form `step start` prints
- **THEN** the command refuses and no event lands

#### Scenario: an outcome that is not a clean word is refused
- **WHEN** `step end` is given an `--outcome` that is empty, holds
  whitespace or could forge rendered text
- **THEN** the command refuses and no event lands

### Requirement: the step commands write only the journal repository's process log

Neither `step` command SHALL write the journal: they append events to the
process log and nothing else. Both SHALL open the log through the resolved
local state, so in a sidecar the event lands in the journal repository's
process log and the host is never written. An `OSError` opening the
log — or any other filesystem error on the step path — SHALL reach
the caller as an error naming the log directory and what to do, never
a traceback.

#### Scenario: a step command leaves the journal untouched
- **WHEN** `step start` and `step end` run against an initialized project
- **THEN** the journal holds exactly what it held before

#### Scenario: in a sidecar the step event lands in the journal repository's log
- **WHEN** `step start` runs inside a sidecar project
- **THEN** the event lands in the sidecar repository's process log and the
  host's local state is untouched

#### Scenario: a filesystem failure opening the log is a named error
- **WHEN** a step command cannot open the process log — a read-only
  filesystem, a permission denial, a full disk
- **THEN** the caller gets an error naming the log directory and what
  to do — never a bare traceback — and no event lands

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
other step with a session record of that activity, and any step with a
`completed` or `abandoned` record — ADR-0014 decision 9 lists
`completed` among the records a step ends with. A `step-started`
event without a step id, an activity or a deadline is not a step the
view can name and SHALL read as no step. A journal record whose
`created_at` cannot be read as a time, or that was written no later
than the step started, SHALL NOT close the step. A step SHALL be
overdue when it is open and its deadline has passed; the comparison
runs in UTC, and one function SHALL compute a task's open steps and
their overdue spans for both forms of the command, the moment taken as
now being injectable so a test decides what has passed. The process log
SHALL be read once per status run, not once per task.

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

#### Scenario: a completed or abandoned record closes the step
- **WHEN** a `completed` or an `abandoned` record for the task was
  written after a step started
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

#### Scenario: the process log is read once per status run
- **WHEN** `status` runs in either form
- **THEN** the process log is read once for the run, however many tasks
  the run lists

### Requirement: `status` prints the actual paths in use

Both forms of `agentmarshal status` SHALL print, once and on stderr —
stdout keeping what the documentation promises the parsers reading it —
the actual paths of the journal, the process log and the local state in
use (ADR-0014 decision 13), each on a line of its own — `journal:
<path>`, `process log: <path>` and `local state: <path>` — and each
escaped like other displayed text. In a sidecar the journal and the
local state SHALL be the journal repository's. A missing process log
SHALL NOT be an error: the log's path still prints and the task reads
as having no steps. A process log that cannot be read SHALL be named on
stderr while `status` still answers. When the local state cannot be
resolved, the journal's path SHALL still print, the process log's and
the local state's lines SHALL mark them unavailable with the reason,
and the command SHALL still answer.

#### Scenario: both forms of status print the three paths once, on stderr
- **WHEN** `status` runs in either form
- **THEN** the actual paths of the journal, the process log and the
  local state print once each on stderr, each on a line of its own

#### Scenario: stdout stays what the documentation promises
- **WHEN** `status` runs in either form
- **THEN** stdout carries exactly what it carried before this change —
  what docs/quickstart.md and docs/sidecar.md promise a parser

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

#### Scenario: a process log that cannot be read is named on stderr
- **WHEN** the local state's `log/` exists but cannot be read — a
  permission denial, a file where the directory should be
- **THEN** `status` names it on stderr, reads no steps and does not
  fail

#### Scenario: a local state that cannot be resolved is named unavailable
- **WHEN** the local state cannot be resolved — git cannot name the
  repository's common directory
- **THEN** the journal's path still prints, the process log's and the
  local state's lines mark them unavailable with the reason, and
  `status` still answers

#### Scenario: a task without steps prints what it printed before
- **WHEN** a task has no steps at all
- **THEN** `status <task>` prints on stdout exactly what it printed
  before this change

### Requirement: `doctor` reports the project's overdue steps

`agentmarshal doctor` SHALL report every overdue step across the
project's tasks — one line per overdue step on stderr, naming the
task, the step id, the activity, the deadline and how long past it the
step is, each line saying it comes from this machine's process log —
using the same open/overdue computation `status` uses (`open_steps` in
`steps.py`), the moment taken as now being injectable. The report
SHALL be a report and nothing more: an overdue step SHALL NOT make
`doctor` exit non-zero, a process log that cannot be read SHALL be
named — its steps reading as none — rather than fail the run, and a
missing `log/` directory SHALL read as no steps. The process log SHALL
be read once per `doctor` run.

#### Scenario: doctor lists every overdue step across the project's tasks
- **WHEN** two tasks each have an open step past its deadline and a
  third has none
- **THEN** `doctor` prints one line per overdue step — each naming its
  task, the step id, the activity, the deadline and how long past it
  is — the line saying it comes from this machine's process log

#### Scenario: a step inside its deadline prints no overdue-step line
- **WHEN** a task's only step is open but inside its deadline
- **THEN** `doctor` prints no overdue-step line for it

#### Scenario: an overdue step never makes doctor exit non-zero
- **WHEN** a task has an overdue step and every check passes
- **THEN** `doctor` exits zero

#### Scenario: an unreadable process log is named, not a failure
- **WHEN** the local state's `log/` exists but cannot be read — a
  permission denial, a file where the directory should be
- **THEN** `doctor` names it, reads no steps and does not fail for it

#### Scenario: a missing process log reads as no steps
- **WHEN** the local state's `log/` directory does not exist
- **THEN** `doctor` reads no steps and does not fail

#### Scenario: the process log is read once per doctor run
- **WHEN** `doctor` runs against a project holding several tasks
- **THEN** the process log is read once for the run, however many
  tasks the project holds

### Requirement: `doctor` prints the actual paths in use

`agentmarshal doctor` SHALL print — on stderr, so the check report on
stdout keeps its shape — the actual paths of the journal, the process
log and the local state in use (ADR-0014 decision 13), each on a line
of its own — `journal: <path>`, `process log: <path>` and `local
state: <path>` — and each escaped like other displayed text. In a
sidecar the journal and the local state SHALL be the journal
repository's. When the local state cannot be resolved, its two lines
SHALL mark them unavailable with the reason and the journal's path
SHALL still print; when the project itself cannot be found, all three
lines SHALL mark themselves unavailable with the reason. The command
SHALL still report in either case.

#### Scenario: doctor prints the three paths once, on stderr
- **WHEN** `doctor` runs in an initialized project
- **THEN** the actual paths of the journal, the process log and the
  local state print once each on stderr, each on a line of its own,
  and none of them reaches stdout

#### Scenario: each path prints escaped like other displayed text
- **WHEN** a path holds a character the forgeable-text rule refuses
- **THEN** it prints escaped like any other displayed text

#### Scenario: in a sidecar the journal and local-state paths are the journal repository's
- **WHEN** `doctor` runs in a sidecar
- **THEN** the printed journal and local-state paths are the journal
  repository's, and the host's do not appear

#### Scenario: a local state that cannot be resolved is named unavailable
- **WHEN** the local state cannot be resolved — git cannot name the
  repository's common directory
- **THEN** the journal's path still prints, the process log's and the
  local state's lines mark them unavailable with the reason, and
  `doctor` still reports

#### Scenario: a project that cannot be found marks all three unavailable
- **WHEN** `doctor` runs outside an initialized project
- **THEN** all three lines mark themselves unavailable with the
  reason, and `doctor` still reports
