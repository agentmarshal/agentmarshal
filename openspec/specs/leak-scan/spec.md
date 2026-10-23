# leak-scan Specification

## Purpose
What the added-content leak scan reports and what it refuses to print.
A hit has to be actionable — the file, and which signature or which configured
marker matched — and the scan's own output must never carry the thing it is
looking for, including in a path.

## Requirements

### Requirement: A leak-scan hit names where it matched and what matched
A hit from the added-content scan SHALL name the file it matched in and what
matched: the signature's own identifier for a built-in signature, and the
configured marker's position in the project's marker list for a private
marker. It SHALL NOT print the matched text, nor the marker's value: a private
marker is itself the sensitive string, which is why it is named by position. A
path that carries a secret SHALL NOT be printed either — neither one
containing a configured marker nor one matching a built-in signature — and
SHALL be described the way that marker or signature is named.

The scan that refuses one captured artefact reports the categories it matched
and no location: the caller named the artefact it offered, so there is no file
to add.

A caller that renders hits into a document of its own — the merge transcript —
MAY bound how many it shows, and SHALL say how many it did not. A caller whose
whole output is the list of places to look SHALL NOT bound it: the operator ran
it to learn where every hit is.

#### Scenario: a built-in signature names its file and itself
- **WHEN** the scan matches a built-in signature in an added line
- **THEN** the hit names the file and the signature, and the matched text
  appears nowhere in the output

#### Scenario: a private marker is named by position, not by value
- **WHEN** the scan matches a configured private marker
- **THEN** the hit names the file and which marker of the configured list
  matched, and the marker's value appears nowhere in the output

#### Scenario: a path that carries a marker is described, not printed
- **WHEN** the file a hit matched in has a path containing a configured marker
- **THEN** the rendering describes the path by that marker's position and the
  marker's value appears nowhere in the output

#### Scenario: a path that is itself a key is described, not printed
- **WHEN** the file a hit matched in has a path that matches a built-in
  signature
- **THEN** the rendering describes the path by that signature's name and the
  characters that matched appear nowhere in the output

#### Scenario: an artefact refusal reports what matched, not where
- **WHEN** the scan refuses one captured artefact
- **THEN** the refusal names the categories that matched and names no file

#### Scenario: the merge boundary reports the same detail
- **WHEN** the gate's added-content scan finds a hit
- **THEN** its line carries the same file and identification the standalone
  command gives

#### Scenario: the transcript's line is bounded and says what it left out
- **WHEN** the gate's added-content scan finds more hits than its line shows
- **THEN** the line shows the first of them and says how many it did not show

#### Scenario: the standalone command shows every place to look
- **WHEN** the standalone leak-scan command finds more hits than the gate's
  line would show
- **THEN** every hit appears in its output

### Requirement: A marker is not matched against the declaration that configures it
The scan SHALL NOT report a private-marker hit whose only occurrence in the
scanned content is the project configuration that declares that marker.

#### Scenario: a change to the marker list does not trip on itself
- **WHEN** the scanned content is a diff of the project configuration that
  declares the markers, and the markers appear only there
- **THEN** the scan reports no private-marker hit

#### Scenario: a marker elsewhere in the same content is still reported
- **WHEN** the scanned content includes both the declaration and an occurrence
  of the same marker in another file
- **THEN** the scan reports the hit, naming the other file

### Requirement: A file that does not decode costs its own readability, not every file's scan
The scan reads the candidate diff one file section at a time. A file whose
section does not decode as UTF-8 SHALL NOT keep any other file's added
content from being scanned. The file's own added bytes SHALL still be
searched — decoded so that whatever valid UTF-8 they hold, ASCII signatures
included, can still match — and a byte that is not a line separator in patch
output SHALL NOT end that search early. The file SHALL be named in the
caller's output as one that was only partially readable, never passed over
in silence.

A name the scan prints is a path like any other it prints: a name that
carries a secret — a configured marker or a string matching a built-in
signature — SHALL be described the way that marker or signature is named,
and a path whose own bytes are not UTF-8 SHALL be named in an escaped
printable form, so naming a file prints neither the secret nor raw bytes.

A file is named when the bytes it lost are bytes the scan reads: its added
content, or the headers that carry its path. A file whose undecodable bytes
sit only in removed lines — a deleted binary — lost nothing the scan reads
and SHALL NOT be named.

