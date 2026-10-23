## ADDED Requirements

### Requirement: `status` shows an agreement record on a line of its own

`agentmarshal status <task>` SHALL print one line per `agreement` record
— after the record's id, type and time: the agreed hash's short form —
and SHALL name the recorder, so `status` shows who agreed (ADR-0018
decision 2). A recorder that is not a declared actor SHALL be shown as
not a declared actor. Every value taken from the record SHALL be escaped
on display as the other record lines' values are.

#### Scenario: status shows an agreement record's line
- **WHEN** `agentmarshal status <task>` lists an `agreement` record
- **THEN** its line carries the agreed hash's short form and
  `recorded_by`

#### Scenario: a recorder that is not a declared actor is shown as such
- **WHEN** `agentmarshal status <task>` lists an `agreement` record
  whose `recorded_by` is not a declared actor
- **THEN** the line names the recorder and says it is not a declared
  actor

#### Scenario: an agreement record's values stay on their own line
- **WHEN** `agentmarshal status <task>` lists an `agreement` record
  whose `contract` or `recorded_by` carries a character that could add a
  line to rendered output or reorder it — a value an older schema's
  journal can hold where today's read rules do not reach
- **THEN** each refused character prints as its escape and the record
  stays on the one line

### Requirement: `status` shows whether an agreement is recorded for the contract's current text

After the record lines, `agentmarshal status <task>` SHALL print one
line when the task carries no `agreement` record, saying no agreement is
recorded — the absence is shown, instead of being indistinguishable
from agreement never asked for (ADR-0018 decision 2) — and SHALL print
one line naming both short hashes when the task's latest `agreement`
record's `contract` differs from the contract's current hash, saying
the agreement is for an earlier contract text. The comparison SHALL be
against the contract's current hash as `contract_sha256` computes it on
the task's `contract.md`, not against the hash `opened` or `amendment`
pin. `status` SHALL print no agreement line when the latest agreement's
hash equals the contract's current hash, or when the contract cannot be
read or hashed. Neither line SHALL fail the command or change the
task's state — visibility, not a requirement.

#### Scenario: a task with no agreement record says so
- **WHEN** `agentmarshal status <task>` runs on a task carrying no
  `agreement` record
- **THEN** it prints one line after the record lines saying no agreement
  with the contract is recorded

#### Scenario: an agreement for an earlier contract text is said
- **WHEN** the task's latest `agreement` record's `contract` differs
  from the contract's current hash
- **THEN** `status <task>` prints one line after the record lines saying
  the agreement is for an earlier contract text, naming the agreed and
  the current short hashes

#### Scenario: the comparison is against the current hash, not the pin
- **WHEN** the contract has drifted from its pin and the latest
  `agreement` record's `contract` equals the pin but not the current
  hash
- **THEN** `status <task>` still prints the earlier-text line

#### Scenario: an agreement at the current hash prints no agreement line
- **WHEN** the task's latest `agreement` record's `contract` equals the
  contract's current hash
- **THEN** `status <task>` prints no agreement line after the records

#### Scenario: a contract that cannot be read or hashed prints nothing
- **WHEN** the task carries an `agreement` record and its `contract.md`
  cannot be read or hashed
- **THEN** `status <task>` prints no agreement line and still answers

#### Scenario: the line never fails the command
- **WHEN** a task carries no `agreement` record, or its latest agreement
  is for an earlier contract text
- **THEN** `status <task>` still answers, printing the line, and the
  task's state is unchanged

## MODIFIED Requirements

### Requirement: An agreement record carries an actor's agreement with the contract at a hash

From schema 7 the journal admits an `agreement` record: a declared actor
states agreement with the contract at a stated hash (ADR-0018 decision 2,
ADR-0022 section 3). The record SHALL carry `contract` — the hash agreed
with, exactly 64 lowercase hex characters, the form `contract_sha256`
produces and `opened`/`amendment` carry — and the field SHALL pass the
forgeable-text rule registered for this record type and field, with no
length bound applying to it. The record SHALL name its recorder in
`recorded_by` with `recorded_by_source`, as `finding` and `check` already
do; a recorder that is not a declared actor is accepted. Any declared
actor may record agreement — there are no roles. The record projects to
no task state and is not admitted after a terminal record. The `agree`
command writes the record, and `status` shows who agreed and whether an
agreement is recorded for the contract's current text; the gate's
`require_agreement` check comes with its own task.

#### Scenario: an agreement record is written and read back
- **WHEN** an `agreement` record carries `contract`
- **THEN** it is written and validated, and the field reads back as given

#### Scenario: a contract hash that is not 64 lowercase hex is refused
- **WHEN** an `agreement` record's `contract` is not exactly 64 lowercase
  hex characters
- **THEN** it is refused and nothing is written

#### Scenario: an agreement record that carries no contract is refused
- **WHEN** an `agreement` record carries no `contract`
- **THEN** it is refused and nothing is written

#### Scenario: a contract that could forge a rendered line is refused
- **WHEN** an `agreement` record's `contract` carries a character that
  could add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: an agreement record that names no recorder is refused
- **WHEN** an `agreement` record carries neither `recorded_by` nor
  `recorded_by_source`
- **THEN** it is refused

#### Scenario: a recorder that is not a declared actor is accepted
- **WHEN** an `agreement` record names a recorder that is not a declared
  actor
- **THEN** it is written, and `recorded_by` carries the name as given

#### Scenario: a candidate adding an agreement record is admitted
- **WHEN** a candidate adds an `agreement` record to an open task
- **THEN** the record check the gate runs admits it, as it admits the
  other schema-7 record types the projection admits before a terminal
  record

#### Scenario: an agreement on a closed task is refused
- **WHEN** an `agreement` record is written for a task that has
  completed or been abandoned
- **THEN** no record is written, the refusal names the state, and the
  journal still validates

#### Scenario: status and validate handle a task carrying an agreement record
- **WHEN** a task carries an `agreement` record
- **THEN** `agentmarshal status` and `agentmarshal validate` answer
  without failing
