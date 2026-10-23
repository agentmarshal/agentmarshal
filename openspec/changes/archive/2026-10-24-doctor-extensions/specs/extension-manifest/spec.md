## ADDED Requirements

### Requirement: `doctor` prints an extensions section

`agentmarshal doctor` SHALL print — on stderr, with the report the
paths and the overdue-step lines belong to, so the check report on
stdout keeps its shape — one section listing each shared extension
found under `.agentmarshal/extensions/` of the journal repository's
working tree, the tree `extension list` reports on. An extension is
found at each `<name>.toml` entry — the file form — and at each
`<name>/` entry — the directory form (ADR-0013 decision 9); a
symbolic-link entry under either spelling is found under the name it
carries, so the manifest reader's own refusal reports it, and a name
present in both forms is listed once. One line SHALL print per
extension in the entries' sorted order, carrying the extension's name,
its form, its manifest's declared schema, its declared stages with
their modes and its declared `ext` kinds. Every line SHALL be escaped
like other displayed text.

#### Scenario: a file-form extension is listed with its form and schema
- **WHEN** `.agentmarshal/extensions/` holds `declared.toml`, a
  schema-1 manifest
- **THEN** the section prints one line naming `declared`, the file
  form and manifest schema 1

#### Scenario: a directory-form extension is listed with its stages' modes and declared kinds
- **WHEN** `.agentmarshal/extensions/openspec/` holds a schema-2
  `manifest.toml` declaring a `pre-gate-stop` stage and the kind
  `openspec/change-archived@1`
- **THEN** the section prints one line naming `openspec`, the
  directory form, manifest schema 2, the `pre-gate-stop` mode and the
  declared kind

#### Scenario: extensions are listed in sorted order
- **WHEN** `.agentmarshal/extensions/` holds several extensions in
  either form
- **THEN** their section lines print in the entries' sorted order

#### Scenario: a name held in both forms is listed once with the reader's refusal
- **WHEN** `.agentmarshal/extensions/` holds both `openspec.toml` and
  `openspec/manifest.toml`
- **THEN** one section line names `openspec` with the refusal that
  names both paths

#### Scenario: the section prints on stderr, escaped
- **WHEN** `doctor` runs in a project holding an extension whose
  listing carries a character the forgeable-text rule refuses
- **THEN** the value prints escaped, and nothing of the section
  reaches stdout

### Requirement: the section reports a directory-form extension's grant state as `extension list` computes it

For a directory-form extension the section line SHALL carry this
clone's local grant state — by the same computation `extension list`
reports, from the same `trust.toml` under the clone's local state and
a fresh hash of the directory's contents — reading `granted`,
`not granted`, or `changed after approval: <file>` with its kind, the
first differing file in sorted order. A grant state SHALL be
information only: it never changes `doctor`'s verdict or exit status,
and a missing grant is no failure. A symbolic-link `<name>` SHALL be
named, never hashed through, and a directory that cannot be hashed
SHALL carry the reason where the grant state would stand — the
treatment `extension list` gives both. When the clone's local state
did not resolve or the grants file cannot be read, the grant position
SHALL say so with the reason rather than fail the run.

#### Scenario: a granted extension reports granted
- **WHEN** `openspec` holds a grant and its contents are unchanged
- **THEN** its section line reports `grant: granted`

#### Scenario: an extension with no grant reports not granted
- **WHEN** `openspec` holds no grant
- **THEN** its section line reports `grant: not granted`

#### Scenario: a file changed after approval is named with its kind
- **WHEN** a granted extension's file changed, was added or was
  removed since the grant
- **THEN** the section line reports `changed after approval:` naming
  the first differing file in sorted order and its kind

#### Scenario: a grant state never changes doctor's verdict
- **WHEN** a directory-form extension holds no grant, or its contents
  changed after approval, and every check passes
- **THEN** `doctor` exits zero

#### Scenario: a symbolic-link extension directory is named, not hashed through
- **WHEN** an entry under `.agentmarshal/extensions/` is a symbolic
  link
