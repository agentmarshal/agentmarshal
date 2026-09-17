## ADDED Requirements

### Requirement: The reviewer command's contract is documented where it is configured
The documentation that describes `AGENTMARSHAL_REVIEWER_CMD` SHALL state that
the command runs with its working directory set to a metadata-free snapshot of
the reviewed commit, that a relative path in the command resolves inside that
snapshot rather than against the operator's checkout, and what the prompt-file
placeholder contains. It SHALL also state that the snapshot bounds where the
command starts and not what the process may read, and that confining the latter
belongs to the adapter.

#### Scenario: an operator learns the contract without reading the launcher
- **WHEN** an operator configures a reviewer command from the documentation
- **THEN** the documentation states the working directory, the resolution of
  relative paths, the prompt-file placeholder, and the adapter's responsibility
  for what the command may read

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
