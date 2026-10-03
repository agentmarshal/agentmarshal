## ADDED Requirements

### Requirement: An extension is found in the file form or the directory form

A process extension SHALL live at `.agentmarshal/extensions/<name>.toml` —
the file form — or at `.agentmarshal/extensions/<name>/manifest.toml` — the
directory form of ADR-0013 decision 9, whose `bin/` holds everything
runnable and whose `lock/` holds the dependency locks. The filesystem
reader SHALL find an extension in either place. When both places hold a
manifest for one name the reader SHALL refuse, naming both paths; when
neither holds one it SHALL report the manifest missing, as the file-form
reader reports it today.

Every refusal the reader applies to a file-form manifest SHALL apply to the
directory form: a symlink at `<name>/manifest.toml`, a symlink for the
`<name>` directory itself, and a symlink in any component of the path SHALL
each be refused as a link.

#### Scenario: the directory form is found at <name>/manifest.toml
- **WHEN** `.agentmarshal/extensions/openspec/` holds a `manifest.toml`
  and no `openspec.toml` exists
- **THEN** the reader returns the manifest that file declares

#### Scenario: a manifest in both forms is refused naming both paths
- **WHEN** `.agentmarshal/extensions/` holds both `openspec.toml` and
  `openspec/manifest.toml`
- **THEN** the reader refuses, naming both paths

#### Scenario: a missing extension is reported missing in either form
- **WHEN** neither `openspec.toml` nor `openspec/manifest.toml` exists
- **THEN** the reader reports the manifest missing

#### Scenario: a symlinked manifest inside the directory is refused
- **WHEN** `openspec/manifest.toml` is a symlink
- **THEN** the reader refuses it as a link

#### Scenario: a symlinked extension directory is refused
- **WHEN** `openspec/` is a symlink to a directory holding a
  `manifest.toml`
- **THEN** the reader refuses it as a link

### Requirement: The directory form requires a manifest of schema 2

A manifest read from the directory form SHALL declare `schema = 2` — the
directory is the schema-2 form, the shape of ADR-0013's amended manifest
example. A directory-form manifest declaring schema 1 SHALL be refused with
a message saying the directory form requires schema 2.

A schema-2 manifest read from the file form that names a path under `bin/`
or `lock/` — a `[[stage]]` `command`, `[dependencies].lock` or
`[wraps].lock` — SHALL be refused naming the path: a single file has no
extension directory for the path to name a file in (ADR-0013 decisions 9
and 13). A schema-2 file-form manifest declaring none of them parses as
the manifest-only form.

#### Scenario: a schema-1 manifest in the directory form is refused
- **WHEN** `openspec/manifest.toml` declares `schema = 1`
- **THEN** the reader refuses it with a message saying the directory form
  requires schema 2

#### Scenario: a single-file manifest naming a bin/ or lock/ path is refused
- **WHEN** a schema-2 `openspec.toml` declares a `command` under `bin/` or
  a `lock` under `lock/`
- **THEN** the reader refuses it naming the path

#### Scenario: a schema-2 single file naming no directory path parses
- **WHEN** a schema-2 `openspec.toml` declares no `stage`, `dependencies`
  or `wraps`
- **THEN** it parses as the manifest-only form

### Requirement: A path the directory form names exists in the extension's directory

In the directory form, every path a manifest names under `bin/` or `lock/`
— each `[[stage]]` `command` and each `lock` — SHALL name a file that
exists inside the extension's own directory: a regular file, reached
through no `..` component and through no symlink — not at the file itself,
not at `bin/`, `lock/` or a directory between. A named path that is absent,
is a directory, is a symlink or resolves outside the extension's directory
SHALL be refused with a message naming the path.

#### Scenario: named paths that exist as regular files are read
- **WHEN** every `command` and `lock` a directory-form manifest declares
  names a regular file inside the extension's directory
- **THEN** the manifest parses and exposes the named paths

#### Scenario: a named path absent from the directory is refused
- **WHEN** a `command` or a `lock` names a path that does not exist in the
  extension's directory
- **THEN** the manifest is refused naming the path

#### Scenario: a named path that is a directory is refused
- **WHEN** a `command` or a `lock` names a directory inside the extension's
  directory
- **THEN** the manifest is refused naming the path

#### Scenario: a named path that is a symlink is refused
- **WHEN** a `command` or a `lock` names a symlink inside the extension's
  directory
- **THEN** the manifest is refused as a link naming the path

#### Scenario: a named path under a symlinked directory is refused
- **WHEN** `bin/` or `lock/` inside the extension's directory is a symlink
- **THEN** the manifest is refused as a link naming the path

### Requirement: The parsed manifest exposes the directory it was read from

A manifest read from the directory form SHALL expose the directory it was
read from, for later tasks — the directory hash of ADR-0013 decision 14 and
the stage runner. A manifest read from the file form, or parsed from a
source with no directory — the gate's base-tree read — SHALL expose none.

#### Scenario: a directory-form manifest exposes its directory
- **WHEN** a manifest is read from `openspec/manifest.toml`
- **THEN** the parsed manifest exposes the `openspec/` directory it was
  read from

#### Scenario: a manifest without a directory exposes none
- **WHEN** a manifest is read from `openspec.toml` or parsed from a
  source with no directory
- **THEN** the parsed manifest exposes no directory
