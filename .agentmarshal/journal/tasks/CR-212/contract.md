+++
schema = 2
id = "CR-212"
title = "agentmarshal record-ext writes an extension's result as an ext record for a kind a shared extension declares, its payload pinned, bounded and masked"
scope = [
  "src/agentmarshal/record_ext.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/record-ext-command/",
  "openspec/changes/archive/",
  "openspec/specs/extension-records/",
]
acceptance = [
  "the change record-ext-command has a proposal, a design.md and a delta spec on the capability extension-records with ADDED requirements (MODIFIED where an existing requirement says nothing writes the record yet); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal record-ext --task <id> --commit <rev> --kind <name>/<kind>@<version> --payload-file <path>` writes one `ext` record through `create_ext_record`: the commit resolved to its full 40-hex id, the payload read as JSON, `payload_sha256` computed over the canonical form CR-179 fixed, the canonical form at most 64 KiB; the command is registered from its own module the way the `step` group is",
  "the kind must be declared in `[records].kinds` of the manifest of the shared extension `<name>` in the working tree — file or directory form; a kind no shared extension declares, or a manifest that cannot be read, refuses naming the kind (ADR-0013 decision 18: only a shared extension writes `ext`, through the core's command)",
  "the payload is leak-scanned at write with the project's private markers: every JSON string value in it — keys included — that trips the scan has each matched span replaced by `[masked: <category>]` using the masking function in capture.py, the hash is computed after masking, and the command names the categories, never the matched text; a payload whose masked canonical form still trips the scan or exceeds 64 KiB refuses",
  "a refusal — unknown or terminal task (an ext record is not admitted after a terminal record), commit not found, unreadable or non-JSON payload file, a value the record rules refuse — writes nothing; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-records/"]
decisions = ["ADR-0013", "ADR-0022"]
+++

# agentmarshal record-ext

## Context

ADR-0013 decision 18: extension records are a shared `ext` type; the core
writes the envelope, the kind is declared in the manifest, the body is
opaque to the core, hash-pinned and size-limited; only a shared extension
writes `ext`, and only through the core's command. ADR-0022 section 3:
`kind`, `commit` (required), `payload` up to 64 KiB, leak-scanned at write,
`payload_sha256`, `recorded_by` required, not admitted after a terminal
record (post-gate results go to the process log). CR-179 landed the record
and fixed the canonical form; CR-152 parses `[records].kinds`; CR-183 added
the masking function the `check` excerpt uses, and the plan for 0.5.0 fixed
that a leak-scan hit in a new field is masked and marked, not refused.

## Objective

A shared extension's result reaches the journal as evidence through the
core, its body pinned and free of the secrets the scan knows.

## Acceptance Criteria

As in the header.

## Non-Goals

- Reading or interpreting the payload (opaque to the core).
- `validate`'s "addressee not found" warning (a later task).
- Running extensions; personal extensions writing records (they have no
  authority, ADR-0013 decision 15).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
