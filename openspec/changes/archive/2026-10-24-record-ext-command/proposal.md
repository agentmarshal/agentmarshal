## Why

[ADR-0013](../../../../docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
decision 18 decided extension records are a shared `ext` type — only a
shared extension writes one, and never to the journal directly: the record
goes through the core's command, which writes the envelope.
[ADR-0022](../../../../docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md)
section 3 gave the record its schema-7 shape — `kind`
(`<name>/<kind>@<version>`), `commit` (required), `payload` (JSON, up to
64 KiB, leak-scanned at write) and `payload_sha256`, `recorded_by` with
`recorded_by_source` required, not admitted after a terminal record. CR-179
landed the record and fixed the canonical form; CR-152 parses
`[records].kinds`; CR-183 added the masking function the write-time scan
uses. What does not exist yet is the way an extension's result reaches the
journal: the record type has no command, so the evidence a shared extension
produces still cannot be written except by hand.

## What Changes

- `agentmarshal record-ext --task <id> --commit <rev> --kind
  <name>/<kind>@<version> --payload-file <path>` writes one `ext` record
  through `create_ext_record`: `--commit` is resolved to its full 40-hex id
  in the journal's repository — a sidecar records against the commits its
  own repository carries — and `--payload-file` is read as JSON, the
  `payload_sha256` computed over the canonical form CR-179 fixed, that form
  bounded at 64 KiB. The command lives in its own module and registers into
  `cli.py` the way `record-check` and the `step` group do.
- The kind must be declared in `[records].kinds` of the shared extension
  `<name>`'s manifest in the working tree — file or directory form: a kind
  no shared extension declares, and a manifest that cannot be read, refuse
  the write naming the kind.
- The payload is leak-scanned at write with the project's configured
  private markers: every JSON string in it — every string value and every
  object key, at any depth — is masked through `mask_leaks`, each matched
  span replaced by `[masked: <category>]`, and the command names the
  categories, never the matched text. The hash is computed after masking.
  A payload whose masked canonical form still trips the scan, or exceeds
  64 KiB, is refused — there is no excerpt to withhold, the payload is the
  record.
- A refusal — an unknown or terminal task, a commit that does not resolve,
  a kind no manifest declares, a manifest that cannot be read, an
  unreadable or non-JSON payload file, a value the record rules refuse, no
  resolvable recorder — writes nothing, and the journal still validates.

## Capabilities

- modified: `extension-records`

## Impact

One new command and one new module; no other command's behaviour or output
changes, and the gate's transcript and fixtures are untouched. The record
stays what CR-179 made it — the body is opaque to the core and nothing
reads it yet; `validate`'s "addressee not found" warning remains a later
task. Personal extensions gain no authority — the manifest check is the
shared scope's declaration — and nothing is added beyond what the
published decisions promise.
