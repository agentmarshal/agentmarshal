# contract-governance Specification

## Purpose
What a task contract's header declares about who may implement the task,
who may review the result, and how independent the review must be — and what
that header refuses at the boundary. The header is parsed before anything it
names is trusted, so a malformed declaration is refused there with a message
naming the field, in the style of the schema-2 refusals, rather than read
loosely later.

## Requirements

### Requirement: Contract header schema 3 declares the assignment and the independence rules in force

A header with `schema = 3` MAY carry `implementers` and `reviewers`, each an
ordered list of non-empty actor ids — the order is the fallback order — and
`independence`, a list drawn from exactly `reviewer-not-writer`,
`distinct-actor`, `distinct-vendor` and `distinct-model`. Each of the three
fields is optional; absent, it SHALL parse as empty. The parsed header SHALL
expose the three fields, and a schema-3 header MAY carry every field a
schema-2 header carries. The gate SHALL read `independence` and check the
declared rules at the merge boundary as this capability's gate requirements
state; `status` SHALL read `implementers` and `reviewers` and show the
declared assignment next to what ran, as this capability's `status`
requirements state.

#### Scenario: the assignment lists keep their declared order
- **WHEN** a schema-3 header lists `implementers` as `['devin', 'codex',
  'devin-ci']` and `independence` as `['reviewer-not-writer',
  'distinct-actor', 'distinct-vendor', 'distinct-model']`
