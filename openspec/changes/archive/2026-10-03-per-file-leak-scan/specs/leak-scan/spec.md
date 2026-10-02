## ADDED Requirements

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
