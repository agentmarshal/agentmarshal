# extension-trust Specification

## Purpose
Local run grants for shared extensions (ADR-0013 decision 14): a grant
approves the exact contents of an extension's directory on one clone — the
manifest, `bin/`, the lock and everything else the directory holds —
recorded as `trust.toml` in the clone's local state (ADR-0014's map), a
name to the directory hash granted, who granted it and when (ADR-0022
section 7), with each file's own hash kept beside it so a later check can
name `changed after approval: <file>`. The grants are kept by
`agentmarshal extension trust | untrust | list`. A shared extension with a
command runs on a workstation only under a valid grant and the core
recomputes the hash before each run — that check, and running extensions
at all, are later tasks; this capability is the grants themselves. The
file is local state: never committed, never read by the gate, and no
defence against a process running with the user's rights (ADR-0013
decision 15).

## Requirements

### Requirement: `extension trust` records a grant over the directory's contents

`agentmarshal extension trust <name>` SHALL compute the sha256 of each
regular file under `.agentmarshal/extensions/<name>/` of the working tree —
the path relative to the directory, sorted — and one directory hash over
that sorted list of relative path and file hash, and SHALL record them in
the clone's local state `trust.toml` (`format = 1`), keyed by the
extension's name: the directory hash, each file's hash, who granted it as
`resolve_recorded_by` resolves the identity, and when as a UTC ISO-8601
time. Granting a name that already holds a grant SHALL replace the earlier
grant. When no identity resolves the command SHALL refuse naming why and
write nothing.

#### Scenario: a grant records the directory hash, every file's hash, the granter and when
- **WHEN** `extension trust openspec` runs against a directory-form
  extension
- **THEN** `trust.toml` records under `openspec` the directory hash, the
  sha256 of every regular file by its relative path, the resolved granter
  and a UTC ISO-8601 time, at `format = 1`

#### Scenario: the directory hash covers the whole directory
- **WHEN** the extension's directory holds a manifest, files under `bin/`
  and `lock/` and a file in a nested subdirectory
- **THEN** every regular file's hash enters the grant and the directory
  hash changes when any one of them changes

#### Scenario: a re-grant replaces the earlier grant
- **WHEN** `extension trust openspec` runs twice with changed contents
- **THEN** the grant records the new hashes and granter, and no second
  entry for `openspec` remains

#### Scenario: no resolvable granter refuses, writing nothing
- **WHEN** `extension trust` runs where `resolve_recorded_by` resolves no
  identity
- **THEN** it refuses naming why and `trust.toml` and the process log are
  untouched

### Requirement: `trust` refuses an extension it cannot approve

`extension trust` SHALL refuse the grant — writing nothing — naming what
it found: a symbolic link inside the extension's directory, at any depth
and dangling or not, naming its relative path; a file that is not a
regular file, naming its relative path; a symbolic link for the
extension's `<name>` directory itself, or at `.agentmarshal` or
`extensions/`, refused as a link; a `<name>.toml` file-form extension with
no directory, naming why; a `<name>.toml` and a `<name>/` directory for
one name, naming both paths; a `<name>` that is not a directory, naming
it; and a missing extension, naming why.

#### Scenario: a symbolic link inside the directory refuses the grant naming it
- **WHEN** a file or a directory inside the extension's directory is a
  symbolic link
- **THEN** `extension trust` refuses naming the link's relative path and
  writes nothing

#### Scenario: a non-regular file inside the directory refuses the grant naming it
- **WHEN** the extension's directory holds a file that is not a regular
  file
- **THEN** `extension trust` refuses naming its relative path and writes
  nothing

#### Scenario: a missing extension refuses the grant naming why
- **WHEN** neither `.agentmarshal/extensions/<name>/` nor
  `.agentmarshal/extensions/<name>.toml` exists
- **THEN** `extension trust` refuses saying the extension is missing

#### Scenario: a file-form extension refuses the grant naming why
- **WHEN** `<name>` exists only as `.agentmarshal/extensions/<name>.toml`
- **THEN** `extension trust` refuses saying a file-form extension has no
  directory to grant

