+++
schema = 2
id = "CR-152"
title = "Extension manifest schema 2 is parsed: stages, dependencies, a wrapped product, record kinds and isolation"
scope = [
  "src/agentmarshal/journal/extensions.py",
  "tests/",
  "openspec/changes/extension-manifest-schema-2/",
  "openspec/changes/archive/",
  "openspec/specs/extension-manifest/",
]
acceptance = [
  "the change extension-manifest-schema-2 has a proposal, a design.md and a delta spec adding the extension-manifest capability; every scenario in the delta spec is demonstrated by a test whose docstring names it; the change is archived with the archive command into openspec/specs/extension-manifest/",
  "a schema-2 manifest parses `[[stage]]` entries — `phase` one of post-gate, pre-gate-warn, pre-gate-stop, and `command` a relative path under `bin/` with no `..`, no absolute path and no bare program name — and `[dependencies].lock` (a relative path under `lock/`), each refused with a message naming the field and the source when malformed",
  "a schema-2 manifest parses `[wraps]` — `product`, `version`, `ecosystem`, `lock` (under `lock/`), `runtime` in the form `<name> >= <version>`, `license` — `[records].kinds`, each of the form `<name>/<kind>@<version>` whose `<name>` is the manifest's own name, and `[isolation]` — `network` (boolean), `env` (variable names), `writes` (none or process-log), `timeout_seconds` (an integer above zero); each refused with a message naming the field and the source when malformed",
  "every schema-2 field in a schema-1 manifest is refused as requiring schema 2; in schema 2 `install` and `remove` are optional; schema-1 manifests parse exactly as before; schema 3 is an unknown manifest schema; the parsed manifest exposes the new fields to later tasks",
  "nothing reads the new fields yet — the gate, the brief and review behave as before and the gate's fixtures are unchanged — and the full CI sequence passes",
]
documents = ["openspec/specs/extension-manifest/"]
+++

# CR-152: extension manifest schema 2

## Context

ADR-0013 (with its 2026-10-03 amendments) gives an extension a manifest of
schema 2: the stages it runs at and how, its dependency lock, the product it
wraps and that product's verified version, the `ext` record kinds it
declares, and the isolation it asks for. ADR-0022 numbers it 2. Today the
parser knows only schema 1, the manifest-only form. This task parses
schema 2 in the file form that exists today; the directory form, running
stages, trust and doctor are later tasks.

## Objective

A schema-2 manifest is read and validated, and every later extension task
has its fields to work with.

## Acceptance Criteria

As in the header.

## Non-Goals

- The directory form (`<name>/manifest.toml`, `bin/`, `lock/` on disk).
- Running anything, trust, switches, doctor, personal scope.
- Checking that a named file under `bin/` or `lock/` exists.
