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
no task state and is not admitted after a terminal record. Nothing reads
acknowledgements yet — the command that writes them and the surfaces that
mark acknowledged hits come with their own tasks.

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
