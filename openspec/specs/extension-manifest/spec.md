# extension-manifest Specification

## Purpose
What a process-extension manifest declares and what it refuses. Schema 1 —
the manifest-only form of ADR-0010 — declares the extension's name, version,
footprint, named documents and artifacts, and `install`/`remove` strings the
tool never runs. Schema 2 (ADR-0013, numbered by ADR-0022) extends it with
the stages an extension runs at and how, its dependency lock, the product it
wraps and that product's verified version, the `ext` record kinds it
declares, and the isolation it asks for. A malformed declaration is refused
at the boundary with a message naming the field and the source.

## Requirements

### Requirement: A manifest declares a known schema version

A manifest SHALL declare `schema` as the integer 1 or 2; a missing,
non-integer or other version SHALL be refused as an unknown or missing
schema version. Every schema-1 rule applies unchanged to schema 2 — the
declared `name` matching the extension's name — the manifest's file name
without `.toml` in the file form, the extension directory's name in the
directory form — `version` a non-empty string, `footprint`, `documents`
and `artifacts` paths in scope syntax with the latter two under the
footprint — with one relaxation: `install`, `remove` and `artifacts` are
OPTIONAL in schema 2 (ADR-0013's example carries none of them), where
schema 1 requires all three. Every free-text string a schema-2 manifest
declares — a present `install` or `remove` included — SHALL pass the
control-character rule.

Each of `stage`, `dependencies`, `wraps`, `records` and `isolation` is a
schema-2 field: any of them in a schema-1 manifest SHALL be refused with a
message naming the field and that it requires schema 2.

#### Scenario: schema 3 is an unknown manifest schema
- **WHEN** a manifest declares `schema = 3`
- **THEN** it is refused as an unknown manifest schema

#### Scenario: a schema-2 field in a schema-1 manifest requires schema 2
- **WHEN** a schema-1 manifest carries `stage`, `dependencies`, `wraps`,
  `records` or `isolation`
- **THEN** it is refused with a message naming the field and that it
  requires schema 2

#### Scenario: install, remove and artifacts are optional in schema 2
- **WHEN** a schema-2 manifest declares none of `install`, `remove` or
  `artifacts`
- **THEN** it parses, and the parsed manifest carries none of them

#### Scenario: schema 1 requires install, remove and artifacts
- **WHEN** a schema-1 manifest lacks `install`, `remove` or `artifacts`
- **THEN** it is refused naming the field

#### Scenario: a schema-2 free-text field carrying control characters is refused
- **WHEN** a schema-2 manifest's `install` or `remove` contains a control
  character
- **THEN** it is refused naming the field and the source

#### Scenario: a schema-1 manifest parses exactly as before
- **WHEN** a schema-1 manifest carries no schema-2 field
- **THEN** it parses with the same fields it parsed with before

### Requirement: A stage entry declares a phase and a command under bin/

A schema-2 manifest MAY carry `[[stage]]` entries. Each entry SHALL declare
`phase`, one of `post-gate`, `pre-gate-warn` or `pre-gate-stop`, and
`command`, a relative path under the extension's own `bin/` — never an
absolute path, never a `..` component, never a bare program name, which
would be a `PATH` lookup, and carrying no whitespace or shell
metacharacters, because the core runs it as an argv path, never through a
shell. A malformed `stage` list or entry SHALL be refused with a message
naming the field and the source.

#### Scenario: a stage entry parses its phase and command
- **WHEN** a schema-2 manifest declares a `[[stage]]` entry with
  `phase = "pre-gate-stop"` and `command = "bin/validate.py"`
- **THEN** the parsed manifest exposes a stage of phase `pre-gate-stop`
  running `bin/validate.py`

#### Scenario: a phase outside the three modes is refused
- **WHEN** a `[[stage]]` entry declares a `phase` that is not `post-gate`,
  `pre-gate-warn` or `pre-gate-stop`
- **THEN** the manifest is refused naming `phase`

#### Scenario: a command outside the extension's bin/ is refused
- **WHEN** a `[[stage]]` entry's `command` is absolute, carries a `..`
  component, or names no path under `bin/` — a bare program name included
- **THEN** the manifest is refused naming `command`

#### Scenario: a command carrying whitespace or a shell metacharacter is refused
- **WHEN** a `[[stage]]` entry's `command` contains whitespace or a shell
  metacharacter
- **THEN** the manifest is refused naming `command`

#### Scenario: a malformed stage declaration is refused
- **WHEN** `stage` is not an array of tables, or an entry lacks `phase` or
  `command`
- **THEN** the manifest is refused naming the field

### Requirement: A dependency lock is a file under lock/

A schema-2 manifest MAY carry `[dependencies]`, which SHALL declare `lock`:
a relative path under `lock/` in the extension's own directory, validated
exactly as a `command` under `bin/` is.

#### Scenario: a dependencies lock under lock/ parses
- **WHEN** a schema-2 manifest declares `[dependencies]` with
  `lock = "lock/uv.lock"`
- **THEN** the parsed manifest exposes the dependency lock `lock/uv.lock`

#### Scenario: a dependencies lock outside lock/ is refused
- **WHEN** `[dependencies].lock` is absolute, carries a `..` component, or
  names no path under `lock/`
- **THEN** the manifest is refused naming `lock`

### Requirement: A wrapped product is named with its verified version, ecosystem, lock, runtime and license

A schema-2 manifest MAY carry `[wraps]` for the wrapper form. The section
SHALL declare `product`, `version`, `ecosystem`, `lock`, `runtime` and
`license`: `lock` a relative path under `lock/` in the extension's own
directory, and `runtime` of the form `<name> >= <version>` — a minimum, the
one `PATH` exception being the wrapped product's runtime. Each free-text
field — `product`, `version`, `ecosystem`, `runtime` and `license` — SHALL
pass the control-character rule. A missing or malformed field SHALL be
refused naming it and the source.

#### Scenario: a wraps section parses every field
- **WHEN** a schema-2 manifest declares `[wraps]` with all six fields
- **THEN** the parsed manifest exposes the product, its verified version,
  the ecosystem, the product lock, the runtime and the license

#### Scenario: a missing wraps field is refused
- **WHEN** `[wraps]` lacks any of `product`, `version`, `ecosystem`, `lock`,
  `runtime` or `license`
- **THEN** the manifest is refused naming the missing field

#### Scenario: a runtime not of the declared form is refused
- **WHEN** `[wraps].runtime` is not of the form `<name> >= <version>`
- **THEN** the manifest is refused naming `runtime`

#### Scenario: a product lock outside lock/ is refused
- **WHEN** `[wraps].lock` is absolute, carries a `..` component, or names no
  path under `lock/`
- **THEN** the manifest is refused naming `lock`

#### Scenario: a wraps field carrying control characters is refused
- **WHEN** `product`, `version`, `ecosystem`, `runtime` or `license`
  contains a control character
- **THEN** the manifest is refused naming the field and the source

### Requirement: Declared record kinds name the extension itself

A schema-2 manifest MAY carry `[records].kinds`, the `ext` record kinds it
writes. Each entry SHALL have the form `<name>/<kind>@<version>` whose
`<name>` is the manifest's own name — an extension declares only its own
kinds — and SHALL pass the control-character rule.

#### Scenario: declared record kinds parse
- **WHEN** the `openspec` manifest declares
  `kinds = ["openspec/change-archived@1"]`
- **THEN** the parsed manifest exposes the declared kind

#### Scenario: a kind naming another extension is refused
- **WHEN** a `kinds` entry's `<name>` is not the manifest's own name
- **THEN** the manifest is refused naming `kinds` and the entry

#### Scenario: a malformed kind is refused
- **WHEN** a `kinds` entry is not of the form `<name>/<kind>@<version>`
- **THEN** the manifest is refused naming `kinds` and the entry

#### Scenario: a kind carrying a control character is refused
- **WHEN** a `kinds` entry contains a control character
- **THEN** the manifest is refused naming `kinds` and the entry

### Requirement: Declared isolation is complete and well-formed

A schema-2 manifest MAY carry `[isolation]`, which SHALL declare `network`
(a boolean), `env` (a list of environment variable names), `writes` (`none`
or `process-log`) and `timeout_seconds` (an integer above zero). A missing
or malformed field SHALL be refused naming it and the source.

#### Scenario: an isolation section parses
- **WHEN** a schema-2 manifest declares `[isolation]` with all four fields
  well-formed
- **THEN** the parsed manifest exposes the declared isolation

#### Scenario: a malformed isolation field is refused naming it
- **WHEN** `network` is not a boolean, an `env` entry is not a variable
  name, `writes` is not `none` or `process-log`, or `timeout_seconds` is
  not an integer above zero
- **THEN** the manifest is refused naming the field

### Requirement: The parsed manifest exposes the schema-2 declarations

The parsed manifest SHALL expose the stages, the dependency lock, the wraps
section, the declared record kinds and the isolation for later tasks to
read. An absent optional section SHALL expose as absent — no stages, no
lock, no wraps, no kinds, no isolation — never as a malformed one.

#### Scenario: the parsed manifest carries every declared section
- **WHEN** a schema-2 manifest declares every schema-2 section
- **THEN** the parsed manifest exposes each of them

#### Scenario: absent sections expose as absent
- **WHEN** a schema-2 manifest declares none of the schema-2 sections
- **THEN** it parses with no stages, no dependency lock, no wraps, no record
  kinds and no isolation

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
each be refused as a link — dangling or not, and before existence is
decided, since strict resolution would report a link pointing nowhere as
missing. A component of the file-form path that is not a directory keeps
the refusal the file-form reader gives it today rather than reporting the
manifest missing; a `<name>` that is not a directory is simply absent.

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

#### Scenario: a dangling symlink at the extension's directory is refused
- **WHEN** `openspec/` is a symlink whose target does not exist
- **THEN** the reader refuses it as a link

#### Scenario: a component of the manifest path that is not a directory is refused
- **WHEN** a component of `.agentmarshal/extensions/<name>.toml` above the
  file is not a directory
- **THEN** the reader refuses rather than reporting the manifest missing

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
- **WHEN** `bin/` or `lock/` inside the extension's directory is a symlink,
  dangling or not
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
