# extension-records Specification (delta)

## ADDED Requirements

### Requirement: `validate` warns "addressee not found" on an ext record whose kind no manifest declares

`agentmarshal validate` SHALL check every `ext` record's `kind` against
the `[records].kinds` the shared extensions' manifests declare in the
journal repository's working tree: the `<name>` segment of the kind
names the extension, whose manifest validate SHALL read through
`read_extension_manifest` — `.agentmarshal/extensions/<name>.toml` or
`.agentmarshal/extensions/<name>/manifest.toml`, the file form or the
directory form — and a `kind` no manifest declares SHALL draw one
`WARN` line naming the task, the record id and the kind, worded
"addressee not found" (ADR-0013 decision 18). The warning is not a
refusal — a record can outlive the manifest that declared its kind —
and SHALL NOT change validate's passed/failed verdict or its exit
status. A manifest that cannot be read SHALL be named once on a `WARN`
line of its own, however many records name the extension, and its
kinds SHALL count as undeclared; a manifest that is missing SHALL draw
no line of its own — the addressee warning is its report. A journal
holding no `ext` record SHALL read no manifest and SHALL print exactly
what validate printed before the check. Every value a record or a
manifest contributes to a warning line SHALL be escaped on display as
validate's other lines are. No other command SHALL read the warning.

#### Scenario: an ext record whose kind no manifest declares draws an addressee warning
- **WHEN** a task carries an `ext` record whose `kind` names an
  extension with no manifest in the journal repository's working tree
- **THEN** validate prints one WARN line naming the task, the record id
  and the kind, worded "addressee not found"

#### Scenario: a kind the manifest does not declare draws an addressee warning
- **WHEN** the `<name>` segment's manifest parses but its
  `[records].kinds` does not declare the record's `kind`
- **THEN** validate prints one WARN line naming the task, the record id
  and the kind, worded "addressee not found"

#### Scenario: a kind declared in the file form draws no warning
- **WHEN** the `<name>` segment's manifest lives at
  `.agentmarshal/extensions/<name>.toml` — the file form — and declares
  the record's `kind`
- **THEN** validate prints no WARN line for the record

#### Scenario: a kind declared in the directory form draws no warning
- **WHEN** `<name>`'s manifest lives at `<name>/manifest.toml` — the
  directory form — and declares the record's `kind`
- **THEN** validate prints no WARN line for the record

#### Scenario: a manifest that cannot be read is named once and declares nothing
- **WHEN** the `<name>` segment's manifest exists but cannot be read,
  and `ext` records on more than one task name the extension
- **THEN** validate names the manifest on one WARN line, prints one
  addressee warning per record — the manifest's kinds count as
  undeclared — and the verdict still passes

#### Scenario: the warning changes neither verdict nor exit status
- **WHEN** validate prints an addressee warning for an `ext` record
- **THEN** the report still passes and `agentmarshal validate` still
  exits 0

#### Scenario: a journal with no ext records reads no manifests
- **WHEN** the journal holds no `ext` record
- **THEN** validate reads no manifest and prints byte for byte what it
  printed before the check existed

#### Scenario: a value on a warning line is escaped
- **WHEN** a value a record or a manifest contributes to a warning
  carries a character that could add a line to rendered output or
  reorder it
- **THEN** the character prints as its escape and the warning stays on
  its own line

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
— on a line of its own, without opening the body. `record-ext` is the
command that writes the record — the kind checked against the declaring
manifest's `[records].kinds`, the payload leak-scanned at write, and
`validate` warns "addressee not found" on a kind no manifest declares;
no command reads the body yet — a reader of it comes with its own task.

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
