## ADDED Requirements

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
