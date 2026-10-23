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

### Requirement: The gate's base-tree reader finds an extension in the file form or the directory form

The gate SHALL read a named extension's manifest from the trusted side's
tree — the merge-base tree in the embedded placement — at
`.agentmarshal/extensions/<name>.toml` or at
`.agentmarshal/extensions/<name>/manifest.toml`, applying the rules the
filesystem reader applies to a working tree, said in tree terms. A
manifest in both places for one name SHALL be refused naming both entries;
in neither, the manifest SHALL be reported missing naming the file-form
path. A symbolic-link entry at either manifest path, or at the `<name>`
directory itself, SHALL be refused as a link — in a tree a link resolves
to nothing, so the `<name>` entry is examined before absence is decided. A
tree entry at a manifest path that is not a blob SHALL be refused as not a
file. A `<name>` entry that is neither a directory nor a link SHALL leave
the directory-form candidate simply absent. Every refusal SHALL land on
the gate's existing "named extension manifest unreadable" line for a
contract-named extension, and on the existing removal-not-examined line
for one read because the candidate deleted its manifest. A manifest read
from a tree exposes no directory, as the parsed-manifest requirement
already states.

#### Scenario: the tree reader finds the directory form at <name>/manifest.toml
- **WHEN** the merge-base tree holds
  `.agentmarshal/extensions/openspec/manifest.toml` and no `openspec.toml`,
  and the contract names `openspec`
- **THEN** the gate reads the manifest that entry declares — its footprint
  joins the effective scope

#### Scenario: a manifest in both forms at the base is refused naming both
- **WHEN** the merge-base tree holds both `openspec.toml` and
  `openspec/manifest.toml`, and the contract names `openspec`
- **THEN** the named-extension manifest refusal names both entries

#### Scenario: a manifest missing from the base in either form is reported missing
- **WHEN** the merge-base tree holds neither `openspec.toml` nor
  `openspec/manifest.toml` — an `openspec/` tree without a `manifest.toml`
  included — and the contract names `openspec`
- **THEN** the manifest is reported missing

#### Scenario: a symlink at the directory form's manifest is refused
- **WHEN** `openspec/manifest.toml` is a symbolic-link entry in the
  merge-base tree, and the contract names `openspec`
- **THEN** the manifest is refused as a link

#### Scenario: a symlink at the extension's directory is refused
- **WHEN** `openspec/` is a symbolic-link entry in the merge-base tree,
  and the contract names `openspec`
- **THEN** the manifest is refused as a link rather than reported missing

#### Scenario: a manifest-path entry that is not a file is refused
- **WHEN** the merge-base tree's entry at `openspec.toml` or at
  `openspec/manifest.toml` is not a blob, and the contract names
  `openspec`
- **THEN** the manifest is refused as not a file

#### Scenario: a named file-form manifest reads exactly as before
- **WHEN** the merge-base tree holds `openspec.toml`, and the contract
  names `openspec`
- **THEN** the gate reads it exactly as before this change — its
  footprint joins the effective scope, and a contract naming only
  file-form extensions, or none, produces the transcript it produced
  today, byte for byte

### Requirement: The directory form at the base requires a manifest of schema 2

A manifest the gate's base-tree reader finds in the directory form SHALL
declare `schema = 2`, the same rule the filesystem reader applies to the
same form: a directory-form manifest declaring schema 1 SHALL be refused
with a message saying the directory form requires schema 2.

#### Scenario: a schema-1 manifest in the base directory form is refused
- **WHEN** `openspec/manifest.toml` in the merge-base tree declares
  `schema = 1`, and the contract names `openspec`
- **THEN** the manifest is refused with a message saying the directory
  form requires schema 2

### Requirement: Deleting the directory form's manifest is the extension's removal

A candidate that deletes `.agentmarshal/extensions/<name>/manifest.toml` —
a manifest present on the base side — SHALL be recognised as removing
extension `<name>`, exactly as the deletion of `<name>.toml` is: the
removal check reads the manifest from the base and refuses while a
`footprint` path it declared remains in the candidate's tree. A deletion
of any other path under `<name>/` — a file in its `bin/` or its `lock/` —
SHALL NOT be read as the extension's removal.

#### Scenario: deleting <name>/manifest.toml checks the former footprint
- **WHEN** the merge base holds `openspec/manifest.toml` and the
  candidate's diff deletes it
- **THEN** the removal check runs for `openspec`: it refuses while a
  declared footprint path remains in the candidate's tree and passes when
  none does