A file that did not decode is not a hit: it is a place the scan could not
fully read, reported beside the hits rather than as one. The gate's scan
stays advisory — undecodable files are a warning, never a violation — and the
standalone command names them without failing on their account: its exit
status answers whether a hit was found, and an ordinary binary file in a diff
is not one.

#### Scenario: one file that does not decode does not switch the scan off
- **WHEN** a diff adds a text file holding a secret-shaped string and a file
  whose added bytes are not UTF-8
- **THEN** the hit in the text file is reported, naming it, and the
  undecodable file is named too

#### Scenario: an undecodable file's bytes are still searched
- **WHEN** a file's added bytes do not decode as UTF-8 but a span of them
  matches a built-in signature
- **THEN** the hit is reported, naming the file

#### Scenario: bytes after a non-separator control byte are still searched
- **WHEN** a file's undecodable added bytes hold a span matching a built-in
  signature after a byte that is not a patch line separator
- **THEN** the hit is still reported, naming the file

#### Scenario: a file that does not decode is named, not passed over in silence
- **WHEN** a file's added content does not decode as UTF-8
- **THEN** the gate's transcript and the standalone command's output each name
  the file as one whose bytes were still searched

#### Scenario: a path that does not decode is named in escaped form
- **WHEN** the file the scan could not decode carries a path whose own bytes
  are not UTF-8
- **THEN** the output names it in an escaped printable form and prints no raw
  path bytes

#### Scenario: an undecodable path that carries a marker is described, not printed
- **WHEN** the file the scan could not decode has a path containing a
  configured marker
- **THEN** the caller names it by that marker's position, and the marker's
  value appears nowhere in the output

#### Scenario: an undecodable path that is itself a key is described, not printed
- **WHEN** the file the scan could not decode has a path matching a built-in
  signature
- **THEN** the caller names it by that signature's identifier, and the
  characters that matched appear nowhere in the output

#### Scenario: a file whose undecodable bytes are all removed is not named
- **WHEN** a diff removes a file whose deleted bytes are not UTF-8 and the
  file adds no undecodable bytes
- **THEN** it is not named among the files the scan could not read

#### Scenario: an undecodable file alone does not fail the command
- **WHEN** the only thing the standalone command has to report is files it
  could not decode
- **THEN** it names them and exits successfully

#### Scenario: the gate's scan stays advisory over undecodable files
- **WHEN** the gate's added-content scan cannot decode a file
- **THEN** the transcript names the file in a warning and the file adds no
  violation

### Requirement: An acknowledgement record carries a reviewed leak-scan hit
From schema 7 the journal admits an `acknowledgement` record: what an
operator writes having verified that a hit the added-content scan reported
is not a leak (ADR-0021). The record SHALL carry `commit` — the candidate
commit the hit was found in, exactly 40 lowercase hex characters; `file` —
the file exactly as the scan's hit prints it, a path already masked, a
non-empty string; exactly one of `signature` — the identifier of a built-in
signature the scan knows — and `marker` — the matched marker's position in
the project's configured marker list, an integer of at least 1 — the hit's
identification as the scan prints it, never the matched text and never the
marker's value; and `reason` — a non-empty string of at most 1000
characters, bounded by the character-bounded text rule. `file` and `reason`
SHALL pass the forgeable-text rule registered for this record type and
field. The record SHALL name its recorder in `recorded_by` with
`recorded_by_source`, as `finding` and `check` already do. It projects to
no task state and is not admitted after a terminal record. `status` is the
surface that reads it and `acknowledge` the command that writes it — the
hit surfaces that mark acknowledged hits come with their own tasks.

#### Scenario: an acknowledgement record is written and read back
- **WHEN** an `acknowledgement` record carries `commit`, `file`,
  `signature` and `reason`
- **THEN** it is written and validated, and each field reads back as given

#### Scenario: a marker's position identifies the hit as well
- **WHEN** an `acknowledgement` record carries `marker` in place of
  `signature`
- **THEN** it is written and validated, and `signature` appears nowhere in
  it

#### Scenario: a record carrying both or neither of signature and marker is refused
- **WHEN** an `acknowledgement` record carries both `signature` and
  `marker`, or neither
- **THEN** it is refused with a refusal naming the two fields, and nothing
  is written

#### Scenario: a signature the scan does not know is refused
- **WHEN** an `acknowledgement` record's `signature` is not a string or not
  the identifier of a built-in signature the scan knows
- **THEN** it is refused and nothing is written

#### Scenario: a marker that is not an integer of at least 1 is refused
- **WHEN** an `acknowledgement` record's `marker` is not an integer, or is
  an integer below 1
