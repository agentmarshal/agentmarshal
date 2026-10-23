# extension-stages Specification (delta)

## Purpose

The operational CR of ADR-0013 decisions 16 and 17 opened by one
command: `agentmarshal extension switch off <name> --reason <text>`
opens a task scoped to `.agentmarshal/switches.toml` alone and writes
the switch into the working tree for the task it opened — the file
CR-217's parser reads, in the shape ADR-0022 section 7 fixes. The
gate's operational lane that admits the diff is a parallel change;
switching back on, personal switches and `--skip-ext` are not this
capability.

## ADDED Requirements

### Requirement: `extension switch off` opens an operational task and writes the switch

`agentmarshal extension switch off <name> --reason <text>` SHALL open a
task through the journal's `open_task` — a contract whose title names
the extension, whose scope is exactly `[".agentmarshal/switches.toml"]`
and whose acceptance says the extension is switched off with the
reason — and SHALL write into the working tree's
`.agentmarshal/switches.toml` the entry `state = "off"`,
`task = <the opened task's id>` and `reason = <text>`, creating the
file with `format = 1` and a `[switches]` table when absent. The
command SHALL print the opened contract's and record's paths as `open`
does, then the switches file's path, and SHALL commit nothing.

#### Scenario: the opened contract names the extension, scopes the switches file and accepts the switch-off
- **WHEN** `extension switch off openspec --reason "…"` runs where
  `openspec` is a shared extension the working tree declares
- **THEN** the opened contract's title names `openspec`, its scope is
  exactly `[".agentmarshal/switches.toml"]` and its acceptance says
  `openspec` is switched off with the reason

#### Scenario: the switches entry is written for the opened task
- **WHEN** the command opens the task `CR-001`
- **THEN** the file's `[switches.openspec]` entry carries
  `state = "off"`, `task = "CR-001"` and the given `reason`

#### Scenario: a missing switches file is created with format and the switches table
- **WHEN** `.agentmarshal/switches.toml` does not exist
- **THEN** the command creates it carrying `format = 1`, a `[switches]`
  table and the off entry

#### Scenario: the paths are printed and nothing is committed
- **WHEN** the command succeeds
- **THEN** stdout carries the opened contract's path, the opened
  record's path and the switches file's path, and HEAD does not move

### Requirement: name, reason and the existing file are checked before the task is opened

The name SHALL be a shared extension the working tree declares — a
name `doctor` and `stage run` enumerate under
`.agentmarshal/extensions/`: a `<name>.toml` entry, a `<name>/`
directory, or a link entry kept under the name it carries — whether
or not the manifest under it can be read, since a broken extension
must stay switchable — and the names an existing
`.agentmarshal/switches.toml`'s entries are checked against SHALL be
that same set. The reason SHALL pass the parser's own rule:
non-empty, at most 1000 characters, the forgeable-text rule. An
existing `.agentmarshal/switches.toml` SHALL be parsed by the shared
parser before the task is opened: a file the parse refuses SHALL be
refused naming it, and an extension whose entry is already `off`
SHALL be refused naming the task that switched it off. Every refusal
before the task is opened SHALL write nothing — no task is opened and
no file changes.

#### Scenario: a name the working tree does not declare is refused before anything is written
- **WHEN** `extension switch off` names an extension
  `.agentmarshal/extensions/` does not declare
- **THEN** it is refused saying so, and no task is opened and no
  switches file is written

#### Scenario: a reason outside its rule is refused before anything is written
- **WHEN** `--reason` is empty, over 1000 characters or carries a
  forgeable character
- **THEN** the command refuses naming why, and no task is opened and no
  file changes

#### Scenario: a malformed switches file is refused naming it and nothing is written
- **WHEN** the working tree's `switches.toml` is refused by the parse
- **THEN** the refusal names the file, and no task is opened and the
  file is unchanged

#### Scenario: an extension already switched off is refused naming the task that switched it off
- **WHEN** the file's entry for the extension is already `off`
- **THEN** the refusal names the task that switched it off, and no task
  is opened and the file is unchanged

#### Scenario: a file-form extension is a shared extension the command switches off
- **WHEN** the working tree declares the extension as `<name>.toml`
  alone
- **THEN** the command opens the task and writes the switch the same
  way

#### Scenario: a declared extension whose manifest cannot be read is switched off
- **WHEN** the name is enumerated under `.agentmarshal/extensions/`
  but its manifest cannot be read — a directory form whose declared
  `bin/` file is missing, or a name claimed in both forms
- **THEN** the command opens the task and writes the switch the same
  way

#### Scenario: a link entry's name is a shared extension the command switches off
- **WHEN** the working tree declares the extension through a
  symbolic-link entry under `.agentmarshal/extensions/` — the
  directory form or the file form linked
