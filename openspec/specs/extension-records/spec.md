# extension-records Specification

## Purpose
The journal carries an extension's result as a shared `ext` record
(ADR-0013 decision 18): the core knows the envelope — the task, who,
when, the commit, `schema`, `tool_version`; the `kind` carries a
namespace and a version and is declared in the extension's manifest; the
body is opaque to the core — hash-pinned and size-limited, its meaning
for the extension itself to check.

## Requirements

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

### Requirement: An ext record is a record of schema 7

An `ext` record SHALL carry schema 7 — the schema the record type was
introduced under. An `ext` record stamped below 7 SHALL be refused at
write, and on read: the field-admission rule of the record's own schema
admits `kind`, `commit`, `payload` and `payload_sha256` only from 7, and
the record-type gate refuses the type below its schema whatever the
record carries. A writer SHALL stamp 7 through the minimum-schema
derivation — the record type itself needs it.

#### Scenario: an ext record stamps schema 7
- **WHEN** an `ext` record is built
- **THEN** it carries schema 7

#### Scenario: an ext record stamped below 7 is refused at write
- **WHEN** an `ext` record stamped below 7 is presented for write
- **THEN** it is refused and nothing is written

#### Scenario: an ext record stamped below 7 is refused on read
- **WHEN** the journal holds an `ext` record stamped below 7
- **THEN** reading the task's records refuses it

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

### Requirement: `record-ext` writes an ext record for a resolved commit

`agentmarshal record-ext --task <id> --commit <rev> --kind
<name>/<kind>@<version> --payload-file <path>` SHALL write one `ext`
record through `create_ext_record` — the task the record binds, the
kind, the commit resolved to its full 40-hex id and the payload with
the `payload_sha256` the builder computes over its canonical form —
and SHALL print the record's path, the resolved commit, the kind and
the recorder. The commit SHALL be resolved — `git rev-parse --verify
<rev>^{commit}` — in the journal's repository: the repository that
holds the journal in either placement, so a sidecar records against
the commits its own repository carries and the host's are never asked.
A reference that does not resolve to a commit there SHALL be refused
naming it, writing nothing. The task SHALL be one an `ext` record may
be written for: an unknown task SHALL be refused naming it, and a
completed or abandoned task SHALL be refused naming its state — the
record type is admitted after no terminal record — in each case
writing nothing.

#### Scenario: an ext record is written for a declared kind at the resolved commit
- **WHEN** `record-ext` runs on an open task with `--commit` naming a
  commit the journal's repository holds, `--kind` a kind the shared
  extension's manifest declares and `--payload-file` a file holding
  JSON
- **THEN** one `ext` record is written at schema 7 carrying the kind,
  the full 40-hex commit id, the payload and the sha256 of its
  canonical form, and the output prints the record's path, the
  resolved commit, the kind and the recorder

#### Scenario: a short or symbolic commit resolves to the full id
- **WHEN** `--commit` names a reference that is not 40 hex — a short
  id, a branch, `HEAD`
- **THEN** the record's `commit` is the full 40-hex id the reference
  resolves to in the journal's repository

#### Scenario: a commit that does not resolve is refused writing nothing
- **WHEN** `--commit` names a reference the journal's repository does
  not hold
- **THEN** it is refused naming the reference, and no record is
  written

#### Scenario: an unknown task is refused writing nothing
- **WHEN** `record-ext` names a task the journal does not carry
- **THEN** it is refused naming the task, and no record is written

#### Scenario: a completed or abandoned task is refused writing nothing
- **WHEN** `record-ext` runs on a task that has completed or been
  abandoned
- **THEN** it is refused naming the state, and no record is written

#### Scenario: in a sidecar the commit resolves in the journal repository
- **WHEN** `record-ext` runs in a project whose journal is a sidecar
  and `--commit` names a commit the sidecar's repository carries
- **THEN** the record lands in the sidecar's journal carrying the full
  id, and the host's repository is never asked

### Requirement: `record-ext` writes only a kind the shared extension's manifest declares

Only a shared extension writes `ext`, and only through the core's
command (ADR-0013 decision 18): the `<name>` segment of `--kind`
SHALL name the extension, whose manifest the command SHALL read from
the journal repository's working tree through
`read_extension_manifest` — `.agentmarshal/extensions/<name>.toml`
or `.agentmarshal/extensions/<name>/manifest.toml`, the file form or
the directory form — and the command SHALL write only when the
manifest's `[records].kinds` declares the kind exactly as given. A
`--kind` not of the `<name>/<kind>@<version>` form SHALL be refused
naming it; a kind no shared extension declares — the manifest
missing, or the kind absent from its `kinds` — SHALL be refused
naming the kind; and a manifest that cannot be read SHALL refuse the
write, the refusal naming the kind. Each refusal writes nothing.

#### Scenario: a kind not of the declared form is refused
- **WHEN** `--kind` is not of the form `<name>/<kind>@<version>`
- **THEN** it is refused naming it, and no record is written

#### Scenario: a kind whose extension has no manifest is refused naming the kind
- **WHEN** the `<name>` segment of `--kind` has no manifest in either
  form in the journal repository's working tree
- **THEN** the write is refused naming the kind, and no record is
  written

#### Scenario: a kind absent from the manifest's kinds is refused naming it
- **WHEN** the `<name>` segment's manifest parses but its
  `[records].kinds` does not declare `--kind`
