# review-evidence Specification

## Purpose
What a review record may carry beyond its verdict and finding ids: the
reviewer's prose, kept verbatim as a file under the task's journal directory
and pinned by sha256 on the record — evidence a reader can open, held to the
same immutability as the record that cites it. Keeping prose is a capability
of both review paths, never an obligation of a journal.

## Requirements

### Requirement: A review may carry the reviewer's prose as a pinned artifact
A review record MAY carry `artifacts`: a list of `{ref, hash}` where `ref` is
a path relative to the project root under
`.agentmarshal/journal/tasks/<task>/artifacts/` and `hash` is the sha256 of
that file's bytes. When a review path keeps prose in the journal, it SHALL keep
the reviewer's output as received, unedited, and SHALL write the file before
the record that pins it. Once the prose is pinned, the review path SHALL keep
no other copy of it outside the journal.

#### Scenario: the model review path keeps its output
- **WHEN** `agentmarshal review` receives reviewer output that yields a valid
  verdict, and the capture level for reviews is `commit`
- **THEN** the launcher writes that output to
  `.agentmarshal/journal/tasks/<task>/artifacts/<review-record-id>-review.md`
  and the review record it writes carries one artifact pinning that file

#### Scenario: an accepted verdict keeps no copy outside the journal
- **WHEN** `agentmarshal review` has pinned the reviewer's output
- **THEN** it writes no copy of that output anywhere else, and tells the
  operator the artifact's path and nothing about a temporary file

#### Scenario: the human review path attaches prose
- **WHEN** `agentmarshal submit-review` is given `--prose <file>` and the
  capture level for reviews is `commit`
- **THEN** the file's bytes are copied to the same location and pinned on the
  record; without `--prose` the record carries no `artifacts`, as before

#### Scenario: a rejected verdict still keeps the prose
- **WHEN** reviewer output fails verdict validation
- **THEN** the output is kept where the operator can read it, as before, at
  every capture level, and no review record is written

### Requirement: Review artifacts are evidence and follow the record rule
A review artifact, once written, MUST NOT be modified or deleted.

#### Scenario: the gate refuses a modified artifact
- **WHEN** a candidate modifies or deletes a file under
  `.agentmarshal/journal/tasks/<task>/artifacts/`
- **THEN** the gate reports it in the append-only check and refuses the
  candidate, as it does for a record

#### Scenario: the artifact's hash is checked where its record is validated
- **WHEN** `agentmarshal validate` reads a review record carrying `artifacts`
- **THEN** it refuses a journal whose artifact file is missing or whose bytes
  do not match the pinned hash

### Requirement: The prose is visible where the record is
`status` SHALL show, on the line of a review record that carries `artifacts`,
how many it carries; `report`, which has no per-record line, SHALL show on the
task's line the total over the task's review records.

#### Scenario: status names the prose
- **WHEN** `agentmarshal status <task>` lists a review record that carries `artifacts`
- **THEN** the review line says how many artifacts it carries

#### Scenario: report totals the prose
- **WHEN** `agentmarshal report --task <task>` reports a task whose review
  records carry artifacts
- **THEN** the task's line shows the sum over those records

### Requirement: Nothing is required of a journal that keeps no prose
A review record without `artifacts` SHALL be read, gated and displayed as
before this capability existed; keeping prose is a capability, not an
obligation.

#### Scenario: an old journal reads as before
- **WHEN** a review record carries no `artifacts`
- **THEN** every command behaves as it did before this capability existed, and
  the gate's transcript for such a candidate is byte-for-byte the transcript
  the committed fixtures pin for a default run

### Requirement: A refused record leaves no artifact behind
A review path SHALL refuse a record for every reason the record writer can
check before writing — its shape, its finding binding, its task, the
recorder's identity — before the record's artifact is written, and SHALL do
so through the same checks the writer applies, stated once.

#### Scenario: a binding to an unknown finding writes nothing
- **WHEN** `submit-review --reviewed-finding <id> --prose <file>` names a
  finding the task does not have
- **THEN** the command refuses, and no file appears under the task's
  artifacts directory

#### Scenario: a refusal the writer cannot foresee is named as a limit
- **WHEN** the record write itself fails after the artifact is written (a
  filesystem error, an id collision)
- **THEN** the command reports the failure and names the artifact it left,
  so the operator can decide what to do with it

### Requirement: Artifact paths follow the record collision rule
The gate SHALL refuse a candidate that adds a path under
`.agentmarshal/journal/tasks/<task>/artifacts/` which already exists in the
base tree, as it refuses such a record path.

#### Scenario: two candidates add the same artifact path
- **WHEN** a candidate adds an artifact path that the base tree already holds
- **THEN** the gate reports the collision and refuses the candidate

### Requirement: A review record may name the contract it judged
A review record MAY carry `reviewed_contract`: the sha256, in lowercase hex, of
the contract text the reviewer was handed. A record carrying it SHALL declare a
schema that allows it; a record without it SHALL be valid under the schema it
declares, and its absence SHALL never be reported anywhere.

#### Scenario: the launcher records the contract it handed over
- **WHEN** `agentmarshal review` records a verdict
- **THEN** the review record carries `reviewed_contract`, the sha256 of the
  exact contract bytes the prompt carried

#### Scenario: the human path records no contract
- **WHEN** `agentmarshal submit-review` records a verdict
- **THEN** the record carries no `reviewed_contract`, because no contract was
  handed to anyone, and the record is valid without it

