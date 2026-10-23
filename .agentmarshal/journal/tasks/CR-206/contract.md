+++
schema = 2
id = "CR-206"
title = "The gate reads an extension manifest in directory form from the trusted side, and recognises its removal, by the rules the working-tree reader applies"
scope = [
  "src/agentmarshal/journal/gate.py",
  "tests/",
  "openspec/changes/gate-reads-directory-form/",
  "openspec/changes/archive/",
  "openspec/specs/extension-manifest/",
]
acceptance = [
  "the change gate-reads-directory-form has a proposal, a design.md and a delta spec on the capability extension-manifest with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "the gate's reader of a named extension's manifest from the merge-base tree finds it at `.agentmarshal/extensions/<name>.toml` or at `.agentmarshal/extensions/<name>/manifest.toml`, by the same rules `read_extension_manifest` applies to a working tree since CR-158: a manifest in both places is refused naming both; a symbolic link at the manifest path, or at the `<name>` directory, is refused; a tree entry that is not a file is refused; the directory form requires manifest schema 2 — each refusal on the gate's existing \"named extension manifest unreadable\" line",
  "a candidate that deletes `.agentmarshal/extensions/<name>/manifest.toml` is recognised as removing extension `<name>`, as the deletion of `<name>.toml` is today, so the removed manifest's former footprint is checked the same way; a deletion of another file under `<name>/` (in `bin/` or `lock/`) is not read as the removal of the extension",
  "a candidate whose contract names only file-form extensions, or none, produces today's gate transcript byte for byte, which the pinned default transcript and the fixtures demonstrate; the sidecar path, which already reads the working tree through `read_extension_manifest`, is unchanged",
  "no other gate check changes; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-manifest/"]
decisions = ["ADR-0010", "ADR-0013", "ADR-0022"]
+++

# The gate reads the directory form

## Context

ADR-0013 decision 9: an extension with commands is a directory —
`manifest.toml`, `bin/`, `lock/` — under `.agentmarshal/extensions/<name>/`.
CR-158 taught `read_extension_manifest` to find it in a working tree beside
the single-file form, with refusals for a manifest in both places, a
symbolic link and a directory form below manifest schema 2. The gate reads
a named extension's manifest from the trusted side — the merge-base tree —
with its own reader, `_manifest_from_tree`, which still looks only at
`<name>.toml`; it also recognises a removal only by a deleted `<name>.toml`.
ADR-0010 has the gate add a manifest's footprint to effective scope and
check a removed manifest's former footprint. Executing extensions is the
0.6.0 work this begins.

## Objective

An extension in directory form is read and its removal recognised at the
merge boundary exactly as a single-file extension is.

## Acceptance Criteria

As in the header.

## Non-Goals

- Running anything an extension declares; trust, switches, isolation
  (later tasks).
- What a change inside an extension's `bin/` or `lock/` means for trust (a
  later task: the check before running).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