- **THEN** it is refused and nothing is written

#### Scenario: a commit that is not 40 lowercase hex is refused
- **WHEN** an `acknowledgement` record's `commit` is missing, not a string,
  or not exactly 40 lowercase hex characters
- **THEN** it is refused and nothing is written

#### Scenario: a file that is missing or empty is refused
- **WHEN** an `acknowledgement` record's `file` is missing, empty, all
  whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a reason that is missing or empty is refused
- **WHEN** an `acknowledgement` record's `reason` is missing, empty, all
  whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a reason beyond the character bound is refused
- **WHEN** an `acknowledgement` record's `reason` carries more than 1000
  characters
- **THEN** it is refused and nothing is written

#### Scenario: a displayed string that could forge a line is refused
- **WHEN** an `acknowledgement` record's `file` or `reason` carries a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: an acknowledgement record that names no recorder is refused
- **WHEN** an `acknowledgement` record carries neither `recorded_by` nor
  `recorded_by_source`
- **THEN** it is refused

#### Scenario: an acknowledgement on a closed task is refused
- **WHEN** an `acknowledgement` record is written for a task that has
  completed or been abandoned
- **THEN** no record is written, the refusal names the state, and the
  journal still validates

### Requirement: An acknowledgement record is a record of schema 7
An `acknowledgement` record SHALL carry schema 7 — the schema the record
type was introduced under. An `acknowledgement` record stamped below 7
SHALL be refused at write, and on read: the field-admission rule of the
record's own schema admits the family's fields only from 7, and the
record-type gate refuses the type below its schema whatever the record
carries. A writer SHALL stamp 7 through the minimum-schema derivation — the
record type itself needs it.

#### Scenario: an acknowledgement record stamps schema 7
- **WHEN** an `acknowledgement` record is built
- **THEN** it carries schema 7

#### Scenario: an acknowledgement record stamped below 7 is refused at write
- **WHEN** an `acknowledgement` record stamped below 7 is presented for
  write
- **THEN** it is refused and nothing is written

#### Scenario: an acknowledgement record stamped below 7 is refused on read
- **WHEN** the journal holds an `acknowledgement` record stamped below 7
- **THEN** reading the task's records refuses it

### Requirement: `status` shows an acknowledgement record on a line of its own

`agentmarshal status <task>` SHALL print one line per `acknowledgement`
record — after the record's id, type and time: the acknowledged commit's
short form, the `file` as recorded, the hit's identification — the
`signature` when the record carries one, the `marker`'s number when it
carries a marker — and the `reason` — and SHALL name the recorder. A
recorder that is not a declared actor SHALL be shown as not a declared
actor. Where the recorder is a declared author or committer of the
acknowledged commit the line SHALL say the hit was self-acknowledged —
derived on display the way the self-acceptance mark is, never stored —
and where git cannot read the commit the line SHALL say the mark was not
checked rather than answering either way. Every value taken from the
record SHALL be escaped on display as the other record lines' values are.

#### Scenario: status shows an acknowledgement's line
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record carrying a `signature`
- **THEN** its line carries the commit's short form, `file`,
  `signature`, `recorded_by` and `reason`

#### Scenario: a marker's number identifies the hit on the line
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record carrying a `marker`
- **THEN** its line carries `marker` and the marker's number, and no
  `signature`

#### Scenario: a self-acknowledgement is marked
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose recorder is a declared author or committer of the
  acknowledged commit
- **THEN** the line says the hit was self-acknowledged

#### Scenario: an acknowledgement by another actor is not marked
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose recorder is not a declared author or committer of the
  acknowledged commit
- **THEN** the line carries no self-acknowledgement mark

#### Scenario: git cannot read the commit
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose commit git cannot read
- **THEN** the line says the self-acknowledgement mark was not checked

#### Scenario: a recorder that is not a declared actor is shown as such
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose `recorded_by` is not a declared actor
- **THEN** the line names the recorder and says it is not a declared
  actor

#### Scenario: an acknowledgement's values stay on their own line
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose `file`, `reason`, `signature` or `recorded_by` carries a
  character that could add a line to rendered output or reorder it — a
  value an older schema's journal can hold where today's read rules do
  not reach
- **THEN** each refused character prints as its escape and the record
  stays on the one line

### Requirement: `acknowledge` writes an acknowledgement record for a reported hit