#### Scenario: the field requires the schema that allows it
- **WHEN** a record carrying `reviewed_contract` declares a schema written
  before the field existed
- **THEN** the record is refused, with a message naming the field and the schema
  it requires

#### Scenario: records written before the field are read as they were
- **WHEN** a journal holds review records written under earlier schemas
- **THEN** every command reads them as it did before this change

### Requirement: The capture policy decides where a review's prose goes
Both review paths SHALL take the level for a review's prose from the capture
policy's `reviews` class, read from the project file of the journal being
written. A project file with no `capture` section SHALL resolve to the default
preset, which puts reviews at `hash`. Only `commit` SHALL put a review's prose
in the journal. At `hash` the reviewer's output SHALL be kept byte for byte in
a file under the local state's process-log area of the repository that holds
the journal, a `review-prose` event carrying the task, the file's path and its
sha256 SHALL be appended to the process log, and the journal SHALL hold
nothing about the prose — no artifact, no field. When the local state cannot
be used — git cannot name it or its directory cannot be created — the output
SHALL be kept in a local temporary file instead, and stderr SHALL say why.

#### Scenario: by default the prose stays out of the journal
- **WHEN** `agentmarshal review` records a verdict in a project whose file has
  no `capture` section
- **THEN** nothing is written under the task's artifacts directory, the record
  carries no `artifacts`, the reviewer's output is kept byte for byte in a
  file under the clone's local state, a `review-prose` event carrying the
  task, the file's path and its sha256 is appended to the process log, and
  the command names the path on stderr

#### Scenario: commit keeps today's behaviour
- **WHEN** the capture level for reviews is `commit`
- **THEN** `agentmarshal review` pins the output as a journal artifact and
  prints `reviewer prose pinned: <ref>` on stderr, as before this change

#### Scenario: off keeps nothing
- **WHEN** `agentmarshal review` records a verdict and the capture level for
  reviews is `off`
- **THEN** nothing is written under the task's artifacts directory, no
  temporary copy of the output is made, the record carries no `artifacts`, and
  stderr says the prose was not kept

#### Scenario: local state that cannot be used falls back to a temporary file
- **WHEN** `agentmarshal review` records a verdict at capture level `hash`
  and the clone's local state cannot be used — git cannot name it or its
  directory cannot be created
- **THEN** the reviewer's output is kept in a local temporary file as before
  this change, and stderr says why the local state could not be used

#### Scenario: a sidecar keeps the prose in the journal repository's local state
- **WHEN** `agentmarshal review` records a verdict at capture level `hash`
  in a sidecar placement
- **THEN** the prose file and the `review-prose` event land in the sidecar
  repository's local state, and the host's local state is untouched

#### Scenario: the human path refuses prose it may not keep
- **WHEN** `agentmarshal submit-review --prose <file>` is run and the capture
  level for reviews is not `commit`
- **THEN** the command refuses before writing anything, and its message names
  the level and the setting that permits keeping prose

#### Scenario: a malformed capture section costs no reviewer run
- **WHEN** the project file's `capture` section is malformed
- **THEN** `agentmarshal review` refuses with the parser's message before it
  launches the reviewer command, and writes nothing

### Requirement: A check record carries what a pipeline check found on a commit
From schema 7 the journal admits a `check` record: a trace of what a
pipeline check found on a commit, written by whoever observed the run —
a measurement that projects to no task state and that the gate decides
nothing from. The record SHALL carry `commit` — exactly 40 lowercase hex
characters; `name` — a non-empty string naming the check; and `result` —
one of `passed`, `failed`, `error` or `skipped`. It MAY carry
`failed_step`, `excerpt` and `run_url`, each a non-empty string when
present. `excerpt` SHALL be bounded at 4 KiB of UTF-8 by the byte-bounded
text rule — refused beyond, never truncated by the record layer — and
`name`, `failed_step`, `excerpt` and `run_url` SHALL pass the
forgeable-text rule registered for this record type and field. A `check`
record SHALL name its recorder in `recorded_by` with
`recorded_by_source`, as `finding` already does.

#### Scenario: a check record is written and read back
- **WHEN** a `check` record carries `commit`, `name`, `result` and all
  three optional fields
- **THEN** it is written and validated, and each field reads back as given

#### Scenario: the optional fields may be absent
- **WHEN** a `check` record carries only the required fields
- **THEN** it is written and validated, and none of `failed_step`,
  `excerpt` or `run_url` appears in it

#### Scenario: a commit that is not 40 lowercase hex is refused
- **WHEN** a `check` record's `commit` is missing, not a string, or not
  exactly 40 lowercase hex characters
- **THEN** it is refused and nothing is written

#### Scenario: a name that is missing or empty is refused
- **WHEN** a `check` record's `name` is missing, empty, all whitespace
  or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a result outside the outcome vocabulary is refused
- **WHEN** a `check` record's `result` is missing, not a string, or not
  one of `passed`, `failed`, `error` or `skipped`
- **THEN** it is refused and nothing is written

#### Scenario: an optional field that is empty is refused
- **WHEN** a `check` record's `failed_step`, `excerpt` or `run_url` is
  present but empty, all whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: an excerpt beyond the byte bound is refused
- **WHEN** a `check` record's `excerpt` encodes to more than 4 KiB of
  UTF-8
- **THEN** it is refused and nothing is written

#### Scenario: a displayed string that could forge a line is refused
- **WHEN** a `check` record's `name`, `failed_step`, `excerpt` or
  `run_url` carries a character that could add a line to rendered output
  or reorder it