- **THEN** the parsed header's `implementers` is `('devin', 'codex',
  'devin-ci')` and its `independence` is `('reviewer-not-writer',
  'distinct-actor', 'distinct-vendor', 'distinct-model')`

#### Scenario: each field is optional
- **WHEN** a schema-3 header carries none of `implementers`, `reviewers` and
  `independence`
- **THEN** it parses, and the parsed header's three fields are empty

#### Scenario: a schema-3 header may carry the schema-2 fields
- **WHEN** a schema-3 header carries `decisions`, `documents` or
  `extensions`
- **THEN** they parse as they do under schema 2

### Requirement: A header field requires the schema that introduced it

Any of `implementers`, `reviewers` and `independence` in a header of schema
1 or 2 SHALL be refused with a message naming the field and the schema it
requires, as the schema-2 fields are refused in a schema-1 header. A schema
version the header grammar does not know SHALL be refused — schema 4 is not
a contract header schema — and headers of schema 1 and 2 SHALL parse exactly
as before.

#### Scenario: a schema-3 field in an older header is refused
- **WHEN** a header of schema 1 or 2 carries `implementers`, `reviewers` or
  `independence`
- **THEN** it is refused with a message naming the field and that it
  requires schema 3

#### Scenario: an unknown schema version is refused
- **WHEN** a header declares `schema = 4`
- **THEN** it is refused as an unknown contract header schema

#### Scenario: headers of schema 1 and 2 parse exactly as before
- **WHEN** a header of schema 1 or 2 carries no schema-3 field
- **THEN** it parses as it did before, and the parsed header's three new
  fields are empty

### Requirement: A malformed schema-3 field is refused naming the field

A schema-3 assignment field is either absent or a non-empty list of distinct
non-empty strings: an empty list SHALL be refused naming the field, as SHALL
a repeated entry, an entry that is empty or not a string, and an entry
carrying a character the record side refuses — the rule the schema-2 string
fields pass. An `independence` entry outside the fixed vocabulary SHALL be
refused naming the rule.

#### Scenario: an empty list is refused naming the field
- **WHEN** a schema-3 header carries `implementers = []`
- **THEN** it is refused with a message naming `implementers`

#### Scenario: a repeated entry is refused naming the field
- **WHEN** a schema-3 header lists the same actor id twice in `reviewers`
- **THEN** it is refused with a message naming `reviewers`

#### Scenario: an empty actor id is refused naming the field
- **WHEN** a schema-3 header lists `implementers = ['devin', '']`
- **THEN** it is refused with a message naming `implementers`

#### Scenario: an entry that is not a string is refused naming the field
- **WHEN** a schema-3 header lists `implementers = ['devin', 42]`
- **THEN** it is refused with a message naming `implementers`

#### Scenario: an entry that could forge a line is refused
- **WHEN** an entry in `implementers`, `reviewers` or `independence`
  contains a character the record side refuses
- **THEN** it is refused as containing control characters

#### Scenario: an unknown independence rule is refused naming the rule
- **WHEN** a schema-3 header lists `independence = ['distinct-actor',
  'self-reviewed']`
- **THEN** it is refused with a message naming `self-reviewed`

### Requirement: A contract hashes one way however it is read

A contract's hash SHALL be computed by one function — `contract_sha256`
in `contracts.py`, the only way any place that hashes a contract computes
it — from the contract's bytes as stored or read. The bytes SHALL decode
as UTF-8, a byte-order mark kept the way text reading keeps it; CRLF and
lone CR SHALL translate to LF the way Python's text reading translates
them; and the function SHALL return the lowercase hex sha256 of the
resulting text encoded as UTF-8. Bytes that do not decode as UTF-8 SHALL
be refused with a message naming the source the caller passed. The review
launcher SHALL compute `reviewed_contract` with it, so a contract checked
out with CRLF line endings hashes to the value the same contract with LF
hashes to, and the value the launcher records is unchanged for every
contract it reads today.

#### Scenario: a contract checked out with CRLF line endings hashes as the same contract with LF
- **WHEN** a contract's bytes carry CRLF and lone CR line endings
- **THEN** its hash equals the hash of the same contract carrying LF
  endings

#### Scenario: a byte-order mark is kept as text reading keeps it
- **WHEN** a contract's bytes open with a UTF-8 byte-order mark
- **THEN** the mark is part of the hashed text, the way
  `read_text(encoding="utf-8")` keeps it

#### Scenario: undecodable bytes are refused naming the source
- **WHEN** a contract's bytes do not decode as UTF-8
- **THEN** the hash is refused with a message naming the source the
  caller passed

#### Scenario: the launcher's reviewed_contract is unchanged
- **WHEN** `agentmarshal review` records a verdict over a contract read
  from LF, CRLF or BOM-bearing bytes
- **THEN** `reviewed_contract` is the value the launcher computed before
  this change — the sha256 of the contract text the prompt carried

### Requirement: An opened or amendment record may carry the contract's hash

From schema 7, an `opened` record and an `amendment` record MAY carry
`contract` — the sha256 of the contract text the record establishes, in
the lowercase hex `reviewed_contract` already uses — as exactly 64
lowercase hex characters. The field is optional in the record model —
records written before it existed keep validating — and it SHALL pass the
forgeable-text rule registered for the record type and the field, with no
length bound applying to it. Optional is the model's word, not the
writers': the commands that establish a contract SHALL pin its hash, as
the writers' requirement states.

#### Scenario: an opened or amendment record carrying the contract's hash is written and read back
- **WHEN** an `opened` or `amendment` record carries `contract`
- **THEN** it is written and validated, and the field reads back as given

#### Scenario: the field is optional
- **WHEN** an `opened` or `amendment` record carries no `contract`
- **THEN** it is written and validated, and the field does not appear in
  it

#### Scenario: a contract hash that is not 64 lowercase hex is refused
- **WHEN** an `opened` or `amendment` record's `contract` is not exactly
  64 lowercase hex characters
- **THEN** it is refused and nothing is written

#### Scenario: a contract that could forge a rendered line is refused
- **WHEN** an `opened` or `amendment` record's `contract` carries a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: The contract field is refused below schema 7

An `opened` or `amendment` record carrying `contract` SHALL carry schema
7: a writer carrying it stamps 7 through the minimum-schema derivation,
and the field SHALL NOT be admitted to a record stamped below 7 —
refused at write, and on read by the field-admission rule of the record's
own schema, as every schema-gated field is. A record carrying none of
the family SHALL stamp the schema it stamps without the family.

#### Scenario: a record carrying the contract field stamps schema 7
- **WHEN** an `opened` or `amendment` record is written carrying
  `contract`
- **THEN** the record carries schema 7

#### Scenario: the field on a record below schema 7 is refused at write
- **WHEN** an `opened` or `amendment` record stamped below 7 carries
  `contract`
- **THEN** it is refused and nothing is written

#### Scenario: the field on a record below schema 7 is refused on read
- **WHEN** the journal holds an `opened` or `amendment` record stamped
  below 7 that carries `contract`
- **THEN** reading the task's records refuses it as an unsupported field

#### Scenario: a record without the field keeps its schema
- **WHEN** an `opened` or `amendment` record is written carrying no
  `contract`
- **THEN** it carries the schema it carried before the family existed —
  3

### Requirement: The commands that establish a contract pin its hash

`agentmarshal open` SHALL write `contract` — the `contract_sha256` of the
contract it writes — in its `opened` record, which therefore stamps
schema 7. `agentmarshal amend` SHALL pin the `contract_sha256` of the
task's `contract.md` as it stands at that moment — in a sidecar, the
journal repository's copy — and SHALL refuse a contract that does not
parse, writing nothing. `agentmarshal migrate` SHALL pin the hash of each
contract it writes.

#### Scenario: open pins the contract it writes
- **WHEN** a task is opened
- **THEN** its `opened` record carries `contract` — the `contract_sha256`
  of the contract the open wrote — and stamps schema 7

#### Scenario: amend pins the contract as it stands
- **WHEN** a contract is amended
- **THEN** the `amendment` record's `contract` is the `contract_sha256`
  of the task's `contract.md` as it stands at that moment

#### Scenario: amend refuses a contract that does not parse
- **WHEN** `amend` runs against a task whose `contract.md` does not parse
- **THEN** it is refused and no record is written

#### Scenario: amend pins the journal repository's copy in a sidecar
- **WHEN** `amend` runs in a sidecar journal
- **THEN** the hash it pins is of the journal repository's `contract.md`

#### Scenario: migrate pins each contract it writes
- **WHEN** a v1 journal is migrated
- **THEN** each task's `opened` record carries the `contract_sha256` of
  the contract the migration wrote for it

### Requirement: `open` takes a contract already written

`agentmarshal open --contract-file <path>` SHALL take a contract already
written — header and body — validate its header as `parse_contract_text`
does, set the header's `id` to the assigned task id — naming on stderr
any different value it replaced — write it as the task's contract and pin
its hash. The `id` is rewritten where it is written as the key `id`,
`"id"` or `'id'` with a one-line string value on a line of its own in the
header's top-level table; a valid contract that writes its `id` any other
way — an escaped key, a value spanning lines — SHALL be refused with a
message naming those forms, writing nothing. `--contract-file` SHALL
refuse to be combined with `--title` or `--scope`, and SHALL refuse a
file that is missing, unreadable or not a valid contract, writing
nothing.

#### Scenario: a contract written first becomes the task's contract
- **WHEN** `open --contract-file` names a valid contract
- **THEN** it is written as the task's `contract.md` — its header's `id`
  set to the assigned task id — and the `opened` record pins its hash

#### Scenario: a different id is replaced and named on stderr
- **WHEN** the provided contract's header `id` differs from the assigned
  task id
- **THEN** it is replaced with the assigned id, which stderr names

#### Scenario: an id written any other way is refused naming the supported forms
- **WHEN** `open --contract-file` names a valid contract whose header
  writes its `id` as an escaped key or a value spanning lines
- **THEN** it is refused with a message naming the forms it rewrites —
  `id`, `"id"` or `'id'` with a one-line string value on a line of its
  own in the header's top-level table — and nothing is written

#### Scenario: --contract-file cannot combine with --title or --scope
- **WHEN** `open --contract-file` is given `--title` or `--scope`
- **THEN** it is refused and nothing is written

#### Scenario: a missing, unreadable or invalid file is refused writing nothing
- **WHEN** `open --contract-file` names a file that is missing,
  unreadable or not a valid contract
- **THEN** it is refused and nothing is written

### Requirement: `status` shows when the contract drifted from its last pin

`agentmarshal status <task>` SHALL print one line when the contract's
current hash differs from the hash in the task's latest `opened` or
`amendment` record that carries one — naming both short hashes and that
the edit should be recorded with `amend` — and SHALL print nothing when
they match or no record carries a hash. The drift SHALL NOT fail the
command.

#### Scenario: a drifted contract prints the drift line
- **WHEN** the contract's current hash differs from the task's latest
  pin
- **THEN** `status <task>` prints one line naming the pinned and the
  current short hashes and that the edit should be recorded with `amend`

#### Scenario: a contract matching its pin prints nothing
- **WHEN** the contract's hash equals the latest pin
- **THEN** `status <task>` prints no drift line

#### Scenario: a task whose records carry no hash prints nothing
- **WHEN** no `opened` or `amendment` record of the task carries
  `contract`
- **THEN** `status <task>` prints no drift line

#### Scenario: the drift never fails the command
- **WHEN** a task's contract has drifted from its last pin
- **THEN** `status <task>` still answers, printing the line

#### Scenario: the latest hash-carrying record is the pin compared
- **WHEN** an `amendment` recorded after the `opened` record carries a
  newer pin
- **THEN** the drift line compares the contract against the amendment's
  hash, not the opened record's

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

### Requirement: The gate checks the independence rules the contract declares

When the contract the gate reads — the merge-base tree's in the embedded
placement, the sidecar working tree's in the sidecar placement — declares
`independence`, the gate SHALL print one line for each declared rule other
than `reviewer-not-writer`, in the declared order, judging the latest
review of the candidate's commit against the task's implementer sessions —
the session records whose `commit` is one of the candidate's commits,
enumerated over `merge-base..candidate` as the range's writer identities
are. `distinct-vendor` SHALL compare the review's `reviewer.vendor` with
each such session's `usage.provider`; `distinct-model` the review's
`reviewer.model` with each session's `model`; and `distinct-actor` the
review's `reviewer.actor` with each session's `actor` — each side declared
in the project's actors table, a key of the project's `actors` section read
from the same trusted side the contract is read from. A comparison SHALL be
exact string equality after the normalisation the existing identity check
applies — strip and casefold — and a rule SHALL hold only when it holds
against every such session. A session whose compared value equals the
review's SHALL make the rule fail, refusing the candidate with a line
naming the rule, the review's value and the session's value, and every
value a rule line takes from a record SHALL be escaped as the gate's other
lines are.

#### Scenario: a declared rule that holds passes naming the rule
- **WHEN** a contract declares `independence = ['distinct-vendor']` and the
  latest review's `reviewer.vendor` differs from every in-range implementer
  session's `usage.provider`
- **THEN** the transcript carries a `PASS` line for `distinct-vendor`

#### Scenario: a rule failing against one session refuses the candidate
- **WHEN** a contract declares `independence = ['distinct-vendor']` and one
  in-range implementer session's `usage.provider` equals the review's
  `reviewer.vendor`
- **THEN** the gate refuses the candidate with a line naming
  `distinct-vendor`, the review's vendor and the session's vendor

#### Scenario: every in-range implementer session is judged
- **WHEN** two implementer sessions of the task carry commits in the
  candidate's range and the second's `model` equals the latest review's
  `reviewer.model`
- **THEN** `distinct-model` fails against that session though it held
  against the first

#### Scenario: a session outside the candidate's range is not judged
- **WHEN** a session of the task carries a `commit` outside
  `merge-base..candidate`
- **THEN** no declared rule compares against it

#### Scenario: the comparison is case-normalised
- **WHEN** an in-range implementer session's `model` differs from the
  latest review's `reviewer.model` only in letter case
- **THEN** `distinct-model` fails — casing does not evade the check

#### Scenario: the rule lines keep the declared order
- **WHEN** a contract declares `independence = ['distinct-model',
  'distinct-vendor']`
- **THEN** the `distinct-model` line prints before the `distinct-vendor`
  line

#### Scenario: distinct-actor compares declared actors
- **WHEN** a contract declares `distinct-actor`, and the latest review's
  `reviewer.actor` and an in-range implementer session's `actor` are both
  keys of the project's actors table
- **THEN** the rule passes where the two differ and fails where they are
  equal

#### Scenario: the review judged is the latest review of the candidate's commit
- **WHEN** the task carries more than one review of the candidate's commit
- **THEN** the declared rules judge the latest one, as the review check
  does

#### Scenario: values from records are escaped
- **WHEN** a value a rule line prints — the review's or a session's —
  carries a character that could add a line to the output or reorder it
- **THEN** it prints escaped, as the gate's other lines are

#### Scenario: a sidecar's declared rules judge its own journal's records
- **WHEN** a sidecar contract declares `distinct-actor` and the sidecar's
  project file declares the actors
- **THEN** the rule judges the sidecar journal's sessions and review — the
  host's history supplies only the diff and the commit range

### Requirement: A declared rule that cannot be judged reads not checked

Where a declared rule cannot be judged — no implementer session of the
task carries a `commit` in the candidate's range, a compared field is
absent on the review or on a session, or an actor the rule would compare
is not declared in the project's actors table — its line SHALL read
`NOT CHECKED` with the reason: neither a refusal nor a pass.

#### Scenario: no implementer session carries a commit in the range
- **WHEN** no session record of the task carries a `commit` in the
  candidate's range
- **THEN** each declared rule reads `NOT CHECKED` saying so, and the gate
  does not refuse for it

#### Scenario: a compared field absent on the review
- **WHEN** the latest review's `reviewer` object carries no `actor`
- **THEN** `distinct-actor` reads `NOT CHECKED` naming the absent field

#### Scenario: a compared field absent on a session
- **WHEN** an in-range implementer session carries no `model` or no
  `usage.provider`
- **THEN** the rule needing it reads `NOT CHECKED` naming the session and
  the absent field

#### Scenario: a session's actor is not a declared actor
- **WHEN** an in-range implementer session's `actor` is not a key of the
  project's actors table
- **THEN** `distinct-actor` reads `NOT CHECKED` saying the actor is not a
  declared actor

#### Scenario: the review's actor is not a declared actor
- **WHEN** the latest review's `reviewer.actor` is not a key of the
  project's actors table
- **THEN** `distinct-actor` reads `NOT CHECKED` saying so

#### Scenario: a failing session outranks an unjudgeable one
- **WHEN** one in-range implementer session's compared value equals the
  review's and another session's cannot be judged
- **THEN** the rule fails against the judged one — a demonstrated
  violation is reported, never softened by what could not be checked

### Requirement: Without a review the declared rules read not examined

Asked to judge without a review — `review_required` false — and the
candidate carrying no review record, the gate SHALL report each declared
rule as `NOT EXAMINED`, as the existing review-bound checks do; a
candidate that does carry a review SHALL have the rules judged however the
run was asked.

#### Scenario: the declared rules are not examined without a review
- **WHEN** the gate runs with `review_required` false and the candidate
  carries no review record
- **THEN** each declared rule's line reads `NOT EXAMINED` and none counts
  as a violation

#### Scenario: a review is judged however the run was asked
- **WHEN** the gate runs with `review_required` false and the candidate
  carries a review
- **THEN** the declared rules are judged against it as in a normal run

### Requirement: `reviewer-not-writer` is one line and the default transcript is unchanged

`reviewer-not-writer` — the existing declared-identity check — SHALL run
for every candidate exactly as before, whether or not the header names it,
and the header naming it SHALL add no second line. A contract declaring no
`independence` SHALL produce the gate transcript of before byte for byte,
as the pinned default fixtures demonstrate.

#### Scenario: the header naming reviewer-not-writer adds no second line
- **WHEN** a contract declares `independence = ['reviewer-not-writer']`
- **THEN** the transcript carries the existing identity line once and no
  rule line for it

#### Scenario: a contract without independence prints today's transcript
- **WHEN** the contract declares no `independence`
- **THEN** the transcript matches the pinned default byte for byte

### Requirement: `status` shows the contract's declared assignment in a section of its own

`agentmarshal status <task>` SHALL print an assignment section — after
the task's scope and before the record lines — when the contract header
declares any of `implementers`, `reviewers` and `independence`, and
SHALL print no assignment section otherwise: a contract declaring none
of the three leaves the detail view byte for byte unchanged. The section
SHALL name the declared `implementers` and `reviewers`, each in its
declared order — the order is the fallback order — and the declared
`independence` rules, each field on a line of its own; the
`independence` line SHALL add `reviewer-not-writer` as always checked
by the gate when the header does not name it — the rule runs for every
candidate whether or not the header names it — so the line states the
rules in force, not only the rules declared. The section SHALL then
show what ran: the implementer-session lines in the order the records
stand, then the review lines in the order the records stand, as the
following requirements state — and an empty ran side SHALL say so the
way the scope section prints `(none)` for an empty scope: when the
contract declares `implementers` and no implementer session is
recorded, the section SHALL print `- implementer sessions: (none)`
where the implementer-session lines would stand, and when the contract
declares `reviewers` and no review is recorded, `- reviews: (none)`
where the review lines would stand. A ran side whose list the header
does not declare SHALL print no `(none)` line — `(not declared)`
already states that side has no assignment. A field the header does not
declare SHALL be shown as not declared rather than omitted (ADR-0018
decision 3).

#### Scenario: a contract declaring all three prints the section
- **WHEN** the contract header declares `implementers`, `reviewers` and
  `independence`
- **THEN** `status <task>` prints an assignment section naming the three
  lists — implementers and reviewers in their declared order — after the
  scope and before the record lines

#### Scenario: an undeclared field is shown as not declared
- **WHEN** the contract header declares `implementers` but neither
  `reviewers` nor `independence`
- **THEN** the section names the declared implementers, shows
  `reviewers` as not declared, and the `independence` line shows the
  field as not declared and names `reviewer-not-writer` as always
  checked by the gate

#### Scenario: reviewer-not-writer the header does not name is named as always checked
- **WHEN** the contract header declares `independence` without
  `reviewer-not-writer`
- **THEN** the `independence` line names the declared rules and adds
  `reviewer-not-writer (always checked by the gate)`

#### Scenario: sessions group before reviews whatever the record order
- **WHEN** the task's records stand with a review before an implementer
  session
- **THEN** the section prints the implementer-session lines first and
  the review lines after, each in the order the records stand

#### Scenario: a contract declaring none prints today's view byte for byte
- **WHEN** the contract header declares none of the three fields
- **THEN** `status <task>` prints no assignment section, and the detail
  view is byte for byte what it was

#### Scenario: a declared implementers list with no session recorded says none
- **WHEN** the contract header declares `implementers` and the task
  carries no implementer session
- **THEN** the section prints `- implementer sessions: (none)` where the
  implementer-session lines would stand

#### Scenario: a declared reviewers list with no review recorded says none
- **WHEN** the contract header declares `implementers` and `reviewers`,
  an implementer session is recorded and no review is recorded
- **THEN** the section prints `- reviews: (none)` where the review lines
  would stand, after the implementer-session lines

#### Scenario: a side with no declared list prints no (none) line
- **WHEN** the contract header declares `independence` alone and the
  task carries neither an implementer session nor a review
- **THEN** the section ends at the declaration lines — neither ran side
  prints a `(none)` line, `(not declared)` already stating the absence

### Requirement: `status` shows which implementer sessions ran

For each implementer session — a session record of the task whose `role`
is `implementer` — the assignment section SHALL print one line naming
the record's id and showing the session's `actor`, the vendor read from
`usage.provider`, the session's `model`, and `fallback_reason` when the
record carries one. An absent value SHALL be shown as absent, never
derived from another field: the vendor comes from `usage.provider`
alone, never guessed from the actor or the model. A session whose
`actor` is not in the declared `implementers` SHALL be marked as not
declared for the role — shown, not refused (ADR-0018 decision 3). The
mark SHALL appear only when the contract declares `implementers`; a
session carrying no actor shows the absent value and no mark. A session
of another `role` prints no implementer-session line.

#### Scenario: an implementer session's line shows what ran
- **WHEN** a task carries an implementer session — a session record
  whose `role` is `implementer`
- **THEN** its assignment-section line names the record's id and shows
  the session's `actor`, the vendor from `usage.provider`, its `model`
  and its `fallback_reason`

#### Scenario: the vendor is read from usage.provider alone
- **WHEN** an implementer session carries no `usage` and its `actor`
  reads like `openai/gpt-5`
- **THEN** the line shows the vendor as absent, never guessed from the
  actor string

#### Scenario: an absent value is shown as absent
- **WHEN** an implementer session carries no `model` or no `actor`
- **THEN** the line shows the absent value as absent

#### Scenario: fallback_reason prints only when the record carries it
- **WHEN** one implementer session carries `fallback_reason` and another
  does not
- **THEN** the first session's line shows it and the second's shows no
  `fallback_reason`

#### Scenario: an actor not in the declared list is marked
- **WHEN** the contract declares `implementers` and an implementer
  session's `actor` is not in the list
- **THEN** the line shows the actor and marks it as not declared for the
  role — shown, not refused

#### Scenario: an actor in the declared list carries no mark
- **WHEN** the contract declares `implementers` and an implementer
  session's `actor` is in the list
- **THEN** the line carries no not-declared mark

#### Scenario: the mark appears only when implementers is declared
- **WHEN** the contract declares no `implementers` and an implementer
  session runs
- **THEN** the line shows the session's actor with no not-declared mark

#### Scenario: a session of another role prints no implementer-session line
- **WHEN** the task carries a session record whose `role` is not
  `implementer`
- **THEN** the section prints no implementer-session line for it

### Requirement: `status` shows which reviews ran

For each review record of the task the assignment section SHALL print
one line naming the record's id and showing its reviewer's `actor`,
`vendor` and `model`, an absent value shown as absent. A review whose
`reviewer.actor` is not in the declared `reviewers` SHALL be marked as
not declared for the role — shown, not refused (ADR-0018 decision 3).
The mark SHALL appear only when the contract declares `reviewers`; a
review carrying no `reviewer.actor` shows the absent value and no mark.

#### Scenario: a review's line shows what ran
- **WHEN** a task carries a review record
- **THEN** its assignment-section line names the record's id and shows
  the reviewer's `actor`, `vendor` and `model`

#### Scenario: an absent reviewer value is shown as absent
- **WHEN** a review's `reviewer` object carries no `actor`
- **THEN** the line shows the absent value and no not-declared mark

#### Scenario: a reviewer actor not in the declared list is marked
- **WHEN** the contract declares `reviewers` and a review's
  `reviewer.actor` is not in the list
- **THEN** the line shows the actor and marks it as not declared for the
  role

#### Scenario: the mark appears only when reviewers is declared
- **WHEN** the contract declares no `reviewers` and a review runs
- **THEN** the line shows the reviewer's `actor` with no not-declared
  mark

### Requirement: the assignment section's values are escaped on display

Every value the assignment section takes from a contract or a record
SHALL be escaped on display as the record lines' values are: each
refused character prints as its escape and the line stays one line.
Nothing else `status` prints SHALL change — the record lines, the
agreement line, the drift line, the overdue-step and path lines — and no
other command changes.

#### Scenario: a value that could forge a line prints escaped
- **WHEN** a value the section prints — a declared list entry, a
  session's or a review's field — carries a character that could add a
  line to rendered output or reorder it
- **THEN** each refused character prints as its escape and the line
  stays on its own line
