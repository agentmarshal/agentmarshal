## ADDED Requirements

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

## MODIFIED Requirements

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
