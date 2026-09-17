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
SHALL name the state the task is in, and SHALL leave the journal exactly as it
was.

The rule is the projection's own (ADR-0005 Decision 3): a session record
accrues after completion, a reopening is the one admitted lifecycle mutation,
and every other record makes the task unreadable from then on.

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

#### Scenario: a reopening is still accepted after completion
- **WHEN** a completed task is reopened
- **THEN** it is accepted, because the projection admits it

#### Scenario: every writing command refuses a closed task
- **WHEN** each command that writes a record into a task is run against a
  completed task
- **THEN** each one refuses, and none of them leaves a record behind

### Requirement: The launcher refuses before it spends a reviewer run
A review launched against a closed task SHALL be refused before the configured
reviewer is run, so a closed task costs no reviewer run to discover.

#### Scenario: a launched review on a closed task runs no reviewer
- **WHEN** `review` is launched for a task that has completed
- **THEN** no reviewer process is started and no record is written
