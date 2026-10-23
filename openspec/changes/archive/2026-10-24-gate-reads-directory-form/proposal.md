## Why

ADR-0013 decision 9 makes an extension with commands a directory —
`manifest.toml`, `bin/`, `lock/` — under `.agentmarshal/extensions/<name>/`.
The directory-form change taught the working-tree reader to find it there:
both forms for one name refused, links refused, schema 2 required of a
directory. The gate reads a named extension's manifest from the trusted
side — the merge-base tree — with its own reader, `_manifest_from_tree`,
which still looks only at `<name>.toml`, and it recognises a removal only
by a deleted `<name>.toml`. A contract naming a directory-form extension
is refused as "manifest unreadable", and a candidate can delete
`manifest.toml` without the removal check ever running on the footprint
the base-side manifest declared.

## What Changes

The gate's base-tree reader finds an extension's manifest at
`.agentmarshal/extensions/<name>/manifest.toml` as well as at
`.agentmarshal/extensions/<name>.toml`, under the same rules the
working-tree reader applies, said in tree terms: a manifest in both places
is refused naming both; a symbolic-link entry at the manifest path, or at
the `<name>` directory itself, is refused; an entry at the manifest path
that is not a blob is refused; the directory form requires manifest schema
2 — each refusal on the existing "named extension manifest unreadable"
line. A candidate deleting `<name>/manifest.toml` is recognised as
removing the extension, as a deleted `<name>.toml` is today, so the
removed manifest's former footprint is checked the same way; a deletion of
another file under `<name>/` — in `bin/` or `lock/` — is not a removal. A
candidate whose contract names only file-form extensions, or none,
produces today's transcript byte for byte, as the pinned fixtures
demonstrate.

## Capabilities

- modified: `extension-manifest`

## Impact

`src/agentmarshal/journal/gate.py`: the tree reader and the removal
trigger. The sidecar gate already reads the working tree through
`read_extension_manifest`, which knows both forms, and is unchanged.
Running stages, trust, switches, `doctor` and the personal scopes remain
later tasks.
