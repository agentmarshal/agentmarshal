## ADDED Requirements

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
lowercase hex characters. The field is optional; it SHALL pass the
forgeable-text rule registered for the record type and the field, and no
length bound SHALL apply to it.

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
