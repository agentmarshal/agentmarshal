## ADDED Requirements

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