- **THEN** the write is refused naming the kind, and no record is
  written

#### Scenario: a manifest that cannot be read refuses the write naming the kind
- **WHEN** the `<name>` segment's manifest exists but is malformed
- **THEN** the write is refused naming the kind, and no record is
  written

#### Scenario: a kind declared in the directory form is written
- **WHEN** `<name>`'s manifest lives at `<name>/manifest.toml` — the
  directory form — and declares the kind
- **THEN** the record is written carrying the kind

### Requirement: the payload is leak-scanned at write, masked where it trips

`--payload-file` SHALL be read and parsed as JSON: a file that cannot
be read and a file that does not parse as JSON SHALL each be refused
naming it, writing nothing. Every string in the parsed payload —
every string value and every object key, at any depth — SHALL be
masked through `mask_leaks` with the project's configured private
markers: each matched span SHALL be replaced by `[masked:
<category>]` — a configured marker by `[masked: private-marker]`, a
built-in signature by the signature's own name — and the command
SHALL name the matched categories on stderr, never the matched text
and never a marker's value. The record SHALL carry the masked
payload, and `payload_sha256` SHALL pin the masked payload's
canonical form — the hash covers what the record carries, never the
file as given. Two object keys that mask to one SHALL be refused,
writing nothing — the collapse would silently drop a member. A
payload whose masked canonical form still trips the scan — a marker
occurring in the mask label itself, or spanning a boundary no single
string holds — SHALL be refused naming the categories, writing
nothing; a payload whose masked canonical form exceeds 64 KiB SHALL
be refused, writing nothing.

#### Scenario: a hit in a string value is masked and its category named
- **WHEN** a string value in the payload trips a built-in signature
- **THEN** the record's payload carries `[masked: <category>]` in
  place of the span, the command names the category on stderr, and
  the matched text appears nowhere — not in the output, not in the
  record

#### Scenario: a hit in an object key is masked
- **WHEN** an object key in the payload trips the scan
- **THEN** the record's payload carries the masked key, and the
  matched text appears nowhere in the record

#### Scenario: the payload hash is computed after masking
- **WHEN** a payload carries a string the scan masks
- **THEN** the record's `payload_sha256` is the sha256 of the masked
  payload's canonical form — of what the record carries, not of the
  file as given

#### Scenario: two keys that mask to one are refused
- **WHEN** masking would make two of a payload object's keys equal
- **THEN** the write is refused and no record is written — a merged
  key would silently drop a member

#### Scenario: a payload whose masked form still trips the scan is refused
- **WHEN** the masked payload's canonical form still trips the scan —
  a marker occurring in the mask label itself, or spanning a boundary
  no single string holds
- **THEN** the write is refused naming the categories — never the
  matched text — and no record is written

#### Scenario: a payload file that cannot be read or parsed is refused
- **WHEN** `--payload-file` names a file that cannot be read, or one
  whose content does not parse as JSON
- **THEN** it is refused naming the file, and no record is written

#### Scenario: a payload past 64 KiB after masking is refused
- **WHEN** the masked payload's canonical form exceeds 64 KiB
- **THEN** the write is refused, and no record is written

### Requirement: `record-ext` names its recorder or writes nothing

`record-ext` SHALL resolve its recorder as `resolve_recorded_by`
resolves — the environment override, the project actors table, the
git identity — and SHALL refuse clearly when none resolves, before
anything is created. A recorder who is not a declared actor SHALL be
accepted, the record written naming the recorder and its source, and
stderr SHALL say the recorder is not a declared actor. The recorder
SHALL be escaped where it could forge a rendered line.

#### Scenario: no resolvable recorder is refused writing nothing
- **WHEN** `record-ext` can resolve no recorder — no override, no
  actors-table match, no git identity
- **THEN** it is refused naming the reason, and the records directory
  is untouched

#### Scenario: a recorder who is not a declared actor is accepted and named
- **WHEN** `record-ext`'s recorder is not a declared actor
- **THEN** the record is written with `recorded_by` and
  `recorded_by_source` as resolved, and stderr notes the recorder is
  not a declared actor

#### Scenario: a declared actor records with no undeclared note
- **WHEN** `record-ext`'s recorder names a declared actor — whether
  resolved through the actors table or named by the override
- **THEN** the record is written and no undeclared-actor note is
  printed

#### Scenario: the recorder is escaped where it could forge a line
- **WHEN** the recorder's name carries a character that could add a
  line to rendered output or reorder it
- **THEN** the output prints the escaped form, in the recorder line
  and the note alike

### Requirement: a refusal writes nothing

Every refusal the command can foresee — an unknown or terminal task,
a commit that does not resolve, a kind not of the declared form or
declared by no shared extension, a manifest that cannot be read, an
unreadable or non-JSON payload file, a payload that stays unclean or
too large after masking, a value the record rules refuse, no
resolvable recorder, a project file that cannot be read — SHALL be
decided before any write, so a refused run writes no record, and the
journal still validates.

#### Scenario: a refused run leaves the journal untouched
- **WHEN** `record-ext` is refused for any reason it can foresee
- **THEN** the journal is byte-identical and `agentmarshal validate`
  still passes

#### Scenario: a value the record rules refuse writes nothing
- **WHEN** the payload file parses as JSON only under a lenient read —
  a non-finite number — so the canonical form the record rules require
  does not exist
- **THEN** the command is refused, and no record is written

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
