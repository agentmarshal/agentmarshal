# Spec Delta

## ADDED Requirements

### Requirement: the outbox refuses a symbolic link in its path

Every `outbox` subcommand SHALL refuse — one line naming the path,
before creating or writing anything — when `.agentmarshal/upstream` or
a component between it and the project root is a symbolic link, so a
sidecar's outbox linked into its host never writes the host; `init`'s
outbox scaffold SHALL refuse the same.

#### Scenario: a linked outbox refuses a command before it writes
- **WHEN** `.agentmarshal/upstream` is a symbolic link
- **THEN** `outbox new`, `outbox check`, `outbox send` and `outbox
  status` each refuse with one line naming the link, and nothing is
  written or committed

#### Scenario: a linked .agentmarshal component refuses the command
- **WHEN** `.agentmarshal` itself is a symbolic link
- **THEN** the command refuses with one line naming that component

#### Scenario: init never scaffolds through a linked outbox
- **WHEN** `init` finds `.agentmarshal/upstream` a symbolic link
- **THEN** it writes nothing through the link and reports the refusal
  on one line naming the path

### Requirement: `outbox send` commits only the bytes it checked

`outbox send` SHALL refuse, naming the file, when the blob id a checked
file stages as — its path's attributes applied — differs from the blob
id of the bytes the check read, so a clean filter or end-of-line
conversion cannot commit content the scan never saw; the sent
manifest's update SHALL be held to the same rule.

#### Scenario: send refuses a draft a clean filter would transform
- **WHEN** a `.gitattributes` clean filter would rewrite a draft's
  bytes on staging
- **THEN** `outbox send` refuses naming the file and commits nothing

#### Scenario: send refuses when a filter would transform the sent manifest
- **WHEN** an attribute would rewrite the manifest content `send`
  stages under `SENT`
- **THEN** the send refuses naming `SENT` and stages nothing

### Requirement: `outbox status` escapes the names it prints

Every name `outbox status` prints SHALL be masked and written in
display-escaped printable form, exactly as `outbox check` names files,
so no printed name can add a line to the report.

#### Scenario: a control character in a file name is escaped in the report
- **WHEN** the outbox holds a file whose name carries a control
  character
- **THEN** `status` prints the name with the character as an escape,
  never the raw character
