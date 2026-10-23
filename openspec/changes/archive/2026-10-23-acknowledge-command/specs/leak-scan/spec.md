## ADDED Requirements

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

## MODIFIED Requirements

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