- **THEN** the command opens the task and writes the switch the same
  way

#### Scenario: a file whose other entry names a linked extension is accepted
- **WHEN** an existing `.agentmarshal/switches.toml` carries an entry
  for an extension the working tree declares through a link
- **THEN** the parse accepts the file and the command proceeds — the
  names the entries are checked against are the enumerated set

### Requirement: the switches file keeps its text and is replaced atomically

The command SHALL keep the existing file's text and change only what
the switch needs: an extension already carrying an `on` entry SHALL
have the switch's own key/value lines inside that entry's
`[switches.<name>]` table replaced by the off entry's — the header,
every other key the entry carries and the file's other content kept —
and any other extension SHALL gain a new `[switches.<name>]` table
appended after the file's existing content. An `on` entry the command
cannot locate and bound on its own lines — a header or key spelled
with escapes or in any form other than a plain bare, basic or literal
key, a header-less form such as an inline table or dotted keys, a
multi-line value inside it holding a line that reads as a table
header — SHALL be refused before any task is opened, on one line
naming the file and saying the entry cannot be rewritten by this
command and must be switched off by editing the file in an
operational task; nothing is written. The `reason` SHALL be written
as a TOML basic string with every character that needs escaping
escaped. The whole new text SHALL be parsed by the shared parser
before the file is replaced — a text the parse refuses writes
nothing — and the file SHALL be replaced atomically: a temporary file
in `.agentmarshal/` renamed over it, an existing file's permission
bits kept and a created file's the usual creation mode masked by the
umask. A failure after the task is opened SHALL be reported on one
line naming the opened task and SHALL exit non-zero.

#### Scenario: an existing on entry's table is replaced and the file's other content is kept
- **WHEN** the file switches the extension `on` and carries other
  entries and comments
- **THEN** the extension's table is replaced by the off entry — the
  other entries, the comments and the file's order are as they were

#### Scenario: an on entry's other keys are kept through the rewrite
- **WHEN** the `on` entry carries a key beyond `state`, `task` and
  `reason` — a multi-line value whose `[`-led continuation lines are
  not table headers
- **THEN** the off entry is written inside the table and the other
  key's value is as it was

#### Scenario: an on entry the command cannot locate and bound on its own lines is refused before any task is opened
- **WHEN** an `on` entry is carried in a form the command cannot
  locate and bound on its own lines — a header or key spelled with
  escapes, a header-less form, or a multi-line value inside it
  holding a line that reads as a table header, like a last array
  element `["x"]` on its own line
- **THEN** the command refuses naming the file and saying the entry
  cannot be rewritten by this command and must be switched off by
  editing the file in an operational task, no task is opened and
  nothing is written

#### Scenario: a new entry is appended after the file's existing content
- **WHEN** the file switches another extension `on` and names this one
  not at all
- **THEN** this extension's `[switches.<name>]` table is appended and
  the file's existing content is unchanged ahead of it

#### Scenario: the new text is parsed back before it replaces the file
- **WHEN** the rewritten text fails the shared parser
- **THEN** nothing is written, and the failure is reported on one line
  naming the opened task with a non-zero exit

#### Scenario: the file is replaced by a temporary file renamed in the same directory
- **WHEN** the command writes the switches file
- **THEN** the new text is staged in a temporary file inside
  `.agentmarshal/` and renamed over the file — a reader never meets a
  half-written file

#### Scenario: a failure after the task is opened names the task on one line and exits non-zero
- **WHEN** the task opened but the switches file could not be written
- **THEN** the command reports the failure on one line naming the
  opened task and exits non-zero

### Requirement: `switch` is a group under `extension` and a sidecar opens no operational task

The `switch` group SHALL be registered under the existing `extension`
group with the `off` subcommand taking `off <name> --reason <text>`;
`extension trust`, `untrust` and `list` SHALL be unchanged, and no
other command changes. In a sidecar the command SHALL refuse with a
line saying operational tasks are not available in a sidecar, writing
nothing. Every value the command shows SHALL be escaped on display.

#### Scenario: the extension group takes switch off with a name and a reason
- **WHEN** the command-line parser is built
- **THEN** `agentmarshal extension switch off <name> --reason <text>`
  parses, and an unknown `switch` subcommand is refused

#### Scenario: a sidecar refuses saying operational tasks are not available
- **WHEN** `extension switch off` runs where the journal placement is a
  sidecar
- **THEN** it refuses with a line saying operational tasks are not
  available in a sidecar, and no task is opened and no file is written

#### Scenario: a value that could forge a line is escaped on display
- **WHEN** a refusal quotes a value carrying a forgeable character — a
  switches entry's name the parse refused
- **THEN** the displayed line carries the escape, not the character
