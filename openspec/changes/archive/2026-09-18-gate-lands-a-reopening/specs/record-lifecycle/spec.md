## ADDED Requirements

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

#### Scenario: other work on a closed task is still refused
- **WHEN** a candidate adds a review record to a task closed at base
- **THEN** the gate refuses, as before