#### Scenario: an extension in both forms refuses the grant naming both paths
- **WHEN** both `.agentmarshal/extensions/<name>.toml` and
  `.agentmarshal/extensions/<name>/` exist
- **THEN** `extension trust` refuses naming both paths

#### Scenario: a symlinked extension directory refuses the grant as a link
- **WHEN** `.agentmarshal/extensions/<name>` is a symbolic link —
  dangling or not
- **THEN** `extension trust` refuses it as a link and writes nothing

#### Scenario: a refused grant writes nothing
- **WHEN** `extension trust` refuses
- **THEN** no `trust.toml` is created, no `trust-changed` event is
  appended and the journal is untouched

### Requirement: `extension untrust` removes the grant

`agentmarshal extension untrust <name>` SHALL remove the grant recorded
for `<name>` and leave every other grant; it SHALL refuse — writing
nothing — a name that holds no grant, naming it. The extension's
directory is not consulted: a grant SHALL be removable when the
extension is gone.

#### Scenario: untrust removes the named grant and keeps the rest
- **WHEN** `extension untrust openspec` runs against a recorded grant
- **THEN** the grant for `openspec` is gone and other grants remain

#### Scenario: untrust on a name with no grant refuses naming it
- **WHEN** `extension untrust` names an extension with no recorded grant
- **THEN** it refuses naming the extension and writes nothing

#### Scenario: untrust works when the extension's directory is gone
- **WHEN** a recorded grant's extension directory no longer exists
- **THEN** `extension untrust` removes the grant

### Requirement: `extension list` reports each directory-form extension's grant state and never writes

`agentmarshal extension list` SHALL print one line for each shared
extension in directory form — each real directory under
`.agentmarshal/extensions/` — giving its state: `granted` while the
recorded per-file hashes match a fresh computation; `not granted` while
no grant is recorded; or `changed after approval:` naming the first
changed, added or removed file by sorted path with its kind, recomputing
the hashes. A file-form extension SHALL NOT be listed. An entry that is a
symbolic link, and a directory whose contents cannot be hashed, SHALL be
named rather than hashed through. With no directory-form extensions the
command SHALL print nothing. The command SHALL NOT write: no `trust.toml`,
no process-log event, no local state directory, no journal write.

#### Scenario: a granted extension lists as granted
- **WHEN** `extension list` runs where `openspec` holds a grant and its
  contents are unchanged
- **THEN** it prints `openspec` granted

#### Scenario: an extension with no grant lists as not granted
- **WHEN** `extension list` runs where `openspec` holds no grant
- **THEN** it prints `openspec` not granted

#### Scenario: a changed file lists as changed after approval naming it
- **WHEN** a granted extension's file changed since the grant
- **THEN** `extension list` prints `openspec` changed after approval
  naming the file and `changed`

#### Scenario: an added file lists as changed after approval naming it
- **WHEN** a granted extension gained a file since the grant
- **THEN** `extension list` prints `openspec` changed after approval
  naming the file and `added`

#### Scenario: a removed file lists as changed after approval naming it
- **WHEN** a granted extension lost a file since the grant
- **THEN** `extension list` prints `openspec` changed after approval
  naming the file and `removed`

#### Scenario: the first differing file in sorted order is named
- **WHEN** several of a granted extension's files changed, were added and
  were removed
- **THEN** `extension list` names the first differing path in sorted
  order

#### Scenario: file-form extensions are not listed
- **WHEN** `.agentmarshal/extensions/` holds only `<name>.toml` files
- **THEN** `extension list` prints no line for them

#### Scenario: a directory that cannot be hashed is named, not hashed
- **WHEN** an extension's directory holds a symbolic link or a
  non-regular file
- **THEN** `extension list` names the extension and why it cannot be
  hashed rather than following the link

#### Scenario: a symlinked extension directory is named, not hashed
- **WHEN** an entry under `.agentmarshal/extensions/` is a symbolic link
- **THEN** `extension list` names it rather than hashing through it

