# reviewer-adapter Specification

## Purpose
What an operator can rely on about the command that produces a verdict: where
it starts, what it is handed, what it must not assume, and which part of
bounding it belongs to the adapter rather than to this tool. Also how to
exercise that command before it decides anything.

## Requirements

### Requirement: The reviewer command's contract is documented where it is configured
The documentation that describes `AGENTMARSHAL_REVIEWER_CMD` SHALL state that
the command runs with its working directory set to a metadata-free snapshot of
the reviewed commit, or — when the review binds to a finding — to a snapshot of
that finding's verified artifacts; that a relative path in the command resolves
inside that snapshot rather than against the operator's checkout; and what the
prompt-file placeholder contains. It SHALL state which subject the verdict must
name for each binding. It SHALL also state that the snapshot bounds where the
command starts and not what the process may read, and that confining the latter
belongs to the adapter.

#### Scenario: an operator learns the contract without reading the launcher
- **WHEN** an operator configures a reviewer command from the documentation
- **THEN** the documentation states the working directory, the resolution of
  relative paths, the prompt-file placeholder, and the adapter's responsibility
  for what the command may read

#### Scenario: the documented contract covers both bindings
- **WHEN** an operator reads that documentation to configure one command for
  both kinds of review
- **THEN** it states what the command is handed for a commit review and for a
  finding review, and which subject each verdict must name

### Requirement: A rejected placeholder is named
When the configured command contains a placeholder the launcher does not
support, the refusal SHALL name the offending token.

#### Scenario: an unsupported placeholder is named in the refusal
- **WHEN** the configured command contains a placeholder that is not supported
- **THEN** the launcher refuses and the message contains the token it rejected

### Requirement: The configured command can be exercised without recording
`agentmarshal review --dry-run` SHALL launch the configured command on a
synthetic prompt, report whether its output yields a parseable verdict, and
write no record, no artifact and no file into the journal.

#### Scenario: a working command is reported as working
- **WHEN** `agentmarshal review --dry-run` runs a command whose output carries a
  well-formed verdict block
- **THEN** it reports success and the journal is unchanged

#### Scenario: a command that yields no verdict is reported as such
- **WHEN** the configured command produces output with no parseable verdict
- **THEN** the dry run reports the failure and names what it could not parse,
  and the journal is unchanged

#### Scenario: a dry run needs no task and no commit
- **WHEN** `agentmarshal review --dry-run` is given no task and no commit
- **THEN** it runs, because it judges the command rather than any work

### Requirement: The reviewer command's diagnostics survive a successful run
When the configured reviewer command exits zero, whatever it wrote to its
error stream SHALL be kept byte for byte in a file under the local state's
process-log area of the repository that holds the journal — at every capture
level — a `review-diagnostics` event carrying the file's path and its sha256
SHALL be appended to the process log, and the command SHALL say where. When
the local state cannot be used, the output SHALL be kept in a local temporary
file instead, and the command SHALL say why. A command that wrote nothing
there SHALL produce no such message.

#### Scenario: a warning from a wrapper reaches the operator
- **WHEN** the reviewer command exits zero having written to its error stream
- **THEN** the review is recorded as it is today, the output is kept under
  the clone's local state and announced by a `review-diagnostics` event, and
  the operator is told where it was kept

#### Scenario: a silent command says nothing about its silence
- **WHEN** the reviewer command exits zero having written nothing to its
  error stream
- **THEN** the output is what it is today, with no mention of a kept file

#### Scenario: diagnostics are kept at every capture level
- **WHEN** the reviewer command exits zero having written to its error stream
  and the capture level for reviews is `commit`, `hash` or `off`
- **THEN** the output is kept in a file under the clone's local state and a
  `review-diagnostics` event is appended to the process log, whatever the
  level does with the prose

#### Scenario: diagnostics fall back to a temporary file when the local state cannot be used
- **WHEN** the reviewer command exits zero having written to its error stream
  and the clone's local state cannot be used
- **THEN** the output is kept in a local temporary file as before this
  change, and the command says why the local state could not be used

### Requirement: A diff that is not wholly UTF-8 still reaches the reviewer, per file
A commit review SHALL decode the merge-base diff one file section at a time,
through the same per-file decode the leak scan uses. A file whose section
does not decode as UTF-8 SHALL NOT keep the review from launching, nor keep
any other file's diff from reaching the reviewer. Each file that did not
decode SHALL be named — in what the reviewer is given and in the command's
own output — and its section SHALL still be shown with its unreadable bytes
marked, never passed over in silence. That includes a file whose undecodable
bytes sit only in lines the commit removed or kept as context: the reviewer
is shown those lines too, so the loss is named the same way.

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

#### Scenario: a file that lost bytes outside its added lines is still named
- **WHEN** a reviewed diff holds a file whose undecodable bytes sit only in
  removed or context lines
- **THEN** the file is named in the prompt and in the command's own output,
  and its section is still shown with the unreadable bytes marked

#### Scenario: other git output that is not UTF-8 never escapes as a traceback
- **WHEN** git output the launch reads other than the diff holds bytes that
  are not UTF-8
- **THEN** the launch uses them in printable escaped form or refuses naming
  the command, and no UnicodeDecodeError escapes

#### Scenario: a path that does not decode is named in escaped form
- **WHEN** a reviewed file's path bytes are not UTF-8
- **THEN** the name that reaches the reviewer and the command's own output is
  an escaped printable form, not raw bytes and not a traceback