- **THEN** the record is refused

#### Scenario: a check record that names no recorder is refused
- **WHEN** a `check` record carries neither `recorded_by` nor
  `recorded_by_source`
- **THEN** it is refused

### Requirement: A check record is a record of schema 7
A `check` record SHALL carry schema 7 — the schema the record type was
introduced under. A `check` record stamped below 7 SHALL be refused at
write, and on read: the field-admission rule of the record's own schema
admits the family's fields only from 7, and the record-type gate refuses
the type below its schema whatever the record carries. A writer SHALL
stamp 7 through the minimum-schema derivation — the record type itself
needs it.

#### Scenario: a check record stamps schema 7
- **WHEN** a `check` record is built
- **THEN** it carries schema 7

#### Scenario: a check record stamped below 7 is refused at write
- **WHEN** a `check` record stamped below 7 is presented for write
- **THEN** it is refused and nothing is written

#### Scenario: a check record stamped below 7 is refused on read
- **WHEN** the journal holds a `check` record stamped below 7
- **THEN** reading the task's records refuses it

### Requirement: A review may name the task's previous review
From schema 7 a review record MAY carry `previous_review` — the id of
the task's previous review (ADR-0016 decision 2), a record id in the
form record ids take: a 26-character Crockford base32 ULID. The field
SHALL pass the forgeable-text rule registered for the review record
type and field. Nothing resolves the id against the journal at the
record layer — what it points at is the writer's.

#### Scenario: a review carrying previous_review is written and read back
- **WHEN** a review record carries `previous_review` naming a record id
- **THEN** it is written and validated, and the field reads back as given

#### Scenario: a previous_review that is not a record id is refused
- **WHEN** a review record's `previous_review` is not a string in the
  form record ids take, or not a string at all
- **THEN** it is refused and nothing is written

#### Scenario: a previous_review that could forge a line is refused
- **WHEN** a review record's `previous_review` carries a character that
  could add a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: A review may carry a class for each of its findings
From schema 7 a review record MAY carry `classes` — an object whose
every key is a finding id the same record names in `findings` or
`advisory_findings` and whose every value is a non-empty string, the
finding's class (ADR-0016 decision 3). Each class value SHALL pass the
forgeable-text rule. A class outside the project's vocabulary SHALL NOT
be refused by the record — recording it as `other` is the writer's. An
empty `classes` object SHALL be refused: a review with nothing
classified carries no `classes`.

#### Scenario: a review carrying classes for its findings is written and read back
- **WHEN** a review record carries `classes` whose keys name finding
  ids of its `findings` and `advisory_findings` and whose values are
  non-empty strings
- **THEN** it is written and validated, and the field reads back as
  given

#### Scenario: a class outside the project's vocabulary is admitted
- **WHEN** a review record carries `classes` naming a class the
  project's vocabulary does not know
- **THEN** the record is admitted — mapping it to `other` is the
  writer's, not the record's

#### Scenario: a classes key naming no finding of the record is refused
- **WHEN** a review record's `classes` carries a key that is not a
  finding id in the record's `findings` or `advisory_findings`
- **THEN** it is refused and nothing is written

#### Scenario: an empty classes object is refused
- **WHEN** a review record carries `classes` as an empty object
- **THEN** it is refused and nothing is written

#### Scenario: a classes that is not an object is refused
- **WHEN** a review record's `classes` is not an object
- **THEN** it is refused and nothing is written

#### Scenario: a class value that is empty or not a string is refused
- **WHEN** a review record's `classes` carries a value that is empty,
  all whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a class value that could forge a line is refused
- **WHEN** a review record's `classes` carries a value holding a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: The reviewer object may carry the reviewer's declared actor
From schema 7 a review record's `reviewer` object MAY carry `actor` —
a non-empty string, the declared reviewer actor the distinct-actor rule
compares (ADR-0018 decision 3) — which SHALL pass the forgeable-text
rule; the object stays closed to every other key. Below schema 7 the
object SHALL stay exactly `role`, `vendor`, `model`, `email`.

#### Scenario: a review whose reviewer carries actor is written and read back
- **WHEN** a review record's `reviewer` carries `actor` as a non-empty
  string
- **THEN** it is written and validated, and the key reads back as given

#### Scenario: an actor that is empty or not a string is refused
- **WHEN** a review record's `reviewer.actor` is empty, all whitespace
  or not a string
- **THEN** it is refused and nothing is written

#### Scenario: an actor that could forge a line is refused
- **WHEN** a review record's `reviewer.actor` carries a character that
  could add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: the reviewer object stays closed to any other key
- **WHEN** a review record's `reviewer` carries a key that is not
  `role`, `vendor`, `model`, `email` or `actor`
- **THEN** it is refused and nothing is written

### Requirement: The link, the classes and the reviewer actor are fields of schema 7
A review record carrying `previous_review`, `classes` or
`reviewer.actor` SHALL carry schema 7: a writer carrying any of them
SHALL stamp 7 through the minimum-schema derivation — `reviewer.actor`,
a key of the reviewer object, raising the stamp the same. None SHALL be
admitted to a review stamped below 7, refused at write and on read —
the two top-level fields by the field-admission rule of the record's
own schema, `actor` by the reviewer object's closed keys under the
record's own schema. A review carrying none of them SHALL be validated
and stamped exactly as before, and the fields SHALL be declared through
the registrations the schema-7 record types use — the field family, the
shared validator tables and the minimum-schema derivation — not by a
second mechanism.

