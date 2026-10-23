## ADDED Requirements

### Requirement: `agree` records an actor's agreement with the contract at its current hash

`agentmarshal agree --task <id>` SHALL write one `agreement` record whose
`contract` is the `contract_sha256` of the task's `contract.md` as it
stands — in a sidecar, the journal repository's copy, the one `amend`
pins — and SHALL print the record's path, the agreed hash and the
recorder, escaping the recorder where it could forge a rendered line.
The task SHALL be one an `agreement` record may be written for: an
unknown task, or one whose projected state does not admit the record,
SHALL be refused naming the reason, writing nothing. Recording agreement
again on the same task SHALL write another record.

#### Scenario: an agreement is written at the contract's current hash
- **WHEN** `agree` runs on an open task
- **THEN** one `agreement` record is written at schema 7 whose `contract`
  is the `contract_sha256` of `contract.md` as it stands, and the output
  prints the agreed hash and the recorder

#### Scenario: an unknown task is refused writing nothing
- **WHEN** `agree` names a task the journal does not carry
- **THEN** it is refused naming the task, no record is written, and the
  journal still validates

#### Scenario: a completed or abandoned task is refused writing nothing
- **WHEN** `agree` runs on a task that has completed or been abandoned
- **THEN** it is refused naming the state and no record is written

#### Scenario: a completed task that accrued a check is still refused
- **WHEN** `agree` runs on a task that completed and then accrued a
  `check` record
- **THEN** it is refused naming the state — the measurement reopened
  nothing — and no record is written

#### Scenario: agreement is recorded more than once on the same task
- **WHEN** `agree` runs twice on the same open task
- **THEN** each run writes its own `agreement` record

#### Scenario: a contract read either way hashes the same
- **WHEN** `agree` runs on a task whose `contract.md` is saved with CRLF
  endings where the pin was made on LF
- **THEN** the record's `contract` equals the LF hash — the command
  agrees with the text, not the bytes' endings

### Requirement: `agree` refuses a contract that drifted from its last pin

When the task's records pin a contract — the `contract` of the latest
`opened` or `amendment` record that carries one — `agree` SHALL compare
the contract's current hash against that pin and SHALL refuse when they
differ, naming both short hashes and that the edit should be recorded
with `amend`, writing nothing. A task whose records carry no hash has no
pin; `agree` SHALL then record agreement at the current hash.

#### Scenario: a drifted contract is refused naming the pin and amend
- **WHEN** the contract's current hash differs from the task's latest
  pin
- **THEN** `agree` is refused naming the pinned and the current short
  hashes and that the edit should be recorded with `amend`, and no
  record is written

#### Scenario: a task whose records carry no pin agrees at the current text
- **WHEN** no `opened` or `amendment` record of the task carries
  `contract`
- **THEN** `agree` writes the agreement at the contract's current hash

#### Scenario: the latest hash-carrying pin is the one compared
- **WHEN** an `amendment` recorded after the `opened` record carries a
  newer pin
- **THEN** `agree` compares the contract against the amendment's hash,
  not the opened record's

### Requirement: `--contract` binds agreement to the hash the actor read

`agentmarshal agree --contract <hash>` SHALL write the record only when
the value equals the contract's current hash. A value that is not
exactly 64 lowercase hexadecimal characters SHALL be refused naming the
`--contract` field, writing nothing; a well-formed value that differs
from the current hash SHALL be refused naming both, writing nothing.

#### Scenario: --contract equal to the contract's current hash writes
- **WHEN** `agree --contract` names the contract's current hash
- **THEN** the agreement record is written at that hash

#### Scenario: --contract differing is refused naming both hashes
- **WHEN** `agree --contract` names a well-formed hash that is not the
  contract's current hash
- **THEN** it is refused naming the given and the current hashes, and no
  record is written

#### Scenario: --contract not exactly 64 lowercase hex is refused naming the field
- **WHEN** `agree --contract` names a value that is not exactly 64
  lowercase hexadecimal characters
- **THEN** it is refused naming the `--contract` field, before the
  journal is touched

### Requirement: `agree` names its recorder or writes nothing

`agree` SHALL resolve its recorder as `resolve_recorded_by` resolves —
the environment override, the project actors table, the git identity —
and SHALL refuse clearly when none resolves, before anything is created.
A recorder who is not a declared actor SHALL be accepted, the record
written naming the recorder and its source, and the output SHALL say the
recorder is not a declared actor. Any actor may agree; no role restricts
it.

#### Scenario: no resolvable recorder identity is refused writing nothing
- **WHEN** `agree` can resolve no recorder — no override, no actors-table
  match, no git identity
- **THEN** it is refused naming the reason, and the records directory is
  untouched

#### Scenario: a recorder who is not a declared actor is accepted and named
- **WHEN** `agree`'s recorder is not a declared actor
- **THEN** the record is written with `recorded_by` and
  `recorded_by_source` as resolved, and the output notes the recorder is
  not a declared actor

#### Scenario: a declared actor records with no undeclared note
- **WHEN** `agree`'s recorder names a declared actor — whether resolved
  through the actors table or named by the override
- **THEN** the record is written and no undeclared-actor note is printed

#### Scenario: the recorder is escaped where it could forge a line
- **WHEN** the recorder's name carries a character that could add a line
  to rendered output or reorder it
- **THEN** the output prints the escaped form, in the recorder line and
  the note alike

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
command writes the record; the gate's `require_agreement` check and
`status` showing agreement come with their own tasks.

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
