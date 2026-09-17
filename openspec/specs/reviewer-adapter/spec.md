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
When the configured reviewer command exits zero, whatever it wrote to its error
stream SHALL be kept where the operator can read it, and the command SHALL say
where. A command that wrote nothing there SHALL produce no such message.

#### Scenario: a warning from a wrapper reaches the operator
- **WHEN** the reviewer command exits zero having written to its error stream
- **THEN** the review is recorded as it is today, and the operator is told
  where that output was kept

#### Scenario: a silent command says nothing about its silence
- **WHEN** the reviewer command exits zero having written nothing to its error
  stream
- **THEN** the output is what it is today, with no mention of a kept file
