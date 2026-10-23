+++
schema = 2
id = "CR-209"
title = "agentmarshal extension trust, untrust and list keep local run grants over the hash of a shared extension's whole directory"
scope = [
  "src/agentmarshal/extension_trust.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/extension-trust-grants/",
  "openspec/changes/archive/",
  "openspec/specs/extension-trust/",
]
acceptance = [
  "the change extension-trust-grants has a proposal, a design.md and a delta spec creating the capability extension-trust — its Purpose written in the delta, covering ADR-0013 decision 14 — with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal extension trust <name>` computes, for the shared extension in directory form at `.agentmarshal/extensions/<name>/` of the working tree, the sha256 of each regular file under it (by its path relative to the directory, sorted) and one directory hash over that sorted list, and records them in the clone's local state as `trust.toml` (`format = 1`, keyed by extension name: directory hash, file hashes, who granted it as `resolve_recorded_by` resolves the identity, when); a symbolic link or a non-regular file inside the directory refuses the grant naming it; a file-form extension or a missing directory refuses naming why",
  "`agentmarshal extension untrust <name>` removes that grant; `agentmarshal extension list` prints each shared extension in directory form with its state — granted, not granted, or changed after approval naming the first changed, added or removed file by sorted path — recomputing the hashes, and never writes; the command group is registered from its own module the way the `step` group is",
  "`trust.toml` is written atomically (a temporary file renamed into place) under the local state `localstate.py` resolves, a malformed or unknown-format `trust.toml` refuses every subcommand naming the file, and each grant and removal appends one `trust-changed` event to the process log carrying the extension name, the action and the directory hash (ADR-0022 section 7); nothing is written to the journal",
  "no extension is run by any of these commands; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-trust/"]
decisions = ["ADR-0013", "ADR-0014", "ADR-0022"]
+++

# Local run grants for shared extensions

## Context

ADR-0013 decision 14: a local grant covers the hash of the whole directory
— the manifest, `bin/`, the lock — through `agentmarshal extension trust |
untrust | list`; a shared extension with a command runs on a workstation
only under a valid grant (in CI no grant is needed), and before each run
the core recomputes the hash and refuses with `changed after approval:
<file>` on a mismatch. Decision 15 states what this does not protect
against: a process with the user's rights and no sandbox can rewrite both
the extension and the grants file. ADR-0014's map places `trust.toml` in
the clone's local state; ADR-0022 section 7 gives it the shape "a name to
the directory hash granted, who granted it and when" and the
`trust-changed` process-log event. The plan for 0.5.0 fixed that the file
also keeps per-file hashes, so the refusal can name the file.

The check before each run and running anything are later tasks; this task
keeps the grants.

## Objective

A developer can approve a shared extension's exact contents on their
machine, withdraw the approval, and see which extensions changed since.

## Acceptance Criteria

As in the header.

## Non-Goals

- Running extensions and the check before each run (later tasks).
- Personal and user-scope extensions (a later task).
- Protection against a process with the user's rights (ADR-0013 decision
  15; see docs/threat-model.md).