#### Scenario: no directory-form extensions prints nothing
- **WHEN** `extension list` runs where no shared extension in directory
  form exists
- **THEN** it prints nothing

#### Scenario: list never writes
- **WHEN** `extension list` runs
- **THEN** no `trust.toml` is created, no local state directory is
  created, no event is appended and the journal is untouched

### Requirement: `trust.toml` is written atomically under the clone's local state and read fail-closed

`trust.toml` SHALL live where `localstate.py` resolves the local state —
`.git/agentmarshal/trust.toml`, shared by every worktree of the clone,
never committed — and SHALL be written atomically: to a temporary file in
the same directory renamed into place, so a reader never meets a
half-written file and a failed write leaves the previous file whole. A
file that does not parse, a `format` that is missing or not `1`, and a
grant missing a field or carrying a field of the wrong type SHALL each
refuse every subcommand — `trust`, `untrust` and `list` — naming the
file. A missing `trust.toml` SHALL read as no grants.

#### Scenario: trust.toml is written under the clone's local state
- **WHEN** `extension trust` records a grant
- **THEN** the file sits at `.git/agentmarshal/trust.toml` — under the git
  common directory, not the working tree — and nothing is committed

#### Scenario: trust.toml is replaced atomically
- **WHEN** writing `trust.toml` fails mid-write
- **THEN** the file under its final name is either the previous file or
  the complete new one — never half-written

#### Scenario: a malformed trust.toml refuses every subcommand naming the file
- **WHEN** `trust.toml` does not parse or a grant lacks a field or
  carries a field of the wrong type
- **THEN** `trust`, `untrust` and `list` each refuse naming the file

#### Scenario: an unknown-format trust.toml refuses every subcommand naming the file
- **WHEN** `trust.toml` declares a `format` other than `1` or none
- **THEN** `trust`, `untrust` and `list` each refuse naming the file

#### Scenario: a missing trust.toml reads as no grants
- **WHEN** `trust.toml` does not exist
- **THEN** every extension reads as not granted

### Requirement: a grant and a removal each append one `trust-changed` event

Each grant and each removal SHALL append one `trust-changed` event to the
process log (ADR-0022 section 7) carrying the extension's name, the
action — `granted` or `removed` — and the directory hash: the hash newly
computed for a grant, the hash the removed grant held for a removal. The
actor SHALL ride along when an identity resolves. A refused command
SHALL append no event. The journal SHALL NOT be written.

#### Scenario: trust appends one trust-changed event
- **WHEN** `extension trust openspec` records a grant
- **THEN** one `trust-changed` event carries `openspec`, `granted`, the
  new directory hash and the granter

#### Scenario: untrust appends one trust-changed event
- **WHEN** `extension untrust openspec` removes a grant
- **THEN** one `trust-changed` event carries `openspec`, `removed` and the
  directory hash the grant held

#### Scenario: a refused command appends no event
- **WHEN** `extension trust` or `extension untrust` refuses
- **THEN** no `trust-changed` event is appended

### Requirement: the commands never run an extension and never write the journal

No subcommand SHALL execute anything the extension's directory holds, and
none SHALL write to the journal.

#### Scenario: no file in the extension's directory is run
- **WHEN** an extension's `bin/` holds an executable file and any of
  `trust`, `untrust`, `list` runs
- **THEN** the file is hashed, never executed — no side effect of running
  it appears

#### Scenario: the journal is untouched
- **WHEN** any of `trust`, `untrust`, `list` runs
- **THEN** `.agentmarshal/journal/` is unchanged

### Requirement: the command group is registered like `step`

The `extension` group SHALL be registered from its own module's
`register`/`run` pair on the command-line parser, the way the `step`
group is, with `trust`, `untrust` and `list` subcommands.

#### Scenario: the extension group takes trust, untrust and list
- **WHEN** the command-line parser is built
- **THEN** `agentmarshal extension trust`, `agentmarshal extension
  untrust` and `agentmarshal extension list` each parse, and an unknown
  subcommand is refused
