# extension-stages Specification (delta)

## Purpose

`status`'s half of ADR-0013 decision 17 — "switched off since CR
so-and-so, reason", the line `doctor` already shows — printed beside
the paths ADR-0014 decision 13 puts on stderr, and the working tree's
shared extension names enumerated by the one function
`switches.shared_extension_names` carries.

## ADDED Requirements

### Requirement: `status` names each switched-off shared extension

`agentmarshal status` — the listing and the view of one task alike —
SHALL print on stderr, right after the lines naming where the journal,
the process log and the local state live, one line per shared
extension the working tree's `.agentmarshal/switches.toml` switches
off: `switched off: <name> since <task> (<reason>)` — ADR-0013
decision 17's "switched off since CR so-and-so, reason" — in the
enumeration's sorted order, every value the file carries escaped for
display. The file SHALL be the one `doctor` reads, read through the
same `read_switches` function and parsed against the shared extension
names `switches.shared_extension_names` enumerates for the working
tree's `.agentmarshal/extensions/`. The lines SHALL be owed in every
case where the paths printed — an empty journal's `No tasks.` and a
task lookup's refusal alike — printed before anything that can return
early. stdout SHALL be unchanged byte for byte. A project without the
file, or whose file switches no extension off, SHALL print nothing new
on stderr. A file the parse refuses SHALL be named on one stderr line
— `switches: unavailable (<reason>)`, the wording `doctor` reports the
same refusal with — and SHALL change neither `status`'s exit status
nor its stdout.

#### Scenario: the listing names each switched-off extension after the paths
- **WHEN** `status` runs in a project whose switches file switches a
  shared extension off
- **THEN** stderr carries `switched off: <name> since <task>
  (<reason>)` after the lines naming where the journal, the process
  log and the local state live

#### Scenario: the view of one task names each switched-off extension after the paths
- **WHEN** `status <task>` runs where the file switches a shared
  extension off
- **THEN** stderr carries the `switched off:` line after the paths

#### Scenario: the lines are owed wherever the paths printed — an empty journal and a failed lookup alike
- **WHEN** `status` lists an empty journal, or `status <task>` names a
  task the journal does not hold, where the file switches an extension
  off
- **THEN** the `switched off:` line still prints after the paths —
  before `No tasks.`, before the lookup's refusal

#### Scenario: a project without the file prints nothing new
- **WHEN** `status` runs — either form — where no `switches.toml`
  exists
- **THEN** stderr carries no `switched off:` line and nothing else new

#### Scenario: an extension switched on or with no entry prints nothing new
- **WHEN** the file switches one extension `on` and names another not
  at all
- **THEN** neither gains a line and stderr reads as before

#### Scenario: a file the parse refuses is named on one line and changes neither the exit nor stdout
- **WHEN** the working tree's `switches.toml` is refused by the parse
- **THEN** one `switches: unavailable (<reason>)` line names it after
  the paths, and `status`'s exit status and stdout are unchanged

#### Scenario: a value the file carries is escaped on display
- **WHEN** a switched-off entry's name carries a forgeable character
- **THEN** the displayed line carries the escape, not the character

#### Scenario: stdout stays byte for byte what it was
- **WHEN** `status` runs — either form — with or without a switches
  file
- **THEN** stdout is byte for byte what the command printed before the
  lines were added

### Requirement: the working tree's shared extension names are enumerated by one function

The set a shared extension name belongs to — the names the working
tree's `.agentmarshal/extensions/` declares — SHALL be enumerated by
one function, `switches.shared_extension_names`: a `<name>.toml` entry
the file form, a `<name>/` entry the directory form, a symbolic-link
entry kept under the name it carries with `.toml` removed, a name
found in more than one form enumerated once, an entry that is none of
these not an extension, and a managed path that is no directory
enumerating no names — whether or not the manifest under a name reads,
so a broken extension stays switchable. `doctor` SHALL enumerate
through it, its output unchanged, and `status`'s switches read SHALL
check the file's entries against the names it returns.

#### Scenario: doctor enumerates through the shared function
- **WHEN** `doctor` lists the working tree's extensions
- **THEN** the names come from `shared_extension_names` — the file
  form, the directory form and a link's name alike — and its output is
  unchanged

#### Scenario: a name declared only through a link is a shared extension the file can switch off
- **WHEN** `status` runs where an extension exists only as a
  symbolic-link entry and the file switches it off
- **THEN** its `switched off:` line prints
