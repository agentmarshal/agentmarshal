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
in the journal.

#### Scenario: by default the prose stays out of the journal
- **WHEN** `agentmarshal review` records a verdict in a project whose file has
  no `capture` section
- **THEN** nothing is written under the task's artifacts directory, the record
  carries no `artifacts`, and the reviewer's output is kept in a local
  temporary file whose path the command names on stderr

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
