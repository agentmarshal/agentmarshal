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
included, can still match — and the file SHALL be named in the caller's
output as one that was only partially readable, never passed over in silence.
A path whose own bytes are not UTF-8 SHALL be named in an escaped printable
form, so naming it prints no raw bytes.

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

#### Scenario: a file that does not decode is named, not passed over in silence
- **WHEN** a file's added content does not decode as UTF-8
- **THEN** the gate's transcript and the standalone command's output each name
  the file as one whose bytes were still searched

#### Scenario: a path that does not decode is named in escaped form
- **WHEN** the file the scan could not decode carries a path whose own bytes
  are not UTF-8
- **THEN** the output names it in an escaped printable form and prints no raw
  path bytes

#### Scenario: an undecodable file alone does not fail the command
- **WHEN** the only thing the standalone command has to report is files it
  could not decode
- **THEN** it names them and exits successfully

#### Scenario: the gate's scan stays advisory over undecodable files
- **WHEN** the gate's added-content scan cannot decode a file
- **THEN** the transcript names the file in a warning and the file adds no
  violation
