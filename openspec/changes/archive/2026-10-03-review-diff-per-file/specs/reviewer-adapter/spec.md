## ADDED Requirements

### Requirement: A diff that is not wholly UTF-8 still reaches the reviewer, per file
A commit review SHALL decode the merge-base diff one file section at a time,
through the same per-file decode the leak scan uses. A file whose section
does not decode as UTF-8 SHALL NOT keep the review from launching, nor keep
any other file's diff from reaching the reviewer. Each file that did not
decode SHALL be named — in what the reviewer is given and in the command's
own output — and its section SHALL still be shown with its unreadable bytes
marked, never passed over in silence.

The other git output the launch reads — merge-base, ls-tree, rev-parse,
error text — SHALL surface as printable text or a named refusal, never a
traceback, and a path whose bytes are not UTF-8 SHALL be named in an escaped
printable form.

#### Scenario: a file that does not decode does not stop the review
- **WHEN** a reviewed commit adds a text file and a file whose added bytes
  are not UTF-8
- **THEN** the reviewer is launched and its prompt carries the text file's
  diff

#### Scenario: the reviewer is told what it could not be shown
- **WHEN** the reviewed diff holds a file whose bytes did not decode
- **THEN** the prompt names the file, says how its unreadable bytes are
  marked, and still shows what decoded

#### Scenario: the command names what the reviewer could not be shown
- **WHEN** a review runs over a diff that was not wholly UTF-8
- **THEN** the command's own output names the file that did not decode

#### Scenario: other git output that is not UTF-8 never escapes as a traceback
- **WHEN** git output the launch reads other than the diff holds bytes that
  are not UTF-8
- **THEN** the launch uses them in printable escaped form or refuses naming
  the command, and no UnicodeDecodeError escapes

#### Scenario: a path that does not decode is named in escaped form
- **WHEN** a reviewed file's path bytes are not UTF-8
- **THEN** the name that reaches the reviewer and the command's own output is
  an escaped printable form, not raw bytes and not a traceback
