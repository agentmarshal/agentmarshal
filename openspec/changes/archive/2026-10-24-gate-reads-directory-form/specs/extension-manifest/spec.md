## ADDED Requirements

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
