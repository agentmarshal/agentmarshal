## ADDED Requirements

### Requirement: `leak-scan` reads the journal's acknowledgements for the candidate

`agentmarshal leak-scan --base <ref> --commit <rev>` SHALL look up the
journal's `acknowledgement` records bound to the candidate: the records
whose `commit` equals the candidate's resolved commit — the full 40-hex
id `git rev-parse --verify <rev>^{commit}` gives in the repository the
scan reads. It SHALL read them from every task of the journal, or from
the one task an optional `--task <id>` names, where the gate reads
records: the calling checkout's working tree in the embedded placement,
the journal repository's working tree under a sidecar (ADR-0014). An
acknowledgement on a task that has since closed still counts — the
record binds the commit, not the task's state. A repository carrying no
journal has no records to find, and the command SHALL behave there
exactly as it does without acknowledgements. When the journal or a
task's records cannot be read — a task `--task` names that does not
exist, a record that fails validation, a journal that cannot be listed
— no hit SHALL count as acknowledged and the command SHALL say why on
stderr.

#### Scenario: the records are read from every task of the journal
- **WHEN** `leak-scan` runs without `--task` and `acknowledgement`
  records bound to the candidate sit on several tasks
- **THEN** each is read, and a hit any of them names counts as
  acknowledged

#### Scenario: --task reads the one task's records
- **WHEN** `leak-scan --task <id>` runs and an acknowledgement bound to
  the candidate sits on a different task
- **THEN** it is not read and the hit counts as unacknowledged; a
  record on the named task still counts

#### Scenario: a task that cannot be read acknowledges nothing
- **WHEN** `--task` names a task the journal does not carry, or one
  whose records fail reading
- **THEN** no hit counts as acknowledged and the command says why on
  stderr

#### Scenario: a journal that cannot be read acknowledges nothing
- **WHEN** reading the journal's tasks or a task's records fails
- **THEN** no hit counts as acknowledged and the command says why on
  stderr

#### Scenario: an acknowledgement on a closed task still counts
- **WHEN** the task carrying the acknowledgement has since completed or
  been abandoned
- **THEN** the record still acknowledges the hit it names — it binds
  the commit, not the task's state

#### Scenario: a repository with no journal behaves as without acknowledgements
- **WHEN** `leak-scan` runs in a git repository carrying no AgentMarshal
  journal
- **THEN** it prints and exits exactly as a run finding no
  acknowledgements does

### Requirement: `leak-scan` acknowledges a hit under the scan's own naming only

A record SHALL acknowledge a hit only on the three bindings ADR-0021
decision 2 names: the candidate's commit, the file exactly as the scan
prints it — masking included — and the hit's identification, where the
record's `signature` equals a signature hit's identification and
`private-marker #<n>` equals a marker hit's for the record's `marker`
<n>. There is no other matching: no path normalisation, no globbing, no
case folding. A new commit, a differently-spelled file or a renumbered
marker list therefore shows the hit again as unacknowledged. Where
several records match one hit, the earliest in journal order marks it.

#### Scenario: an acknowledgement bound to the hit acknowledges it
- **WHEN** a record's `commit` equals the candidate's resolved commit,
  its `file` equals the hit's file as the scan prints it and its
  `signature` equals the hit's identification
- **THEN** the hit counts as acknowledged

#### Scenario: a marker's number identifies a marker hit
- **WHEN** a record carries `marker` <n> and the hit's identification
  is `private-marker #<n>` on the same commit and file
- **THEN** the hit counts as acknowledged

#### Scenario: a record on another commit acknowledges nothing
- **WHEN** a record names the hit's file and identification but its
  `commit` is not the candidate's resolved commit
- **THEN** the hit counts as unacknowledged

#### Scenario: a file spelled differently acknowledges nothing
- **WHEN** a record's `file` differs from the hit's file as the scan
  prints it
- **THEN** the hit counts as unacknowledged

#### Scenario: an identification that is not the hit's acknowledges nothing
- **WHEN** a record's signature or marker does not equal the hit's
  identification — a marker renumbered since the record was written
  among them
- **THEN** the hit counts as unacknowledged

#### Scenario: the earliest matching record marks the hit
- **WHEN** two `acknowledgement` records both name a hit's commit, file
  and identification
- **THEN** the mark names the earlier record in journal order

### Requirement: an acknowledged hit stays printed and marked, and only an unacknowledged hit fails the command

Every hit the scan reports SHALL still be printed, in the order and
form it prints today, and an acknowledged hit's entry SHALL
additionally carry a mark naming who acknowledged it — the record's
`recorded_by` — and the `reason`, each escaped on display as the other
displayed record values are. Nothing is removed, and the matched text
is never printed. The command SHALL exit 0 when the scan finds hits
and every one is acknowledged, SHALL exit 1 when any hit is
unacknowledged, and SHALL print and exit exactly as today when the
scan finds nothing or finds no acknowledgement. The mark belongs to
this command: the merge boundary's leak-scan line and its bound are
unchanged until the task that lands the gate's marking (ADR-0021
decision 3).

#### Scenario: an acknowledged hit prints marked
- **WHEN** a hit is acknowledged
- **THEN** its printed entry additionally carries a mark naming who
  acknowledged it and the reason

#### Scenario: every hit still prints in today's order and form
- **WHEN** the scan reports hits of which some are acknowledged and
  some are not
- **THEN** every hit appears in the order and form it prints today, the
  acknowledged entries carrying the mark

#### Scenario: the mark is escaped where it could forge a line
- **WHEN** the acknowledging record's `recorded_by` carries a character
  that could add a line to rendered output or reorder it
- **THEN** the mark prints each such character as its escape

#### Scenario: the matched text is never printed
- **WHEN** a hit is acknowledged
- **THEN** neither stdout nor stderr carries the matched text or a
  marker's value

#### Scenario: every hit acknowledged exits 0
- **WHEN** the scan reports hits and every one is acknowledged
- **THEN** the command exits 0

#### Scenario: any unacknowledged hit exits 1
- **WHEN** the scan reports a hit nobody has acknowledged
- **THEN** the command exits 1

#### Scenario: a clean scan is unchanged
- **WHEN** the scan reports no hits
- **THEN** the command prints and exits as it does without
  acknowledgements

#### Scenario: a run with no acknowledgement is byte for byte today's
- **WHEN** the scan reports hits and the journal holds no
  acknowledgement naming one
- **THEN** the hits print exactly as before, unmarked, and the command
  exits 1

#### Scenario: the merge boundary's line carries no mark yet
- **WHEN** the gate's added-content scan reports a hit an
  acknowledgement names
- **THEN** its line prints as today — the same file and identification
  the standalone command gives, and no mark

## MODIFIED Requirements

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
status answers whether a hit nobody has acknowledged was found, and an
ordinary binary file in a diff is not one.

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
own. `agentmarshal leak-scan`'s own scan is unchanged — the same
functions over the same inputs; what a written record changes on the
standalone command's surface is the marking and the exit status the
requirements above give, never what the scan reports.

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
- **WHEN** `agentmarshal leak-scan --base --commit` runs on a range
  whose reported hits no `acknowledgement` record names
- **THEN** it prints each hit exactly as before, unmarked, and exits 1
