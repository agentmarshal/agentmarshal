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
schema-2 header carries.

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
