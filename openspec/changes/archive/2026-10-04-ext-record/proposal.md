## Why

[ADR-0013](../../../../docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
decision 18: extension records are a shared `ext` type — the core knows the
envelope (the task, who, when, the commit, `schema`, `tool_version`); the kind
carries a namespace and a version and is declared in the manifest; the body is
opaque to the core, hash-pinned and size-limited.
[ADR-0022](../../../../docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md)
section 3 gave the record schema 7 — `kind` (`<name>/<kind>@<version>`),
`commit` (required), `payload` (JSON, up to 64 KiB, leak-scanned at write) and
`payload_sha256`, `recorded_by` with `recorded_by_source` required — and
section 8 the bound the body answers to. Neither ADR fixes how the hash is
computed; this change fixes the canonical form. The journal cannot yet carry
an extension's result at all.

## What Changes

- An `ext` record type joins the record-type registry, declared once: its
  predicate type, no projected state, admission after no terminal record —
  post-gate results go to the process log — writable, `recorded_by` with
  `recorded_by_source` required.
- Its fields register as a schema-7 field family: `kind` — of the
  `<name>/<kind>@<version>` form extension manifests declare kinds in, by the
  manifest's own rule — `commit` — required, 40 lowercase hex — `payload` —
  any JSON value — and `payload_sha256` — the sha256 of the payload's
  canonical form: its JSON serialization with sorted keys, no insignificant
  whitespace, non-ASCII unescaped, encoded as UTF-8, at most 64 KiB through
  the shared bounded-JSON validator (ADR-0022 section 8).
- An `ext` record stamped below 7 is refused at write and on read; a writer
  stamps 7 through the minimum-schema derivation, and `create_ext_record`
  builds the record, pinning the hash itself.

## Capabilities

- new: `extension-records`

## Impact

No other record type changes, and the gate's fixtures are unchanged. Nothing
reads ext records yet: the `record-ext` command, the leak scan of the payload
at write, `validate`'s "addressee not found" warning, checking that a kind is
declared by a manifest, and any reader of the body are later tasks. The
payload is opaque to the core (ADR-0013 decision 18); what it means is for
the extension itself to check.