#### Scenario: a review carrying a field of the family stamps schema 7
- **WHEN** a review record is built carrying `previous_review`,
  `classes` or `reviewer.actor`
- **THEN** it carries schema 7

#### Scenario: a field of the family on a review below schema 7 is refused at write
- **WHEN** a review record stamped below 7 carries `previous_review`,
  `classes` or `reviewer.actor`
- **THEN** it is refused and nothing is written

#### Scenario: a field of the family on a review below schema 7 is refused on read
- **WHEN** the journal holds a review record stamped below 7 that
  carries `previous_review`, `classes` or `reviewer.actor`
- **THEN** reading the task's records refuses it

#### Scenario: a review carrying none of the fields keeps its schema and reads as before
- **WHEN** a review record carries none of `previous_review`, `classes`
  and `reviewer.actor`
- **THEN** it is validated and stamped exactly as before the family
  existed

### Requirement: A review may carry what it executed and read
From schema 7 a review record MAY carry `verification` — what the
reviewer ran, read and could not run (ADR-0017 decision 4, ADR-0022
section 2): an object with one or more of the keys `executed`, `read`
and `not_run` and no other key, `executed` a non-empty array of objects
carrying exactly `what` and `result`, `read` a non-empty array of
strings, and `not_run` a non-empty array of objects carrying exactly
`what` and `why`. Every string inside SHALL be non-empty and SHALL pass
the forgeable-text rule, and a refusal SHALL name the key and the
position at fault.

#### Scenario: a review carrying verification is written and read back
- **WHEN** a review record carries `verification` naming what was
  executed, what was read and what was not run
- **THEN** it is written and validated, and the field reads back as
  given

#### Scenario: a verification that is not an object is refused
- **WHEN** a review record's `verification` is not an object
- **THEN** it is refused and nothing is written

#### Scenario: an empty verification object is refused
- **WHEN** a review record carries `verification` as an empty object
- **THEN** it is refused and nothing is written

#### Scenario: a verification carrying a key outside the three is refused
- **WHEN** a review record's `verification` carries a key that is not
  `executed`, `read` or `not_run`
- **THEN** it is refused and nothing is written

#### Scenario: a verification section that is not a non-empty array is refused
- **WHEN** a review record's `verification` carries `executed`, `read`
  or `not_run` as an empty array or as a value that is not an array
- **THEN** it is refused and nothing is written

#### Scenario: an executed entry missing a key or carrying another is refused
- **WHEN** a review record's `verification.executed` carries an entry
  that is not an object carrying exactly `what` and `result`
- **THEN** it is refused and nothing is written

#### Scenario: a not_run entry missing a key or carrying another is refused
- **WHEN** a review record's `verification.not_run` carries an entry
  that is not an object carrying exactly `what` and `why`
- **THEN** it is refused and nothing is written

#### Scenario: a verification string that is empty or not a string is refused
- **WHEN** a string inside a review record's `verification` — a `read`
  item, or an entry's `what`, `result` or `why` — is empty, all
  whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a verification string that could forge a line is refused
- **WHEN** a string inside a review record's `verification` carries a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: a refusal names the key and the position at fault
- **WHEN** a review record's `verification` is refused
- **THEN** the refusal names the section, the position and the key at
  fault

### Requirement: A review may carry evidence for its findings
From schema 7 a review record MAY carry `evidence` — a non-empty object
whose every key is a finding id the same record names in `findings` or
`advisory_findings` and whose every value is a non-empty string, the
evidence behind the finding (ADR-0017 decision 5): a link, a
`file:line`, or the command that checked the claim with the essential
part of its output. Each value SHALL pass the forgeable-text rule, and
each refusal SHALL name the key at fault. An empty `evidence` object
SHALL be refused: a review with no evidence to name carries no
`evidence`.

#### Scenario: a review carrying evidence for its findings is written and read back
- **WHEN** a review record carries `evidence` whose keys name finding
  ids of its `findings` and `advisory_findings` and whose values are
  non-empty strings
- **THEN** it is written and validated, and the field reads back as
  given

#### Scenario: an evidence key naming no finding of the record is refused
- **WHEN** a review record's `evidence` carries a key that is not a
  finding id in the record's `findings` or `advisory_findings`
- **THEN** it is refused and nothing is written

#### Scenario: an empty evidence object is refused
- **WHEN** a review record carries `evidence` as an empty object
- **THEN** it is refused and nothing is written

#### Scenario: an evidence that is not an object is refused
- **WHEN** a review record's `evidence` is not an object
- **THEN** it is refused and nothing is written

#### Scenario: an evidence value that is empty or not a string is refused
- **WHEN** a review record's `evidence` carries a value that is empty,
  all whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: an evidence value that could forge a line is refused
- **WHEN** a review record's `evidence` carries a value holding a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: The verification and the evidence are fields of schema 7
A review record carrying `verification` or `evidence` SHALL carry schema
7: a writer carrying either SHALL stamp 7 through the minimum-schema
derivation. Neither SHALL be admitted to a review stamped below 7,
refused at write and on read by the field-admission rule of the record's
own schema. A review carrying neither SHALL be validated and stamped
exactly as before, and the fields SHALL be declared through the
registrations the schema-7 record types use — the field family, the
shared validator tables and the minimum-schema derivation — not by a
second mechanism.

#### Scenario: a review carrying either field stamps schema 7
- **WHEN** a review record is built carrying `verification` or
  `evidence`
- **THEN** it carries schema 7

