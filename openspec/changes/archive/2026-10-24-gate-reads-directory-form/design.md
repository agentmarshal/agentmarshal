## Context

`run_gate` reads a named extension's manifest from the merge-base tree —
the trusted side, so a candidate cannot widen its own scope or silence a
documents check by rewriting the manifest it ships with (ADR-0010 D2;
ADR-0013 decision 6, "read from the base", extended to the gate's own
reading by the 2026-10-03 amendment). The reader is `_manifest_from_tree`
in `src/agentmarshal/journal/gate.py`: it `ls-tree`s
`.agentmarshal/extensions/<name>.toml` with a literal pathspec, refuses a
symlink (mode `120000`) and a non-blob entry, `git show`s the blob and
passes the text to `parse_extension_manifest_text` — the shared validator
that knows nothing about where the text came from. A removal is recognised
by a `D` status on `<name>.toml` (`_extension_name`), and the removed
manifest's former footprint is checked in the candidate's tree
(ADR-0010 D5).

The directory-form change taught the working-tree reader the second form
of ADR-0013 decision 9 — `<name>/manifest.toml`, with `bin/` and `lock/` —
with refusals for a manifest in both places, a link at the manifest path
or at the `<name>` directory, a component that is not a directory, and
schema 1 in a directory. This change gives the gate's tree read the same
form knowledge. A git tree holds no resolvable links, but it records them
— mode `120000` — which is the whole of what the link refusals become
there.

## Goals

- A contract naming a directory-form extension reads its manifest at the
  merge base: its footprint joins the effective scope and its `documents`
  the named documents, exactly as a file-form manifest's do.
- The working-tree refusals carried to tree terms: a manifest in both
  places refused naming both; a link entry at the manifest path or at the
  `<name>` directory refused; a non-blob entry at the manifest path
  refused; schema 1 in a directory refused. Each refusal lands on the
  existing "named extension manifest unreadable" line — or, for a manifest
  read because the candidate deleted it, on the existing
  removal-not-examined line.
- A deletion of `<name>/manifest.toml` is a removal of `<name>`; a
  deletion of any other path under `<name>/` is not.
- A contract naming only file-form extensions, or none, gets today's
  transcript byte for byte; the sidecar's working-tree read is unchanged.

## Non-Goals

- Existence of the `bin/` or `lock/` files a directory-form manifest
  names. The working-tree reader checks them against the filesystem it
  reads, because later tasks will run what the manifest names; the gate
  reads the manifest for scope, documents and removal inputs and never
  runs it, and a tree read exposes no `directory` — the parsed-manifest
  requirement already says so. The directory hash and the stage runner
  that consume those paths are later tasks.
- The single-file refusal of a schema-2 manifest naming `bin/` or `lock/`
  paths. It is a rule about where the file lives on disk; at the merge
  base the file-form manifest parses exactly as it does today, and whether
  it would be refused on a working tree is the filesystem readers' call,
  unchanged.
- How a sidecar recognises a removal — the code comment already names the
  awaited ADR-0010 amendment — and everything else the change's non-goals
  name: running stages, trust, switches, `doctor`, the personal scopes.

## Decisions

- **Two candidate entries, the file form first.** The reader `ls-tree`s
  `.agentmarshal/extensions/<name>.toml`, then the `<name>` entry itself,
  then — only when `<name>` is a tree — `<name>/manifest.toml`. The order
  mirrors the filesystem reader, which evaluates the file candidate before
  the directory candidate, so a link at `<name>.toml` is reported before
  one at `<name>`. A `120000` entry is the tree form of a symbolic link
  and is refused with the words the file-form refusal already uses; a
  non-blob entry at the manifest path keeps the existing
  "is a `<kind>`, not a file" refusal.
- **A `<name>` entry that is not a directory and not a link is simply
  absent** — a blob or a gitlink there means the directory-form candidate
  does not exist, exactly as the filesystem reader treats a `<name>` that
  is not a directory. A link there is refused instead, and it is checked
  before the manifest path beneath it is queried: a tree walk resolves
  nothing through a link, so without the explicit check the link would
  read as a missing manifest — the same reason the filesystem reader
  refuses a link lexically, dangling or not, before deciding existence.
- **Both present is refused naming both, neither is missing naming the
  file-form path** — the place an adopter is told to look, as the
  filesystem reader does.
- **The directory form at the base requires schema 2**, with the
  filesystem reader's message and for its reason: a directory exists to
  hold what a schema-2 manifest declares. The check runs after the shared
  validator, so a schema the validator does not know is refused there
  first, as on disk.
- **A removal is a deleted manifest in either form.** `_extension_name`
  matches `<name>.toml` and `<name>/manifest.toml` — each a single path
  component for the name — and nothing else under `<name>/`: a `bin/` or
  `lock/` file deleted is footprint-neutral and does not trigger the
  check. The removal check itself is untouched: the manifest is read from
  the base — now in either form — and its footprint is counted off in the
  candidate's tree.
