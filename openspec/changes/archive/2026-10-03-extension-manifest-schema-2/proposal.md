## Why

ADR-0013 (with its 2026-10-03 amendments) gives an extension a manifest of
schema 2: the stages it runs at and how, its dependency lock, the product it
wraps and that product's verified version, the `ext` record kinds it
declares, and the isolation it asks for. ADR-0022 numbers it 2. Today the
parser knows only schema 1 — the manifest-only form — and refuses
`schema = 2` as an unknown version, so nothing an extension needs to declare
can be declared at all.

## What Changes

Extension manifest schema 2 exists and parses in the file form that exists
today (`.agentmarshal/extensions/<name>.toml`). A schema-2 manifest may carry
`[[stage]]` entries — `phase` from `post-gate`, `pre-gate-warn` and
`pre-gate-stop`, and `command` naming a file under the extension's own
`bin/` — `[dependencies].lock` under `lock/`, `[wraps]` naming the wrapped
product, its verified version, ecosystem, product lock, required runtime and
license, `[records].kinds` declaring this extension's `ext` kinds, and
`[isolation]` declaring network, environment, writes and timeout. Every
malformed field is refused with a message naming the field and the source, as
the existing messages do. In schema 2 `install` and `remove` become optional;
the schema-2 fields in a schema-1 manifest are refused as requiring schema 2;
schema 3 stays an unknown schema, and schema-1 manifests parse exactly as
before.

## Capabilities

- new: `extension-manifest`

## Impact

Parsing and validation only: the parsed `ExtensionManifest` exposes the new
fields and nothing reads them yet — the gate, `brief` and `review` behave as
before, and the gate's fixtures are unchanged. The directory form, running
stages, trust, switches, doctor and personal scope are later tasks.