#### Scenario: either field on a review below schema 7 is refused at write
- **WHEN** a review record stamped below 7 carries `verification` or
  `evidence`
- **THEN** it is refused and nothing is written

#### Scenario: either field on a review below schema 7 is refused on read
- **WHEN** the journal holds a review record stamped below 7 that
  carries `verification` or `evidence`
- **THEN** reading the task's records refuses it

#### Scenario: a review carrying neither field keeps its schema and reads as before
- **WHEN** a review record carries neither `verification` nor `evidence`
- **THEN** it is validated and stamped exactly as before the fields
  existed

### Requirement: `record-check` writes a check record for a resolved commit

`agentmarshal record-check --task <id> --commit <rev> --name <check>
--result <result>` SHALL write one `check` record through
`create_check_record` — the task the record binds, the commit, the
check's name and its result — and SHALL print the record's path, the
resolved commit, the name, the result and the recorder. `--result`
SHALL be one of `passed`, `failed`, `error` or `skipped`; any other
value SHALL be refused before the command runs, writing nothing.
`--failed-step` and `--run-url` MAY be given, landing as the record's
`failed_step` and `run_url`; without them the record SHALL carry
neither field.

The commit SHALL be resolved to its full 40-hex id — `git rev-parse
--verify <rev>^{commit}` — in the journal's repository: the repository
that holds the journal in either placement, so a sidecar records
against the commits its own repository carries and the host's are never
asked. A reference that does not resolve to a commit there SHALL be
refused naming it, writing nothing. The task SHALL be one a `check`
record may be written for: an unknown task SHALL be refused naming it;
a completed or abandoned task SHALL admit the record — a measurement
admitted after a terminal record, reopening nothing.

#### Scenario: a verdict is recorded at the resolved commit
- **WHEN** `record-check` runs on an open task with `--commit`
  naming a commit the journal's repository holds
- **THEN** one `check` record is written at schema 7 carrying the
  full 40-hex commit id, the name and the result, and the output
  prints the record's path, the commit, the name, the result and the
  recorder

#### Scenario: a short or symbolic commit resolves to the full id
- **WHEN** `--commit` names a reference that is not 40 hex — a short
  id, a branch, `HEAD`
- **THEN** the record's `commit` is the full 40-hex id the reference
  resolves to

#### Scenario: the optional fields land on the record
- **WHEN** `record-check` runs with `--failed-step` and `--run-url`
- **THEN** the record carries `failed_step` and `run_url` as given;
  without them, neither field appears

#### Scenario: a result outside the vocabulary is refused writing nothing
- **WHEN** `--result` names a value that is not `passed`, `failed`,
  `error` or `skipped`
- **THEN** the command is refused before it runs, and no record is
  written

#### Scenario: a commit that does not resolve is refused writing nothing
- **WHEN** `--commit` names a reference the journal's repository does
  not hold
- **THEN** it is refused naming the reference, and no record is
  written

#### Scenario: an unknown task is refused writing nothing
- **WHEN** `record-check` names a task the journal does not carry
- **THEN** it is refused naming the task, and no record is written

#### Scenario: a completed task accepts the record
- **WHEN** `record-check` runs on a task that has completed
- **THEN** the `check` record is written — the measurement a terminal
  record admits — and the task's projection is unchanged

#### Scenario: an abandoned task accepts the record
- **WHEN** `record-check` runs on a task that was abandoned
- **THEN** the `check` record is written, and the task's projection
  is unchanged

### Requirement: `--output-file` keeps the check's full output and announces a `check-output` event

With `--output-file <path>` the command SHALL keep the file's full
bytes — unmasked — under the journal repository's local state
process-log area through `write_payload`, and SHALL append one
`check-output` event carrying the task, the check's name, the resolved
commit, the kept file's path and its sha256 — the mechanism the review
launcher keeps review prose with. An output file that cannot be read
SHALL be refused naming it, writing nothing. Without the flag the
record SHALL carry no `excerpt` and no event SHALL be written. When
the local state cannot be used — git cannot name the common directory
or its directory cannot be created — the output SHALL be kept in a
local temporary file instead, stderr SHALL name the path and say why,
and the record SHALL still be written.

#### Scenario: an output file is kept and a check-output event announces it
- **WHEN** `record-check` runs with `--output-file`
- **THEN** the file's full bytes land under the journal repository's
  local state `log/files/`, and one `check-output` event carries the
  task, the check's name, the resolved commit, the kept file's path
  and the bytes' sha256

#### Scenario: the kept bytes are the file exactly as given
- **WHEN** `record-check` runs with `--output-file` on content that
  trips the leak scan
- **THEN** the kept file holds the bytes unmasked — the masking is
  the excerpt's, and the full output stays on the machine that ran
  the check

#### Scenario: without --output-file no excerpt and no event
- **WHEN** `record-check` runs without `--output-file`
- **THEN** the record carries no `excerpt` field and no `check-output`
  event lands in the process log

#### Scenario: an unreadable output file is refused writing nothing
- **WHEN** `--output-file` names a file that cannot be read
- **THEN** it is refused naming the file, and no record, no event and
  no kept file is produced

#### Scenario: local state that cannot be used falls back to a temporary file
- **WHEN** `record-check` runs with `--output-file` and the clone's
  local state cannot be used
- **THEN** the output is kept in a local temporary file, stderr names
  the path and the reason, no `check-output` event lands, and the
  record is still written

### Requirement: the excerpt is the output's tail — bounded, masked, and safe to render

