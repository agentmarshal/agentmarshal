## Why

ADR-0013 (decision 9 and the 2026-10-03 amendments) gives an extension with
commands a directory — `manifest.toml`, `bin/` for everything runnable,
`lock/` for the dependency locks — while an extension without commands stays
a single `<name>.toml`. The manifest schema-2 change parses every section
the directory's manifest declares, but nothing reads an extension that lives
in a directory: the working-tree reader knows only the file form, and a
`bin/` or `lock/` path it parses is never checked against the filesystem.

## What Changes

`read_extension_manifest` finds an extension at
`.agentmarshal/extensions/<name>/manifest.toml` as well as at
`.agentmarshal/extensions/<name>.toml`, and refuses when both exist for one
name, naming both paths. The directory form requires `schema = 2`; every
symlink refusal the reader has applies to the directory and to the manifest
inside it; and every path the manifest names under `bin/` or `lock/` — each
stage's `command` and each `lock` — must exist inside the directory as a
regular file, not a symlink and not reached through `..`, and is refused
otherwise with a message naming the path. A schema-2 manifest in the
single-file form that names such a path is refused: a single file has no
extension directory for it to name a file in. The parsed manifest exposes
the directory it was read from, for later tasks.

## Capabilities

- modified: `extension-manifest`

## Impact

The working-tree readers — `brief`, `review` and the sidecar gate — keep
calling `read_extension_manifest` unchanged and now accept both forms; the
gate's base-tree reader and the removal check are a later task, and the
gate's fixtures are unchanged. Running stages, trust, `doctor` and the
personal scope remain later tasks.
