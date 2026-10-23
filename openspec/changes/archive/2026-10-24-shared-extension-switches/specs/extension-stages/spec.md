# extension-stages Specification (delta)

## Purpose

The shared extension switches of ADR-0013 section E — decisions 16 and
17, with decision 6's read from the base and decision 7's no-silence
rule — over the file ADR-0022 section 7 shapes and ADR-0014's map
places at `.agentmarshal/switches.toml`. A shared extension is switched
off only by an operational CR; `stage run` reads the switches from the
merge base's tree and reports a switched-off extension instead of
running it, and `doctor` shows each switched-off extension from the
working tree. Opening the operational CR, the gate's operational lane,
personal switches and `status`'s half of decision 17 are later work,
not this capability.

## ADDED Requirements

### Requirement: `.agentmarshal/switches.toml` is parsed by one function

The shared switches file SHALL carry `format = 1` and a `[switches]`
table holding, per extension name, a table of `state` — `"on"` or
`"off"` — `task` — the operational CR that set the switch, matching
`CR-<n>` — and `reason`. `reason` SHALL be required when `state` is
`"off"` and SHALL be refused when `state` is `"on"`; present, it is at
most 1000 characters and passes the forgeable-text rule. Keys an entry
carries beyond those SHALL pass unread. One function SHALL parse the
file's bytes against the shared extension names the caller knows: text
that is not UTF-8 TOML, a missing `format`, an unknown `format`, a
`switches` that is not a table, an entry that is not a table, an entry
naming no shared extension, a `state` outside `"on"` and `"off"`, a
`task` that is not a `CR-<n>` identifier, or a `reason` outside its
rule SHALL each be refused naming the file and, where one exists, the
entry. The refusal SHALL carry the entry names the file declares where
they could be enumerated. A missing file SHALL mean every extension is
on.

#### Scenario: an off switch parses with its task and reason
- **WHEN** `switches.toml` holds `format = 1` and an entry
  `[switches.openspec]` with `state = "off"`, `task = "CR-214"` and a
  `reason`
- **THEN** the parse returns the extension's switch — `off`, `CR-214`
  and the reason

#### Scenario: a missing switches file means every extension is on
- **WHEN** the file does not exist
- **THEN** the read returns an empty set — every extension is on

#### Scenario: a file that is not TOML is refused naming it
- **WHEN** the file's text is not UTF-8 TOML
- **THEN** the parse is refused naming the file

#### Scenario: an unknown or missing format is refused naming the file
- **WHEN** the file declares no `format` or a `format` other than 1
- **THEN** the parse is refused naming the file

#### Scenario: an entry naming no shared extension is refused naming the file and the entry
- **WHEN** a `switches` entry names an extension the caller does not
  know
- **THEN** the parse is refused naming the file and the entry

#### Scenario: a switch entry outside its shape is refused naming the file and the entry
- **WHEN** an entry is not a table, has a `state` outside `"on"` and
  `"off"`, a `task` that is not `CR-<n>`, an `off` with no `reason`, an
  `on` carrying a `reason`, or a `reason` over 1000 characters or
  carrying a forgeable character
- **THEN** the parse is refused naming the file and the entry

### Requirement: `stage run` reads the switches from the base and reports a switched-off extension

`stage run` SHALL read `.agentmarshal/switches.toml` from the merge
base's tree — never the candidate's and never the working tree's —
parsed against every shared extension name the base's
`.agentmarshal/extensions/` enumerates, both forms. An entry at the
file's path that is not a file SHALL be the file's own malformation.
Each stage of a switched-off extension SHALL print `<name>: switched
off (<task>, <reason>)` as its one result line, the values escaped for
display, and SHALL NOT run: the extension is neither materialized nor
grant-checked for that stage. Its `extension-event` SHALL carry the
decision `switched-off` and a reason of `<task>, <reason>`. A
switched-off stage SHALL neither pause a `pre-gate-stop` nor warn a
`pre-gate-warn`. A switches file the parse refuses SHALL be reported on
one line on stderr naming the file and, where the parse reached one,
the entry; no stage of an extension the file names SHALL run — each
SHALL be `not run (shared switches file unreadable)` — and where the
file's entries cannot be enumerated at all, every stage SHALL be.

#### Scenario: a switched-off extension prints switched off (task, reason) and does not run
- **WHEN** the base's switches file switches an extension off
- **THEN** each of its matching stages prints `<name>: switched off
  (<task>, <reason>)` and the extension does not run

#### Scenario: the switches are read from the base commit, never the candidate or the working tree
- **WHEN** the candidate's tree or the working tree carries a different
  switches file — one switching the extension on, or off
- **THEN** the base's file decides: a base switch-off still reports
  `switched off`, a base all-on still runs

#### Scenario: a switched-off pre-gate-stop stage does not pause
- **WHEN** a `pre-gate-stop` extension is switched off
- **THEN** the command does not pause and exits 0

#### Scenario: every stage of a switched-off extension gets the switched-off line
- **WHEN** a switched-off extension declares two matching stages
- **THEN** each prints `switched off (<task>, <reason>)` — two result
  lines, no run

#### Scenario: a switched-off stage's event carries the switched-off decision, the task and the reason
- **WHEN** a switched-off stage's result is appended to the process log
- **THEN** the event carries decision `switched-off` and reason
  `<task>, <reason>`

#### Scenario: an extension switched on or with no entry runs
- **WHEN** the file switches one extension `on` and names another not
  at all
- **THEN** both run as before

#### Scenario: a malformed switches file is reported on one line and no stage of an extension it names runs
- **WHEN** the base's switches file parses but holds an entry outside
  its shape
- **THEN** the refusal is printed on one stderr line naming the file
  and the entry, every named extension's stages are `not run`, and an
  extension the file does not name still runs

#### Scenario: a switches file that cannot be read leaves every stage not run
- **WHEN** the base's switches file is not TOML at all
- **THEN** the refusal is printed on one stderr line and every stage is
  `not run (shared switches file unreadable)`

### Requirement: `doctor` shows each switched-off shared extension

`doctor` SHALL read `.agentmarshal/switches.toml` from the working
tree, parsed against the shared extension names the working tree
enumerates, and SHALL show each switched-off shared extension's line
carrying `switched off since <task> (<reason>)` — for the file form
and the directory form alike, and on the line of an extension whose
manifest cannot be read — every value from the file escaped on
display. A project without the file SHALL show nothing new: every
extension is on. A file the parse refuses SHALL be named on one
`switches: unavailable (<reason>)` line, never a check failure.

#### Scenario: doctor shows a switched-off extension with its task and reason
- **WHEN** the working tree's switches file switches an extension off
- **THEN** its line carries `switched off since <task> (<reason>)`

#### Scenario: a project without switches.toml shows nothing new
- **WHEN** the project has no `switches.toml`
- **THEN** the extensions section reads as before — every extension is
  on

#### Scenario: an extension switched on or with no entry shows no switch
- **WHEN** the file switches one extension `on` and names another not
  at all
- **THEN** neither line mentions the switch

#### Scenario: a file-form extension switched off is shown the same way
- **WHEN** the file switches off a `<name>.toml` extension
- **THEN** its line carries `switched off since <task> (<reason>)`

#### Scenario: a malformed switches file is named on one line and fails nothing
- **WHEN** the working tree's switches file is refused by the parse
- **THEN** one `switches: unavailable (<reason>)` line names it, and no
  check fails for it

#### Scenario: a value that could forge a line is escaped on display
- **WHEN** a switches entry's name carries a forgeable character and
  the refusal quotes it
- **THEN** the displayed line carries the escape, not the character