With `--output-file` the record's `excerpt` SHALL be derived from the
content as: the content decoded as UTF-8 with every undecodable byte
replaced; that text leak-masked; every character the
forgeable-text rule refuses escaped; and the longest suffix of whole
characters whose UTF-8 encoding is at most 4 KiB kept — a mask can be
longer than the span it replaces, so the bound is measured after
masking — so the excerpt's end is always the content's end and no
character is ever halved. An excerpt that comes out empty or all
whitespace SHALL be omitted.

#### Scenario: the excerpt is the content's last 4 KiB at most
- **WHEN** the output file is larger than 4 KiB
- **THEN** the record's `excerpt` encodes to at most 4 KiB of UTF-8
  and its end is the content's end

#### Scenario: the tail is cut on a character boundary
- **WHEN** the 4 KiB cut would split a multi-byte UTF-8 character
- **THEN** the excerpt begins at the next boundary — the split
  character is absent or whole, never half-carried

#### Scenario: undecodable bytes are replaced
- **WHEN** the output's tail holds bytes that are not UTF-8
- **THEN** the excerpt carries the replacement character for them and
  the record is still written

#### Scenario: the bound holds after masking
- **WHEN** masking the tail grows it past 4 KiB
- **THEN** the written `excerpt` still encodes to at most 4 KiB of
  UTF-8 and still ends at the content's end

#### Scenario: characters that could forge a line are escaped
- **WHEN** the output's tail holds newlines or other characters the
  forgeable-text rule refuses
- **THEN** the excerpt carries them as visible escapes, and the
  record passes the rule that would refuse them raw

### Requirement: a leak-scan hit in the excerpt is masked, never refused

Before the excerpt is written it SHALL be passed through the leak
scan with the project's configured private markers. Each matched span
SHALL be replaced by `[masked: <category>]` — a configured marker by
`[masked: private-marker]`, a built-in signature by the signature's
own name — and the command SHALL name the matched categories on
stderr, never the matched text and never a marker's value. A hit
SHALL NOT refuse the record: the check's result is the fact being
recorded, and refusing it would lose the fact with no path to record
it. When the masked excerpt still trips the scan — a private marker
that occurs in the mask label itself — the record SHALL carry no
`excerpt`, and the command SHALL say the excerpt was withheld and
SHALL still name the categories found. The masking SHALL live beside
the scan in `capture.py`, and `agentmarshal leak-scan` SHALL be
unchanged in behaviour and output.

#### Scenario: a signature hit is masked and its category named
- **WHEN** the excerpt trips a built-in signature
- **THEN** the record's `excerpt` carries `[masked: <category>]` in
  place of the span, the command names the category, and the matched
  text appears nowhere in the output or the record

#### Scenario: a private marker is masked by category, value nowhere
- **WHEN** the excerpt contains a configured private marker
- **THEN** the record's `excerpt` carries `[masked: private-marker]`,
  the command names the category, and the marker's value appears
  nowhere in the output or the record

#### Scenario: a hit does not refuse the record
- **WHEN** the excerpt trips the leak scan
- **THEN** the `check` record is written with the masked excerpt, and
  the command exits zero

#### Scenario: an excerpt masking cannot make clean is withheld
- **WHEN** the masked excerpt still trips the scan — a private marker
  that occurs in the mask label itself
- **THEN** the record carries no `excerpt`, the command says the
  excerpt was withheld and names the categories found, and the
  check's result still lands

#### Scenario: the standalone scan is untouched
- **WHEN** `agentmarshal leak-scan` runs
- **THEN** its behaviour and output are exactly what they were before
  this change — the masking is a new function beside the scan, not a
  change to it

### Requirement: `record-check` names its recorder or writes nothing

`record-check` SHALL resolve its recorder as `resolve_recorded_by`
resolves — the environment override, the project actors table, the
git identity — and SHALL refuse clearly when none resolves, before
anything is created. A recorder who is not a declared actor SHALL be
accepted, the record written naming the recorder and its source, and
stderr SHALL say the recorder is not a declared actor. The recorder
SHALL be escaped where it could forge a rendered line.

#### Scenario: no resolvable recorder is refused writing nothing
- **WHEN** `record-check` can resolve no recorder — no override, no
  actors-table match, no git identity
- **THEN** it is refused naming the reason, and nothing is created —
  no record, no event, no kept file

#### Scenario: a recorder who is not a declared actor is accepted and named
- **WHEN** `record-check`'s recorder is not a declared actor
- **THEN** the record is written with `recorded_by` and
  `recorded_by_source` as resolved, and stderr notes the recorder is
  not a declared actor

#### Scenario: a declared actor records with no undeclared note
- **WHEN** `record-check`'s recorder names a declared actor
- **THEN** the record is written and no undeclared-actor note is
  printed

### Requirement: a refusal leaves nothing behind

Every refusal the command can foresee — an unknown or inadmissible
task, a commit that does not resolve, a result outside the
vocabulary, a value the record rules refuse, an unreadable output
file, no resolvable recorder, a malformed project file — SHALL be
decided before any write, so a refused run writes no record, appends
no event and keeps no file, and the journal still validates. A record
write that fails after the output was kept SHALL report the failure
and name the kept file, the way a left artifact is named.

#### Scenario: a refused run leaves the journal, the log and the files area untouched
- **WHEN** `record-check` is refused for any reason it can foresee
- **THEN** the journal is byte-identical, no `check-output` event
  lands, no payload file appears under `log/files/`, and
  `agentmarshal validate` still passes