`agentmarshal acknowledge --task <id> --base <ref> --commit <rev>
--file <path> (--signature <id> | --marker <n>) --reason <text>` SHALL
write one `acknowledgement` record through
`create_acknowledgement_record` — the task, the commit resolved to its
full 40-hex id, the file exactly as the scan's hit prints it, the
identification and the reason — and SHALL print the record's path, the
resolved commit, the file, the identification and the recorder. Exactly
one of `--signature` and `--marker` SHALL be given: both or neither
SHALL be refused before the command runs, writing nothing. The commit
SHALL be resolved — `git rev-parse --verify <rev>^{commit}` — in the
repository the scan reads: the project's own in the embedded placement,
the host's under a sidecar, where the candidate's commits live. A
`--commit` that resolves to no commit there SHALL be refused naming it,
and a `--base` and `--commit` sharing no merge base SHALL be refused
naming both — in each case writing nothing. The task SHALL be one an
`acknowledgement` record may be written for: an unknown task SHALL be
refused naming it, and a completed or abandoned task SHALL be refused
naming its state — the record type is admitted after no terminal
record — in each case writing nothing.

#### Scenario: an acknowledgement is written for a reported hit
- **WHEN** `acknowledge` runs on an open task naming a hit the
  added-content scan reports — `--file` the file exactly as the scan
  prints it and `--signature` the hit's signature id
- **THEN** one `acknowledgement` record is written at schema 7 carrying
  the full 40-hex commit id, the file, the signature and the reason,
  and the output prints the record's path, the resolved commit, the
  file, the identification and the recorder

#### Scenario: a marker's number acknowledges a marker hit
- **WHEN** `acknowledge` runs with `--marker <n>` naming a hit the scan
  reports as `private-marker #<n>`
- **THEN** the record carries `marker` and no `signature`

#### Scenario: a short or symbolic commit resolves to the full id
- **WHEN** `--commit` names a reference that is not 40 hex — a short
  id, a branch, `HEAD`
- **THEN** the record's `commit` is the full 40-hex id the reference
  resolves to in the scanned repository

#### Scenario: both or neither of --signature and --marker is refused before the command runs
- **WHEN** `acknowledge` runs with both `--signature` and `--marker`,
  or with neither
- **THEN** it is refused before the command runs, and no record is
  written

#### Scenario: an unknown task is refused writing nothing
- **WHEN** `acknowledge` names a task the journal does not carry
- **THEN** it is refused naming the task, and no record is written

#### Scenario: a completed or abandoned task is refused writing nothing
- **WHEN** `acknowledge` runs on a task that has completed or been
  abandoned
- **THEN** it is refused naming the state, and no record is written

#### Scenario: a commit that does not resolve is refused writing nothing
- **WHEN** `--commit` names a reference the scanned repository does not
  hold
- **THEN** it is refused naming the reference, and no record is written

#### Scenario: a base sharing no merge base is refused writing nothing
- **WHEN** `--base` and `--commit` share no merge base in the scanned
  repository
- **THEN** it is refused naming both references, and no record is
  written

### Requirement: `acknowledge` checks the hit against the same scan `leak-scan` runs

Before writing, `acknowledge` SHALL run the same added-content scan
`agentmarshal leak-scan --base --commit` runs: the merge base of the
two refs in the scanned repository; the project's private markers read
from the trusted side as the standalone command reads them — the
merge-base tree in the embedded placement, the sidecar's own
configuration under a sidecar; the `merge-base..commit` diff through
`leak_scan_diff`; and the hits through `scan_diff_for_leaks` with the
same declaration-path suppression — the same functions over the same
inputs, never a second scan. The command SHALL write only when the scan
reports a hit whose file equals `--file` — exactly as the scan prints
it, masking included — and whose identification equals `--signature`,
or `private-marker #<n>` for `--marker <n>`; there is no other
matching: no path normalisation, no globbing, no case folding.
Otherwise the command SHALL refuse, naming the file and the
identification it was given and how many hits the scan did report —
never the matched text and never a marker's value. A file the scan
could not decode is not a hit: the command SHALL name it beside the
result as the standalone command does, and it SHALL fail nothing on its
own. `agentmarshal leak-scan` SHALL be unchanged in behaviour, output
and exit status — an acknowledgement is not yet honoured on any hit
surface.

#### Scenario: a hit is acknowledged only under its printed name
- **WHEN** `--file` spells the file differently than the scan prints it
  — another path, another separator, a path carrying the marker where
  the scan prints the masked form
- **THEN** the acknowledgement is refused naming the file as given and
  how many hits the scan reported, and no record is written

