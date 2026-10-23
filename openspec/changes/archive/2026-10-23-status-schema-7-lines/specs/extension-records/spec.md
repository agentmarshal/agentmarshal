## ADDED Requirements

### Requirement: `status` shows an ext record on a line of its own

`agentmarshal status <task>` SHALL print one line per `ext` record —
after the record's id, type and time: the `kind`, the commit's short
form and the payload hash's short form — and SHALL name the recorder. A
recorder that is not a declared actor SHALL be shown as not a declared
actor (ADR-0022 section 3). The record's `payload` SHALL NOT be shown —
it is opaque to the core; the line names its hash only. Every value
taken from the record SHALL be escaped on display as the other record
lines' values are.

#### Scenario: status shows an ext record's line
- **WHEN** `agentmarshal status <task>` lists an `ext` record
- **THEN** its line carries `kind`, the commit's short form,
  `payload_sha256`'s short form and `recorded_by`, and none of the
  payload's text

#### Scenario: a recorder that is not a declared actor is shown as such
- **WHEN** `agentmarshal status <task>` lists an `ext` record whose
  `recorded_by` is not a declared actor
- **THEN** the line names the recorder and says it is not a declared
  actor

#### Scenario: an ext record's values stay on their own line
- **WHEN** `agentmarshal status <task>` lists an `ext` record whose
  `kind`, `commit`, `payload_sha256` or `recorded_by` carries a
  character that could add a line to rendered output or reorder it — a
  value an older schema's journal can hold where today's read rules do
  not reach
- **THEN** each refused character prints as its escape and the record
  stays on the one line

## MODIFIED Requirements

### Requirement: An ext record carries an extension's result pinned by hash

From schema 7 the journal admits an `ext` record (ADR-0013 decision 18,
ADR-0022 section 3). The record SHALL carry `kind` — of the form
`<name>/<kind>@<version>` extension manifests declare kinds in, by the
manifest's own rule — `commit` — exactly 40 lowercase hex characters,
required — `payload` — any JSON value — and `payload_sha256` — exactly
64 lowercase hex characters equal to the sha256 of the payload's
canonical form. The payload's canonical form SHALL be its JSON
serialization with sorted keys, no insignificant whitespace (separators
`,` and `:`), non-ASCII characters unescaped, encoded as UTF-8, and that
form SHALL be at most 64 KiB (ADR-0022 section 8); a payload that has no
JSON form SHALL be refused. Every refusal SHALL name the field at fault.
The record SHALL name its recorder in `recorded_by` with
`recorded_by_source`, as `check`, `agreement` and `acknowledgement` do;
a recorder that is not a declared actor is accepted. The record SHALL
project to no task state and SHALL NOT be admitted after a terminal
record — post-gate results go to the process log. `status` shows the
record's envelope — `kind`, `commit`, `payload_sha256` and the recorder
— on a line of its own, without opening the body. No command reads the
body yet — the `record-ext` command, the leak scan of the payload at
write, `validate`'s "addressee not found" warning, checking that a kind
is declared by a manifest, and any reader of the body come with their
own tasks.

#### Scenario: an ext record is written and read back
- **WHEN** an `ext` record carries `kind`, `commit`, `payload` and
  `payload_sha256`
- **THEN** it is written and validated, and the fields read back as given

#### Scenario: a kind not of the manifest's form is refused
- **WHEN** an `ext` record's `kind` is missing, not a string, or not of
  the form `<name>/<kind>@<version>`
- **THEN** it is refused and nothing is written

#### Scenario: a kind that could forge a rendered line is refused
- **WHEN** an `ext` record's `kind` carries a character that could add a
  line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: a commit that is not 40 lowercase hex is refused
- **WHEN** an `ext` record's `commit` is missing, not a string, or not
  exactly 40 lowercase hex characters
- **THEN** it is refused and nothing is written

#### Scenario: an ext record that carries no payload is refused
- **WHEN** an `ext` record carries no `payload`
- **THEN** it is refused and nothing is written

#### Scenario: a payload at the byte bound is admitted and one past it is refused
- **WHEN** an `ext` record's `payload` encodes, canonically, to exactly
  64 KiB, or to one byte more
- **THEN** the first is admitted, the second is refused and nothing is
  written

#### Scenario: a payload that has no JSON form is refused
- **WHEN** an `ext` record's `payload` carries a non-finite number or
  another value JSON cannot encode
- **THEN** it is refused and nothing is written

#### Scenario: a payload hash that is not 64 lowercase hex is refused
- **WHEN** an `ext` record's `payload_sha256` is missing, not a string,
  or not exactly 64 lowercase hex characters
- **THEN** it is refused and nothing is written

#### Scenario: a payload hash that does not match the payload is refused
- **WHEN** an `ext` record's `payload_sha256` is not the sha256 of the
  payload's canonical form
- **THEN** it is refused and nothing is written

#### Scenario: the same payload under another key order hashes the same
- **WHEN** two `ext` records carry equal payloads whose object keys
  differ in order
- **THEN** their `payload_sha256` is the same

#### Scenario: an ext record that names no recorder is refused
- **WHEN** an `ext` record carries neither `recorded_by` nor
  `recorded_by_source`
- **THEN** it is refused

#### Scenario: a recorder that is not a declared actor is accepted
- **WHEN** an `ext` record names a recorder that is not a declared actor
- **THEN** it is written, and `recorded_by` carries the name as given

#### Scenario: a candidate adding an ext record is admitted
- **WHEN** a candidate adds an `ext` record to an open task
- **THEN** the record check the gate runs admits it, as it admits the
  other schema-7 record types the projection admits before a terminal
  record

#### Scenario: an ext record on a closed task is refused
- **WHEN** an `ext` record is written for a task that has completed or
  been abandoned
- **THEN** no record is written, the refusal names the state, and the
  journal still validates

#### Scenario: status and validate handle a task carrying an ext record
- **WHEN** a task carries an `ext` record
- **THEN** `agentmarshal status` and `agentmarshal validate` answer
  without failing
