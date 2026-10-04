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
