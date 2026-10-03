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
declared `name` matching the manifest's file name, `version` a non-empty
string, `footprint`, `documents` and `artifacts` paths in scope syntax with
the latter two under the footprint — with one relaxation: `install` and
`remove` are OPTIONAL in schema 2, where schema 1 requires them as non-empty
strings.

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

#### Scenario: install and remove are optional in schema 2
- **WHEN** a schema-2 manifest declares neither `install` nor `remove`
- **THEN** it parses, and the parsed manifest carries neither

#### Scenario: a schema-1 manifest parses exactly as before
- **WHEN** a schema-1 manifest carries no schema-2 field
- **THEN** it parses with the same fields it parsed with before

### Requirement: A stage entry declares a phase and a command under bin/

A schema-2 manifest MAY carry `[[stage]]` entries. Each entry SHALL declare
`phase`, one of `post-gate`, `pre-gate-warn` or `pre-gate-stop`, and
`command`, a relative path under the extension's own `bin/` — never an
absolute path, never a `..` component, never a bare program name, which
would be a `PATH` lookup. A malformed `stage` list or entry SHALL be refused
with a message naming the field and the source.

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
one `PATH` exception being the wrapped product's runtime. A missing or
malformed field SHALL be refused naming it and the source.

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

### Requirement: Declared record kinds name the extension itself

A schema-2 manifest MAY carry `[records].kinds`, the `ext` record kinds it
writes. Each entry SHALL have the form `<name>/<kind>@<version>` whose
`<name>` is the manifest's own name — an extension declares only its own
kinds.

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