#### Scenario: deleting another file under <name>/ is not a removal
- **WHEN** the candidate deletes `openspec/bin/tool.py` or
  `openspec/lock/uv.lock` and keeps `openspec/manifest.toml`
- **THEN** no removal is recognised and no removal line is printed

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

### Requirement: `doctor` checks the runtime a wrapper declares

For each shared extension whose manifest parses and declares
`[wraps].runtime` — the `<name> >= <version>` form, a declared
minimum — `doctor` SHALL run one check of its own,
`extension runtime <name>`, which resolves the declared `<name>` on
`PATH` — the one `PATH` exception of ADR-0013 decision 13 as
amended — runs the resolved path with `--version` as an argv call,
never through a shell, under a short time limit, and reports the
path found, the version it reports and whether that meets the
declared minimum. Versions SHALL be compared by their leading
numeric dot-separated components — a leading `v` ignored, a missing
trailing component reading as zero — and output naming no readable
version SHALL be reported as unreadable rather than guessed. A
runtime not found on `PATH`, one whose invocation fails, one that
does not answer in time, one reporting an unreadable version and
one below the declared minimum SHALL each fail the check — the
failure counting in the verdict and the exit status by `doctor`'s
existing rules for a failed check. Every value a result names —
the path found, the version reported, the declared requirement —
SHALL be escaped on display; the check SHALL run nothing else an
extension declares and SHALL install nothing.

#### Scenario: a wrapper's runtime that meets the declared minimum passes
- **WHEN** a shared extension's manifest declares
  `runtime = "node >= 20"` and `node` resolves on `PATH` reporting
  `v20.11.0`
- **THEN** the `extension runtime` check passes, naming the path
  found, the version reported and the requirement it meets

#### Scenario: versions compare by leading numeric components, a leading v ignored
- **WHEN** the manifest declares `runtime = "node >= 20"` and the
  runtime reports `v9.11.0`
- **THEN** the check fails below the minimum — 9 is less than 20
  numerically though the texts compare otherwise — and the leading
  `v` played no part

#### Scenario: a runtime not found on PATH fails the check
- **WHEN** the declared `<name>` resolves nowhere on `PATH`
- **THEN** the check fails naming the runtime and the declared
  requirement

#### Scenario: a runtime whose --version fails fails the check
- **WHEN** the resolved path's `--version` exits non-zero
- **THEN** the check fails naming the path and the exit status

#### Scenario: a runtime that does not answer in time fails the check
- **WHEN** `--version` does not return within the time limit
- **THEN** the check fails naming the path and the limit

#### Scenario: a runtime reporting no readable version fails the check
- **WHEN** the `--version` output names no numeric version or
  cannot be decoded
- **THEN** the check fails reporting the version unreadable rather
  than guessed

#### Scenario: a runtime below the declared minimum fails the check
- **WHEN** the manifest declares `runtime = "node >= 20"` and the
  runtime reports `v18.19.0`
- **THEN** the check fails naming the reported version and the
  declared minimum

#### Scenario: each value a runtime result names is escaped on display
- **WHEN** a value a runtime result names — the resolved path,
  say — carries a character the forgeable-text rule refuses
- **THEN** the value prints escaped

#### Scenario: the check runs nothing else an extension declares and installs nothing
- **WHEN** a wrapper's `bin/` holds a runnable file and `doctor`
  runs the runtime check
- **THEN** only the declared runtime's `--version` is invoked — no
  `[[stage]]` `command` runs and nothing is installed

### Requirement: a wrapper adds a runtime check only while its manifest declares `[wraps]`

An extension whose manifest declares no `[wraps]` SHALL gain no
runtime check and no runtime line; an extension whose manifest
cannot be read SHALL gain none either — the manifest's own check
already reports the reason — and a project holding no wrapper SHALL
keep `doctor`'s output unchanged: the same checks, the same
verdict.

#### Scenario: each wrapper gets its own runtime check
- **WHEN** two shared extensions declare `[wraps]` with different
  runtimes
- **THEN** each gains one `extension runtime <name>` check

#### Scenario: an extension without wraps gets no runtime line
- **WHEN** a shared extension's manifest declares no `[wraps]`
- **THEN** no `extension runtime` line prints for it

#### Scenario: an unreadable manifest adds no runtime check
- **WHEN** a shared extension's manifest cannot be read
- **THEN** the `extension manifest <name>` check reports the
  reason and no `extension runtime` line prints

#### Scenario: a project without wrappers prints doctor's output unchanged
- **WHEN** `doctor` runs in a project whose extensions declare no
  `[wraps]`, or holding none
- **THEN** the check report and the verdict print as they would
  without the change
