## ADDED Requirements

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
no task state and is not admitted after a terminal record. Nothing reads
agreements yet — the `agree` command, the gate's `require_agreement`
check and `status` showing agreement come with their own tasks.

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

### Requirement: An agreement record is a record of schema 7

An `agreement` record SHALL carry schema 7 — the schema the record type
was introduced under. An `agreement` record stamped below 7 SHALL be
refused at write, and on read: the field-admission rule of the record's
own schema admits `contract` only from 7, and the record-type gate
refuses the type below its schema whatever the record carries. A writer
SHALL stamp 7 through the minimum-schema derivation — the record type
itself needs it.

#### Scenario: an agreement record stamps schema 7
- **WHEN** an `agreement` record is built
- **THEN** it carries schema 7

#### Scenario: an agreement record stamped below 7 is refused at write
- **WHEN** an `agreement` record stamped below 7 is presented for write
- **THEN** it is refused and nothing is written

#### Scenario: an agreement record stamped below 7 is refused on read
- **WHEN** the journal holds an `agreement` record stamped below 7
- **THEN** reading the task's records refuses it
