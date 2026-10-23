## Purpose

The gate's enforcement of a project's `contract.require_agreement`
setting — what the check compares, what its transcript line says, and
what the transcript carries by default.

## ADDED Requirements

### Requirement: The gate can be made to require a recorded agreement with the contract it judges

When `contract.require_agreement` is true in the project file the gate
reads its settings from — the journal repository's `project.json`, the
working-tree read the `changes_required` threshold makes — the
implementation lane's transcript SHALL carry one line for the agreement
check, printed after the scope line. The check SHALL judge whether the
task's records — the ones `load_task_status` projects, the journal
repository's working tree where `agree` appends — hold an `agreement`
record whose `contract` equals the `contract_sha256` of the contract the
gate judges against: the merge-base tree's contract in the embedded
placement, the sidecar working tree's in the sidecar placement. The line
SHALL name the judged contract's short hash — the first seven
characters, as `status` renders hashes — as `PASS: agreement recorded
for contract <hash>` on success, and on failure `FAIL`, refusing the
candidate and saying that agreement is recorded with `agentmarshal
agree`. Any `agreement` record carrying the hash SHALL satisfy the
check, whoever recorded it — there are no roles (ADR-0018 decision 2).
When the task carries `agreement` records but none carries the hash, the
FAIL line SHALL say an agreement exists for another hash and SHALL name
the latest `agreement` record's short hash beside the judged one. The
check SHALL run however the run was asked — it binds the contract, not
a review — and the deterministic lane SHALL print no agreement line,
judging no contract.

#### Scenario: a recorded agreement at the judged hash passes
- **WHEN** `contract.require_agreement` is true and the task's records
  hold an `agreement` whose `contract` equals the `contract_sha256` of
  the contract the gate judges against
- **THEN** the transcript carries `PASS: agreement recorded for
  contract <hash>` naming the judged contract's short hash

#### Scenario: no recorded agreement refuses the candidate
- **WHEN** `contract.require_agreement` is true and the task carries no
  `agreement` record
- **THEN** the gate refuses the candidate with a `FAIL` line naming the
  judged contract's short hash and saying agreement is recorded with
  `agentmarshal agree`

#### Scenario: an agreement for an earlier contract text fails
- **WHEN** `contract.require_agreement` is true and the task carries an
  `agreement` record whose `contract` is not the judged contract's hash
- **THEN** the `FAIL` line says an agreement exists for another hash and
  names that record's and the judged contract's short hashes

#### Scenario: the latest agreement names the other hash
- **WHEN** the task carries `agreement` records at two hashes and none
  is the judged contract's
- **THEN** the `FAIL` line names the latest `agreement` record's hash as
  the other one

#### Scenario: any agreement carrying the hash satisfies
- **WHEN** the task carries `agreement` records at another hash and at
  the judged contract's hash
- **THEN** the check passes — the records hold an agreement whose
  `contract` equals the hash

#### Scenario: any recorder satisfies the check
- **WHEN** `contract.require_agreement` is true and the `agreement`
  record carrying the judged hash was recorded by an actor who is not a
  declared actor
- **THEN** the check passes — there are no roles over who may agree

#### Scenario: the hash compared is the contract the gate judges against
- **WHEN** `contract.require_agreement` is true, the working tree's
  `contract.md` differs from the merge-base tree's, and an `agreement`
  record carries the working-tree contract's hash
- **THEN** the check fails — the gate judges the merge-base tree's
  contract, whose hash the line names

#### Scenario: a sidecar's required agreement is judged against its own journal's contract
- **WHEN** a sidecar's project file declares `contract.require_agreement`
  true and the sidecar journal's records hold an `agreement` at the
  sidecar contract's hash
- **THEN** the advisory transcript carries the `PASS` line naming the
  hash — the host's history supplies only the diff and the commit range

#### Scenario: the check is not review-bound
- **WHEN** the gate runs with `review_required` false,
  `contract.require_agreement` true, and the task carries no `agreement`
  record
- **THEN** the agreement check still refuses the candidate

#### Scenario: the deterministic lane prints no agreement line
- **WHEN** `contract.require_agreement` is true and the candidate is a
  journal-only transaction
- **THEN** the transcript carries no agreement line — no contract is
  judged there

### Requirement: A false, absent or unreadable setting changes no transcript

When `contract.require_agreement` is absent or false — the default — the
gate SHALL print no agreement line and its transcript SHALL be the
transcript of before, byte for byte, as the pinned default fixtures
demonstrate. A setting the gate cannot read SHALL be reported on a
`WARN` line naming the unreadable key, the way the gate reports an
unreadable `changes_required` threshold: neither a refusal nor a silent
skip.

#### Scenario: an absent or false setting prints no agreement line
- **WHEN** `contract.require_agreement` is absent or false
- **THEN** the gate prints no agreement line and the run's transcript
  matches the pinned default byte for byte

#### Scenario: an unreadable setting is reported, not silently skipped
- **WHEN** `contract.require_agreement` is present but malformed
- **THEN** the transcript carries a `WARN` line naming the unreadable
  setting and the agreement check is neither passed nor refused

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
command writes the record, `status` shows who agreed and whether an
agreement is recorded for the contract's current text, and the gate
enforces a project's `require_agreement` setting as this capability's
gate requirements state.

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