#### Scenario: a record failure after the output is kept names the kept file
- **WHEN** the output is kept and the record write itself fails
- **THEN** the command reports the failure and names the kept file's
  path

### Requirement: Both review paths take the reviewer's declared actor
`agentmarshal submit-review` and `agentmarshal review` — the launcher in
its commit form and its finding-review form — SHALL take an optional
`--actor <id>` naming the declared reviewer actor (ADR-0018 decision 3,
ADR-0022 section 2). When given, the review record's `reviewer` object
SHALL carry `actor` with that value, passed through
`create_review_record`'s `reviewer_actor` parameter, and the record
SHALL stamp schema 7 through the minimum-schema derivation. The value
SHALL be the flag's own: it SHALL NOT be derived from the environment or
the git identity — the process that launches a reviewer is usually not
the reviewer — and it SHALL stay independent of `recorded_by`, which
says who wrote the record and stamps as before.

#### Scenario: submit-review --actor records the reviewer actor
- **WHEN** `submit-review` records a verdict given `--actor <id>`
- **THEN** the review record's `reviewer` object carries `actor` with
  that value and the record stamps schema 7

#### Scenario: review --actor records the reviewer actor on a commit review
- **WHEN** `review` records a commit verdict given `--actor <id>`
- **THEN** the review record's `reviewer` object carries `actor` with
  that value and the record stamps schema 7

#### Scenario: review --actor records the reviewer actor on a finding review
- **WHEN** `review --reviewed-finding` records a verdict given
  `--actor <id>`
- **THEN** the review record's `reviewer` object carries `actor` with
  that value and the record stamps schema 7

#### Scenario: the reviewer actor is not confused with recorded_by
- **WHEN** a review is recorded given `--actor` by a recorder resolving
  a different actor
- **THEN** the record keeps both — `recorded_by` the writer,
  `reviewer.actor` the declared reviewer actor

### Requirement: Without --actor the review paths are unchanged

Without `--actor` both paths SHALL write the same record, stamp the same
schema and print the same lines as before the flag existed — apart from
the `previous_review` link and the `classes` a launched review records of
its own, which are the launcher's and not the flag's: the flag adds a
capability, never an obligation.

#### Scenario: a review written without --actor is byte-for-byte as before
- **WHEN** `submit-review` or `review` records a verdict without
  `--actor`
- **THEN** the record — apart from its id and times — is byte-for-byte
  the record the command wrote before the flag existed, less the
  `previous_review` and `classes` a launched review records regardless of
  the flag, and every line the command prints is unchanged

### Requirement: A refused --actor costs nothing
Each path SHALL check `--actor` against the record's own rule — a
non-empty string carrying no character that could forge a line — before
anything is written and, for the launcher, before the reviewer command
starts; the refusal SHALL name `--actor`.

#### Scenario: submit-review refuses a refused actor value before writing
- **WHEN** `submit-review --actor` is empty, all whitespace or carries a
  character that could forge a line
- **THEN** the command refuses naming `--actor`, and nothing is written

#### Scenario: the launcher refuses a refused actor value before the reviewer runs
- **WHEN** `review --actor` is empty, all whitespace or carries a
  character that could forge a line
- **THEN** the command refuses naming `--actor` before the reviewer
  command is invoked, and nothing is written

#### Scenario: the dry run refuses a refused actor value before the reviewer runs
- **WHEN** `review --dry-run --actor` is empty, all whitespace or carries
  a character that could forge a line
- **THEN** the command refuses naming `--actor` before the reviewer
  command is invoked, and nothing is written

### Requirement: An undeclared reviewer actor is accepted and noted
An `--actor` id that is not in the project's actors table SHALL be
accepted and recorded as given — the record stands, as an undeclared
recorder does (ADR-0022 section 3) — and the command SHALL say the id is
not a declared actor. Declared-ness SHALL be tested on the id against
the `actors` keys of the project file of the repository holding the
journal — the same project `recorded_by` resolves from.

#### Scenario: an undeclared reviewer actor is accepted and noted
- **WHEN** `--actor` names an id the project's actors table does not
  declare
- **THEN** the review is recorded with the actor as given, and the
  command says the actor is not a declared actor

#### Scenario: a declared reviewer actor is recorded with no note
- **WHEN** `--actor` names an id the project's actors table declares
- **THEN** the review is recorded and no not-declared note is printed

### Requirement: --dry-run shows the actor it would record
`--actor` SHALL be admitted beside `review --dry-run` — the one record
flag the dry run accepts — and a dry run carrying it SHALL say which
actor a recorded review would carry, with the same not-declared note a
recorded run prints.

#### Scenario: a dry run shows the actor it would record
- **WHEN** `review --dry-run --actor <id>` runs
- **THEN** the command's report of the dry run names the actor a
  recorded review would carry

#### Scenario: a dry run notes an undeclared actor as a recorded run does
- **WHEN** `review --dry-run --actor` names an id the project's actors
  table does not declare
- **THEN** the command shows the actor it would record and notes the id
  is not a declared actor

### Requirement: `status` shows a check record on a line of its own

`agentmarshal status <task>` SHALL print one line per `check` record —
after the record's id, type and time: the check's `name`, its `result`,
the commit's short form, and `failed_step` when the record carries one —
and SHALL name the recorder. A recorder that is not a declared actor
SHALL be shown as not a declared actor. Every value taken from the
record SHALL be escaped on display as the other record lines' values are.

#### Scenario: status shows a check record's line
- **WHEN** `agentmarshal status <task>` lists a `check` record
- **THEN** its line carries `name`, `result`, the commit's short form and
  `recorded_by`

