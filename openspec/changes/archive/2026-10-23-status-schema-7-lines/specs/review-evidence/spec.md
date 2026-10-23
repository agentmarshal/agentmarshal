## ADDED Requirements

### Requirement: `status` shows a check record on a line of its own

`agentmarshal status <task>` SHALL print one line per `check` record —
after the record's id, type and time: the check's `name`, its `result`,
the commit's short form, and `failed_step` when the record carries one —
and SHALL name the recorder. A recorder that is not a declared actor
SHALL be shown as not a declared actor. Every value taken from the
record SHALL be escaped on display as the other record lines' values are.

#### Scenario: status shows a check record's line
- **WHEN** `agentmarshal status <task>` lists a `check` record
- **THEN** its line carries `name`, `result`, the commit's short form and
  `recorded_by`

#### Scenario: a check record's failed step is shown when present
- **WHEN** `agentmarshal status <task>` lists a `check` record carrying
  `failed_step`, and one carrying none
- **THEN** the first line names the failed step and the second shows no
  `failed_step`

#### Scenario: a recorder that is not a declared actor is shown as such
- **WHEN** `agentmarshal status <task>` lists a `check` record whose
  `recorded_by` is not a declared actor
- **THEN** the line names the recorder and says it is not a declared
  actor

#### Scenario: a check record's values stay on their own line
- **WHEN** `agentmarshal status <task>` lists a `check` record whose
  `name`, `result`, `failed_step` or `recorded_by` carries a character
  that could add a line to rendered output or reorder it — a value an
  older schema's journal can hold where today's read rules do not reach
- **THEN** each refused character prints as its escape and the record
  stays on the one line
