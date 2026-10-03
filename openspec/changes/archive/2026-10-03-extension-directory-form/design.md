## Context

`read_extension_manifest` in `src/agentmarshal/journal/extensions.py` reads
`.agentmarshal/extensions/<name>.toml` from a working tree — the file form —
refusing a link at the manifest path outright and a link above it by strict
resolution, and reporting a missing manifest as `ExtensionManifestMissing`
so context-building readers can go on while an authority path fails loudly.
Its callers are `brief`, `review` and the sidecar gate's working-tree read;
the embedded gate reads the manifest blob from the merge-base tree and
passes the text to `parse_extension_manifest_text`, which validates syntax
and knows nothing about files on disk.

ADR-0013 decision 9 (amended 2026-10-03) makes an extension with commands a
directory — `manifest.toml`, `bin/` for everything runnable, `lock/` for
the dependency locks — while a manifest-only extension stays a single
`<name>.toml`. The schema-2 change deferred existence: it parsed `command`
and the locks as lexical paths and named "checking that a named file under
`bin/` or `lock/` exists" a later task. This is that task, for the working
tree. The gate's base-tree reader is a separate task.

## Goals

- The reader finds an extension in the directory form as well as the file
  form, refuses both together for one name naming both paths, and reports
  neither as missing.
- The directory form requires `schema = 2`, and every path it names under
  `bin/` or `lock/` exists inside the directory as a regular file reached
  through no symlink and no `..`.
- The parsed manifest exposes the directory it was read from, for the
  directory hash and the stage runner a later task builds.
- The callers and the gate's fixtures are unchanged.

## Non-Goals

- The gate's base-tree reader (`_manifest_from_tree`) and the removal check:
  reading the directory form out of a git tree is a later task, so
  `parse_extension_manifest_text` keeps validating syntax only.
- Running stages, trust, switches, `doctor`, the personal scopes.
- Enumerating the directory: the reader checks the paths the manifest
  names, not what else the directory holds — the hash check of ADR-0013
  decision 14 is a later task's.

## Decisions

- **Two candidate paths, one resolution rule each.** The reader resolves
  `.agentmarshal/extensions/<name>.toml` and
  `.agentmarshal/extensions/<name>/manifest.toml` with the same rule the
  file form uses today: a link at the manifest path is refused as a link
  (dangling or not, before resolution can report it missing), a strict
  resolution that succeeds but lands elsewhere is refused the same way —
  which is how a symlinked `<name>` directory is refused — and an absent
  candidate is simply absent. Both resolving for one name is refused naming
  both paths, because which form the extension is would be ambiguous;
  neither resolving is `ExtensionManifestMissing` naming the file-form
  path, the place an adopter is told to look.
- **The directory form is schema 2 only.** A directory exists to hold what
  a manifest of schema 2 declares — the commands and the locks — so schema
  1 inside it is refused with a message saying the directory form requires
  schema 2, rather than silently reading an ADR-0010 manifest from a place
  ADR-0010 did not name.
- **A named path must exist as a regular file inside the directory.** Each
  `[[stage]]` `command` and each `lock` is checked against the extension's
  own directory with the same resolution rule as the manifest itself: a
  link at the named path is refused as a link; a strict resolution that
  lands elsewhere — a link for `bin/`, `lock/` or a directory between, each
  of which is also how a `..` would be reached through a link — is refused
  the same way; an absent path is refused naming it; and a path that
  resolves to something that is not a regular file — a directory — is
  refused naming it. The lexical rule already forbids `..` in the declared
  path, so the filesystem check is the whole remaining hazard.
- **The file form has no directory, so it names no directory paths.** A
  schema-2 single file naming `bin/` or `lock/` paths — any `command` or
  `lock` — is refused naming the path: ADR-0013 decision 13's "the `bin/`
  of its own directory" has no referent for a single file, and letting it
  stand would bless a command with no file behind it. A schema-2 single
  file declaring none of them — a manifest-only extension that happens to
  declare schema 2 — parses unchanged; everything else about the file form
  is unchanged too.
- **The directory is exposed, not searched.** `ExtensionManifest` gains a
  `directory` the filesystem reader fills with the resolved path of
  `<name>/` and nothing else fills: the parser leaves it `None`, so the
  gate's base-tree read exposes none until its own task. Later tasks —
  the grant hash of decision 14, the stage runner — take the directory
  from there rather than re-deriving where the manifest was found.