#### Scenario: a check record's failed step is shown when present
- **WHEN** `agentmarshal status <task>` lists a `check` record carrying
  `failed_step`, and one carrying none
- **THEN** the first line names the failed step and the second shows no
  `failed_step`

#### Scenario: a recorder that is not a declared actor is shown as such
- **WHEN** `agentmarshal status <task>` lists a `check` record whose
  `recorded_by` is not a declared actor
- **THEN** the line names the recorder and says it is not a declared
  actor

#### Scenario: a check record's values stay on their own line
- **WHEN** `agentmarshal status <task>` lists a `check` record whose
  `name`, `result`, `failed_step` or `recorded_by` carries a character
  that could add a line to rendered output or reorder it — a value an
  older schema's journal can hold where today's read rules do not reach
- **THEN** each refused character prints as its escape and the record
  stays on the one line

### Requirement: A launched review links the task's previous review

`agentmarshal review` — in its commit form and its finding-review form —
SHALL write `previous_review` on the review record it writes: the id of
the task's latest review record at launch time — the latest the task's
records hold when the launch begins, read before the reviewer command
runs so a concurrent write cannot make a review link to itself — whatever
that review bound to. A task carrying no earlier review record SHALL
yield a record with no `previous_review` field. `submit-review` SHALL NOT
write the field.

#### Scenario: a second launched review links the first
- **WHEN** `agentmarshal review` records a verdict on a task that already
  carries a review record
- **THEN** the record's `previous_review` is the earlier review's id —
  whatever it bound to — and the record stamps schema 7

#### Scenario: the first launched review carries no link
- **WHEN** `agentmarshal review` records a verdict on a task carrying no
  review record
- **THEN** the record carries no `previous_review` field

#### Scenario: a launched finding review links the same way
- **WHEN** `review --reviewed-finding` records a verdict on a task that
  already carries a review record
- **THEN** the record's `previous_review` is the earlier review's id

#### Scenario: the link names the latest review at launch time
- **WHEN** `review` launches on a task carrying a review and another
  review record is written while the reviewer runs
- **THEN** the launched record's `previous_review` is the review the
  task carried when the launch began — never the concurrent one, and
  never the launched record's own id

#### Scenario: submit-review writes no link
- **WHEN** `submit-review` records a verdict on a task that already
  carries a review record
- **THEN** the record carries no `previous_review` field

### Requirement: The verdict may carry a class per finding id and the prompt says so

The verdict protocol SHALL admit an optional `classes` object mapping
finding ids to class strings — one class per finding id reported,
blocking or advisory. The prompt the launcher builds, for either binding,
SHALL list the project's finding-class vocabulary —
`review.finding_classes`, the default when unset — and ask for one class
per finding id.

#### Scenario: the prompt lists the default vocabulary
- **WHEN** the launcher builds the review prompt for a project that does
  not set `review.finding_classes`
- **THEN** the prompt names each default class and asks for one class per
  finding id reported

#### Scenario: the prompt lists the project's configured vocabulary
- **WHEN** `review.finding_classes` is set in the journal repository's
  project file
- **THEN** the prompt lists that vocabulary instead

#### Scenario: a classes object is admitted by the protocol
- **WHEN** a verdict carries `classes` mapping finding ids to class
  strings
- **THEN** the verdict parses — `classes` is an optional key, never an
  unknown one

### Requirement: The launcher records the classes a verdict names, dropping what it cannot keep

When a launched review's verdict carries `classes`, the record SHALL
carry a `classes` entry for each id among the verdict's `findings` and
`advisory_findings`: the class given when it is in the project's
vocabulary, `other` when it is not — with a warning naming the id and
the class given. An entry for an id the verdict does not carry SHALL be
dropped with a warning, and a `classes` that is not an object — or holds
a value that is not a usable class string — SHALL be dropped as a whole
with a warning. A verdict SHALL NOT be refused over a class: the run is
paid and the class is reference markup. A verdict carrying no `classes`
SHALL be recorded exactly as before — no `classes` field.

#### Scenario: classes for the verdict's ids are recorded
- **WHEN** a verdict carries `classes` naming classes of the vocabulary
  for ids among its `findings` and `advisory_findings`
- **THEN** the record carries them, and the review stamps schema 7

#### Scenario: a class outside the vocabulary records as other with a warning
- **WHEN** a verdict's `classes` names, for a finding id it carries, a
  class the vocabulary does not know
- **THEN** the record carries `other` for the id and the command prints a
  warning naming the id and the class given

#### Scenario: an entry for an id the verdict does not carry is dropped with a warning
- **WHEN** a verdict's `classes` names an id that is not among its
  `findings` or `advisory_findings`
- **THEN** that entry is dropped with a warning and the entries for the
  verdict's ids are recorded

#### Scenario: a classes that is not an object is dropped whole with a warning
- **WHEN** a verdict's `classes` is not an object
- **THEN** the verdict is recorded, no `classes` field lands and a
  warning says the value was dropped

#### Scenario: a classes holding a value that is no class string is dropped whole
- **WHEN** a verdict's `classes` holds a value that is not a non-empty
  string
- **THEN** the whole object is dropped with a warning — the verdict is
  never refused over a class — and the record carries no `classes`

#### Scenario: a verdict without classes records exactly as before
- **WHEN** a verdict carries no `classes`
- **THEN** the record carries no `classes` field — and its schema stamp
  rises only where `previous_review` asks it
