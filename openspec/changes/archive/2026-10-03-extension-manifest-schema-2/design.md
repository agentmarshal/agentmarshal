## Context

`parse_extension_manifest_text` in `src/agentmarshal/journal/extensions.py`
validates a manifest already read from a trusted source: schema exactly 1,
the declared name matching the file's, `footprint`, `documents` and
`artifacts` in scope syntax with the latter two under the footprint, and
`install`/`remove` as non-empty strings. Its readers are `brief`, `review`
and the gate; the gate reads `footprint` and `documents` only.

ADR-0013's amended manifest example is the wrapper form: `[[stage]]` with
`phase` and `command`, `[dependencies]` with the adapter's lock under
`lock/`, `[wraps]` with six fields, `[records].kinds` and `[isolation]` with
four fields. ADR-0022 numbers that manifest schema 2. This task parses the
sections in the single-file manifest that exists today; the directory form
they describe is a later task.

## Goals

- A schema-2 manifest parses every section ADR-0013's example carries, and
  the parsed `ExtensionManifest` exposes them for later tasks.
- Every malformed field is refused at the boundary with a message naming the
  field and the source — the existing style.
- The schema ladder holds: the schema-2 fields refuse in a schema-1 manifest
  as requiring schema 2, schema 3 is unknown, and schema-1 manifests parse
  exactly as before.

## Non-Goals

- The directory form (`<name>/manifest.toml`, `bin/`, `lock/` on disk).
- Running anything, trust, switches, doctor, personal scope.
- Checking that a named file under `bin/` or `lock/` exists — the manifest
  declares the path; existence is a later task's check.
- Any reader of the new fields.

## Decisions

- **Each section is optional, and complete when present.** A native
  extension has no `[wraps]`; a manifest without commands has no
  `[[stage]]`. A section that is present is validated in full — every field
  it declares is required — matching how the schema-1 fields are required
  today.
- **The schema-1 field set stays required, minus three relaxations.**
  `name`, `version`, `footprint` and `documents` keep their schema-1
  requiredness in schema 2: the file form is the shared form, and a shared
  extension declares a footprint and named documents. `install`, `remove`
  and `artifacts` relax to optional — ADR-0013's wrapper example carries
  none of them, `install`/`remove` stay recorded declarations the tool
  never runs, and an extension without artifact paths declares no
  `artifacts`. A present `artifacts` is validated exactly as in schema 1.
- **`command` and the locks name a plain file under a declared directory.**
  `command` names only a file in the `bin/` of its own directory — the
  `PATH` ban of ADR-0013 D13 — and each `lock` names one under `lock/`. The
  existing `validate_scope_entry` supplies the relative-path, no-dot
  component and control-character refusals; on top of it the first path
  component must be the declared directory and a non-empty filename must
  follow, so a bare program name is refused. The allowed character set is
  ASCII letters, digits, `_`, `.`, `-` and `/` — a plain relative path,
  never whitespace or a shell metacharacter, because the core runs a
  command as an argv path, never through a shell; the locks share the rule
  because the spec validates them exactly as a `command`.
- **Every schema-2 free-text string passes the control-character rule.**
  Field by field, a schema-2 manifest's strings are checked as follows:
  `name` — a non-empty string equal to the manifest's file name, which
  `extension_manifest_path` has already put through the rule; `version` —
  `_require_text` under schema 2, `_require_string` under schema 1 exactly
  as before; `footprint`, `documents` and `artifacts` entries —
  `validate_scope_entry`, which ends in the rule; a present `install` or
  `remove` — `_require_text`; a `stage` entry's `phase` — membership of the
  three-literal set, which no control character passes — and its `command` —
  `validate_scope_entry` plus the `_PLAIN_PATH` alphabet with `bin/` as the
  first component; `[dependencies].lock` and `[wraps].lock` — the same check
  with `lock/` as the first component; `[wraps]`'s `product`, `version`,
  `ecosystem`, `runtime` and `license` — `_require_text`; `[records].kinds`
  entries — `reject_control_characters` plus the `<name>/<kind>@<version>`
  form; `[isolation]`'s `env` entries — the `_ENV_NAME` alphabet — and its
  `writes` — membership of a two-literal set, while `network` and
  `timeout_seconds` are a boolean and a positive integer, not strings. So no
  text the manifest declares can forge a line when a later task renders it,
  and the refusal names the field and the source — for the fields two
  sections carry, the section too: `[dependencies].lock`, `[wraps].lock` and
  `[wraps].version`.
- **`runtime` keeps the ADR's exact shape.** `<name> >= <version>` — three
  whitespace-separated tokens with `>=` in the middle — because the manifest
  declares a minimum, never a pin; the wrapped product itself comes only
  from its lock.
- **A declared kind names this extension.** `[records].kinds` entries have
  the `ext` form `<name>/<kind>@<version>` (ADR-0022 section 3), and
  `<name>` must be the manifest's own — an extension declares only its own
  kinds.
- **`env` entries are variable names.** `[A-Za-z_][A-Za-z0-9_]*`, a name a
  later runner can pass through — never a value, so a manifest cannot smuggle
  a secret into the environment list.
- **The schema ladder works as the contract header's does.** `schema` is the
  integer 1 or 2; the five new top-level keys refuse under schema 1 with
  "requires schema 2" — the contract-header phrasing applied to the
  manifest — and `install`/`remove` keep their schema-1 requiredness under
  schema 1 only.