- **THEN** the section names it and computes no grant state for it

#### Scenario: a directory that cannot be hashed carries the reason in its grant position
- **WHEN** an extension's directory holds a symbolic link or a
  non-regular file
- **THEN** the section line names the extension with the reason where
  the grant state would stand, rather than hashing through it

#### Scenario: a grants file or local state that cannot be read is named, not failed
- **WHEN** `trust.toml` is malformed, or the clone's local state did
  not resolve
- **THEN** a directory-form extension's grant position says the state
  is unavailable with the reason, and `doctor` does not fail for it

### Requirement: an unreadable manifest is reported the way doctor reports a malformed setting

An extension whose manifest cannot be read or validated — malformed
TOML, a field refusal, a `<name>/` directory holding no
`manifest.toml`, a name held in both forms, a link at a manifest path
or at the extension's directory — SHALL fail a check of its own,
`extension manifest <name>`, naming the reason, the way a malformed
project setting fails its own check: the failure counts in the
verdict and in the exit status, and it stops neither the other checks
nor the rest of the section. The same extension SHALL be named with
the reason on its one section line. When the listing itself cannot be
produced — `.agentmarshal` or `extensions/` a link, or a directory
that cannot be listed — one `extension manifests` check SHALL fail
naming the reason and the section SHALL mark the listing unavailable;
when the project itself cannot be found, the section SHALL mark
itself unavailable with the reason, as the paths do.

#### Scenario: an unreadable manifest fails a check of its own naming the reason
- **WHEN** `doctor` runs where `openspec`'s manifest cannot be read
  or validated
- **THEN** the check `extension manifest openspec` fails naming the
  reason, counting in the verdict and the exit status the way a
  malformed project setting's check does

#### Scenario: an unreadable manifest is named on one section line and stops nothing else
- **WHEN** `doctor` runs where one extension's manifest cannot be
  read and another's can
- **THEN** the section names the unreadable one with the reason on
  one line, the readable extension's line still prints and the other
  checks still run

#### Scenario: a discovered directory without a manifest is reported missing
- **WHEN** `.agentmarshal/extensions/openspec/` exists but holds no
  `manifest.toml`
- **THEN** the `extension manifest openspec` check fails with the
  missing-manifest report, and the section names it

#### Scenario: a listing that cannot be produced fails one check naming the reason
- **WHEN** `.agentmarshal/extensions/` is a symbolic link or cannot
  be listed
- **THEN** one `extension manifests` check fails naming the reason
  and the section marks the listing unavailable

#### Scenario: a project that cannot be found marks the section unavailable
- **WHEN** `doctor` runs where no project resolves
- **THEN** the section marks itself unavailable with the reason, as
  the paths do

### Requirement: a project without extensions gets one line and unchanged output

When the journal repository's working tree holds no
`.agentmarshal/extensions/` directory, or none that lists an
extension, the section SHALL print one line saying there are no
extensions, and the rest of `doctor`'s output SHALL be what it is
without the section: the same checks, the same verdict.

#### Scenario: no extensions directory prints one line saying there are no extensions
- **WHEN** `doctor` runs in a project with no
  `.agentmarshal/extensions/` directory
- **THEN** the section prints one line saying there are no extensions

#### Scenario: doctor's other output is unchanged without extensions
- **WHEN** `doctor` runs in a project with no extensions
- **THEN** the check report and the verdict print as they would
  without the section

### Requirement: the listing runs nothing an extension declares and writes nothing

The section and the manifest checks SHALL NOT execute anything an
extension declares — no `[[stage]]` `command` — and SHALL NOT write:
no grant file, no local-state directory, no process-log event, no
journal write.

#### Scenario: no file an extension declares is run
- **WHEN** an extension's `bin/` holds a runnable file and `doctor`
  runs
- **THEN** the file is never executed — no side effect of running it
  appears

#### Scenario: the listing writes nothing
- **WHEN** `doctor` runs in a project holding an extension
- **THEN** no `trust.toml` is created, no local-state directory is
  created, no event is appended and the journal is unchanged
