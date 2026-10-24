# record-lifecycle Specification

## Purpose
Which records a task still admits once it is closed, and which the writer
refuses. The projection has always had the rule; this capability is about the
side that writes, because a record the projection refuses to read cannot be
taken back out of an append-only journal.

## Requirements

### Requirement: A closed task admits only what its projection admits
A command that writes a record into an existing task SHALL refuse when the
task's projected state is terminal, unless the record is one the projection
admits after a terminal record — a measurement or a reopening. The refusal
SHALL name the state the task is in, and SHALL leave the journal exactly as
it was.

The rule is the projection's own. A session record accrues after completion
because measurements are not lifecycle (ADR-0005 Decision 3), and a `check`
record accrues likewise, a measurement admitted after either terminal
state. A reopening is the one lifecycle mutation admitted after a terminal
record — Decision 3 predates it and states the opposite, which that ADR's
own status note records. Every other record makes the task unreadable from
then on.

#### Scenario: a verdict is refused on a completed task
- **WHEN** a review verdict is submitted for a task that has completed
- **THEN** no record is written, the refusal names the state, and the journal
  still validates

#### Scenario: a verdict is refused on an abandoned task
- **WHEN** a review verdict is submitted for a task that was abandoned
- **THEN** no record is written, the refusal names the state, and the journal
  still validates

#### Scenario: a measurement is still accepted after completion
- **WHEN** a session record is written for a task that has completed
- **THEN** it is accepted, because the projection admits it

#### Scenario: a check record is still accepted after completion
- **WHEN** a check record is written for a task that has completed
- **THEN** it is accepted, because the projection admits it

#### Scenario: a check record is still accepted after abandonment
- **WHEN** a check record is written for a task that was abandoned
- **THEN** it is accepted, because the projection admits it

#### Scenario: a reopening is still accepted after completion
- **WHEN** a completed task is reopened
- **THEN** it is accepted, because the projection admits it

#### Scenario: every writing command refuses a closed task
- **WHEN** each command that writes a record into a task is run against a
  completed task
- **THEN** each one refuses, and none of them leaves a record behind

### Requirement: A closed task costs no reviewer run
A review launched against a closed task SHALL be refused before the configured
reviewer is run, for every binding the launcher accepts. The `findings-review`
capability already requires this of a review bound to a finding; the lifecycle
rule is the same one and holds for a commit review too, so neither binding
spends a run to discover a state the journal already knows.

#### Scenario: a launched review on a closed task runs no reviewer
- **WHEN** `review` is launched for a task that has completed or been
  abandoned, with either binding
- **THEN** no reviewer process is started and no record is written

### Requirement: The merge gate admits what the projection admits after a terminal record
A candidate that only appends to a task closed at base SHALL pass the gate's
base-state check when every record it adds is one the projection admits after
that task's terminal record: a measurement in any terminal state, and a
reopening only when the task was completed. Anything else remains refused as
before. The gate SHALL read what is admitted from the projection's own rule, not
from a second list of its own.

#### Scenario: a reopening lands through the gate
- **WHEN** a candidate adds only a reopening record to a task completed at base
- **THEN** the gate's base-state check passes, and the projection of the
  candidate is open

#### Scenario: an abandoned task cannot be reopened through the gate
- **WHEN** a candidate adds a reopening record to a task abandoned at base
- **THEN** the gate refuses, as the projection would

#### Scenario: measurements still accrue after completion
- **WHEN** a candidate adds only session records to a task closed at base
- **THEN** the gate's base-state check passes, as before

#### Scenario: check records still accrue after completion
- **WHEN** a candidate adds only check records to a task completed at base
- **THEN** the gate's base-state check passes, as it does for a session
  append

#### Scenario: check records still accrue after abandonment
- **WHEN** a candidate adds only check records to a task abandoned at base
- **THEN** the gate's base-state check passes, as it does for a session
  append

#### Scenario: other work on a closed task is still refused
- **WHEN** a candidate adds a review record to a task closed at base
- **THEN** the gate refuses, as before

### Requirement: `status --base` lists the task's records the ref does not hold

`agentmarshal status <task> --base <ref>` SHALL print, after the detail
view the command prints today and before any process-log lines, the
task's records present in the journal's working tree whose paths the
tree of `<ref>` does not hold: a header naming the ref as given, then
one `- <id> <type>` line per record in the task's stored order — or one
line naming the ref and saying there are none. The comparison SHALL be
by record path — a path the ref's tree holds is published whatever its
content there — and SHALL run in the repository the journal lives in:
the project repository in the embedded placement, the sidecar
repository in the sidecar placement, never the host repository's refs.
`<ref>` SHALL resolve to a commit or the command refuses, nonzero,
naming the ref as given — printing no part of the view first. `--base`
without a named task SHALL refuse, because the listing is per task.
Without `--base` the command SHALL print exactly what it prints today.
Every value the listing prints — the ref, the record id, the record
type — SHALL be escaped for display like every other value the view
prints.

#### Scenario: records the ref does not hold are listed
- **WHEN** the working tree holds records whose paths the tree of the
  named ref does not — a session and an amendment written since the
  commit the ref names
- **THEN** after the detail view a header names the ref and one line
  each prints the record's id and type

#### Scenario: no records the ref lacks prints one line
- **WHEN** every record path the working tree holds is held by the
  ref's tree
- **THEN** one line after the detail view names the ref and says there
  are none

#### Scenario: without --base the view is unchanged
- **WHEN** `status <task>` runs with no `--base`
- **THEN** the output is byte for byte what it prints today

#### Scenario: an unknown ref refuses naming it
- **WHEN** the named ref resolves to no commit in the journal's
  repository
- **THEN** the command returns nonzero, names the ref as given on
  stderr, and prints no part of the view

#### Scenario: a sidecar compares against the journal repository's ref
- **WHEN** the journal lives in a sidecar repository and the named ref
  is a commit of that repository — not of the host's
- **THEN** the listing answers against the sidecar's tree, and the
  host's refs are never consulted

#### Scenario: a value the listing prints is escaped on display
- **WHEN** the ref as given carries a character display refuses
- **THEN** the refusal — as the listing's lines would — prints the
  value's escaped form

#### Scenario: --base without a task is refused
- **WHEN** `status --base <ref>` runs with no task named
- **THEN** the command refuses, nonzero, saying the flag applies only to
  a named task

### Requirement: The merge gate projects every task the candidate appends to

For every task other than the judged one to which the candidate adds
records, the gate SHALL project that task's merged records — the
target's plus the candidate's — with the same lifecycle projection it
applies to the judged task and the same closed-at-base admission rule,
and SHALL refuse with one FAIL line naming the task and the
projection's reason when the projection refuses.

#### Scenario: a reopening added to another task abandoned at base is refused
- **WHEN** a candidate for one task adds a `reopened` record to another
  task that was abandoned at base
- **THEN** the gate refuses with one FAIL line naming the task and the
  projection's reason

#### Scenario: work bundled with a reopening on another closed task is refused
- **WHEN** a candidate adds a `reopened` record and a work record to a
  task other than the judged one that was completed at base
- **THEN** the gate refuses with one FAIL line naming the task as
  already closed at base

#### Scenario: records another task's projection admits are not refused
- **WHEN** a candidate adds to another task a record its lifecycle
  admits — a measurement on an open task, an admitted append on a
  closed one
- **THEN** the lifecycle check reports consistent, as it does today