#### Scenario: an identification the scan does not report for that file is refused
- **WHEN** `--file` names a file the scan reports a hit in but
  `--signature` or `--marker` is not the identification the hit carries
- **THEN** the acknowledgement is refused naming the file and the
  identification given and how many hits the scan reported, and no
  record is written

#### Scenario: a hit on another commit is not a hit here
- **WHEN** the file and identification name a hit the scan reported on
  a different commit but the scan over `--base`..`--commit` reports
  none for them
- **THEN** the acknowledgement is refused saying how many hits the scan
  did report, and no record is written

#### Scenario: a clean scan reports no hit to acknowledge
- **WHEN** the scan over `--base`..`--commit` reports no hits at all
- **THEN** the acknowledgement is refused saying the scan reported no
  hits, and no record is written

#### Scenario: the matched text appears nowhere in the output
- **WHEN** `acknowledge` runs — refused or writing
- **THEN** neither stdout nor stderr carries the matched text or a
  marker's value, and the written record carries none either

#### Scenario: a file the scan could not decode is named beside the result
- **WHEN** the diff holds a file whose added bytes do not decode as
  UTF-8
- **THEN** the command names the file on stderr as one whose bytes were
  still searched — masked the way every printed name is — and the file
  is no hit and fails nothing on its own

#### Scenario: a hit under a marker-named path acknowledges by the masked name
- **WHEN** a hit's file is printed by the scan in masked form — a path
  carrying a configured marker
- **THEN** `--file` naming the masked form writes the record, and
  `--file` naming the raw path is refused, the raw path printed nowhere

#### Scenario: the standalone command's output and exit are unchanged
- **WHEN** an `acknowledgement` record for a reported hit has been
  written and `agentmarshal leak-scan --base --commit` runs on the
  same range
- **THEN** it prints the hit exactly as before and exits 1 — the
  acknowledgement is not yet honoured on the hit's surfaces

### Requirement: `acknowledge` names its recorder or writes nothing

`acknowledge` SHALL resolve its recorder as `resolve_recorded_by`
resolves — the environment override, the project actors table, the git
identity — and SHALL refuse clearly when none resolves, before anything
is created. A recorder who is not a declared actor SHALL be accepted,
the record written naming the recorder and its source, and the output
SHALL say the recorder is not a declared actor. The recorder SHALL be
escaped where it could forge a rendered line.

#### Scenario: no resolvable recorder is refused writing nothing
- **WHEN** `acknowledge` can resolve no recorder — no override, no
  actors-table match, no git identity
- **THEN** it is refused naming the reason, and the records directory
  is untouched

#### Scenario: a recorder who is not a declared actor is accepted and named
- **WHEN** `acknowledge`'s recorder is not a declared actor
- **THEN** the record is written with `recorded_by` and
  `recorded_by_source` as resolved, and the output notes the recorder
  is not a declared actor

#### Scenario: a declared actor records with no undeclared note
- **WHEN** `acknowledge`'s recorder names a declared actor — whether
  resolved through the actors table or named by the override
- **THEN** the record is written and no undeclared-actor note is
  printed

#### Scenario: the recorder is escaped where it could forge a line
- **WHEN** the recorder's name carries a character that could add a
  line to rendered output or reorder it
- **THEN** the output prints the escaped form, in the recorder line and
  the note alike

### Requirement: a refusal leaves nothing behind

Every refusal the command can foresee — an unknown or inadmissible
task, a commit or base that does not resolve, both or neither of
`--signature` and `--marker`, a value the record rules refuse, a
`--reason` that trips the scan, a hit the scan does not report, no
resolvable recorder, a project file that cannot be read — SHALL be
decided before any write, so a refused run writes no record, and the
journal still validates.

#### Scenario: a refused run leaves the journal untouched
- **WHEN** `acknowledge` is refused for any reason it can foresee
- **THEN** the journal is byte-identical and `agentmarshal validate`
  still passes

#### Scenario: a value the record rules refuse writes nothing
- **WHEN** a field the record rules govern — a reason beyond the
  1000-character bound, an empty file or reason, a signature the scan
  does not know, a marker below 1 — would keep the record from being
  written
- **THEN** the command is refused naming the field's rule, and no
  record is written

#### Scenario: a reason that trips the scan is refused naming the categories
- **WHEN** `--reason` carries a string a built-in signature matches or
  a configured private marker
- **THEN** the acknowledgement is refused naming the categories the
  scan found — never the matched text nor a marker's value — and no
  record is written
