## MODIFIED Requirements

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
