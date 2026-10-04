+++
schema = 2
id = "CR-179"
title = "An ext record of schema 7 carries an extension's result: a declared kind, the commit, an opaque payload and its hash"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "src/agentmarshal/journal/status.py",
  "tests/",
  "openspec/changes/ext-record/",
  "openspec/changes/archive/",
  "openspec/specs/extension-records/",
]
acceptance = [
  "the change ext-record has a proposal, a design.md and a delta spec creating the capability extension-records — its Purpose written in the delta, covering ADR-0013 decision 18 — with ADDED requirements for the record; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "an `ext` record type exists from schema 7, declared once in the record-type registry (predicate type, projected state, writable, not admitted after a terminal record, `recorded_by` with `recorded_by_source` required, as ADR-0022 section 3 lists it); its fields are `kind` — matching the `<name>/<kind>@<version>` form extension manifests declare kinds in, by the manifest's own rule, not a copy of it — `commit` — 40 lowercase hex, required — `payload` — any JSON value — and `payload_sha256`",
  "the payload's canonical form is its JSON serialization with sorted keys, no insignificant whitespace (separators `,` and `:`), non-ASCII characters unescaped, encoded as UTF-8; `payload_sha256` must be 64 lowercase hex equal to the sha256 of that form, and that form must be at most 64 KiB (ADR-0022 section 8) — each refusal naming the field; design.md states the form",
  "an ext record below schema 7 is refused at write and on read; writing one stamps 7; no other record type changes; `validate` and `status` handle a task carrying one without failing; nothing else reads it yet",
  "the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-records/"]
+++

# The ext record

## Context

ADR-0013 decision 18: extension records are a shared `ext` type — the core
knows the envelope (the task, who, when, the commit, `schema`,
`tool_version`); the kind carries a namespace and a version and is declared
in the manifest; the body is opaque to the core, hash-pinned and
size-limited. ADR-0022 section 3 gives it schema 7: `kind`
(`<name>/<kind>@<version>`), `commit` (required), `payload` (JSON, up to
64 KiB, leak-scanned at write) and `payload_sha256`, with `recorded_by`
required. Neither ADR fixes how the hash is computed; this contract fixes
the canonical form. The leak scan at write belongs to the command that
writes the record (`record-ext`), as the `check` excerpt's does to
`record-check`; `validate`'s "addressee not found" warning reads manifests
and is a later task too.

## Objective

The journal can carry an extension's result with its body pinned by hash
and bounded in size.

## Acceptance Criteria

As in the header.

## Non-Goals

- The `record-ext` command, the leak scan of the payload at write,
  `validate`'s "addressee not found" warning, checking that a kind is
  declared by a manifest, and any reader of the body (later tasks).
- Any meaning of the payload: it is opaque to the core (ADR-0013 decision 18).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
