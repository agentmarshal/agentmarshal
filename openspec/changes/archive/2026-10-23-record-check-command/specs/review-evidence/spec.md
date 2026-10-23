## ADDED Requirements

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
content as: the last 4 KiB at most of its bytes, the cut moved forward
to a UTF-8 character boundary so no character is halved, undecodable
bytes replaced; that text leak-masked; every character the
forgeable-text rule refuses escaped; and the result bounded once more
to at most 4 KiB of UTF-8 — a mask can be longer than the span it
replaces, so the bound is measured after masking — cut from the front
on a character boundary so the content's end always survives. An
excerpt that comes out empty or all whitespace SHALL be omitted.

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
it. The masking SHALL live beside the scan in `capture.py`, and
`agentmarshal leak-scan` SHALL be unchanged in behaviour and output.

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
