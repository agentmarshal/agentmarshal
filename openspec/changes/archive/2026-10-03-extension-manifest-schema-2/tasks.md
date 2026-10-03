## 1. The parser

- [x] 1.1 `ExtensionManifest` exposes `stages`, `dependencies`, `wraps`,
  `record_kinds` and `isolation`, each absent by default, with the
  supporting dataclasses — verify: a schema-2 parse test.
- [x] 1.2 The schema check admits 2; schema 3 is refused as an unknown
  schema version — verify: test.
- [x] 1.3 Each of `stage`, `dependencies`, `wraps`, `records` and
  `isolation` in a schema-1 manifest is refused with a message naming the
  field as requiring schema 2 — verify: a test parametrized over the field.
- [x] 1.4 `[[stage]]` parses `phase` from `post-gate`, `pre-gate-warn`,
  `pre-gate-stop` and `command` under `bin/`; a malformed `stage`, a phase
  outside the three, an absolute command, a `..` command and a bare program
  name are each refused naming the field and the source — verify: tests.
- [x] 1.5 `[dependencies].lock` and `[wraps].lock` parse only as relative
  paths under `lock/` — verify: tests.
- [x] 1.6 `[wraps]` requires `product`, `version`, `ecosystem`, `lock`,
  `runtime` in `<name> >= <version>` form and `license` — verify: tests.
- [x] 1.7 `[records].kinds` entries parse as `<name>/<kind>@<version>`
  naming the manifest's own name — verify: tests.
- [x] 1.8 `[isolation]` requires a boolean `network`, `env` variable names,
  `writes` of `none` or `process-log` and an integer `timeout_seconds` above
  zero — verify: parametrized tests.
- [x] 1.9 `install`, `remove` and `artifacts` are optional in schema 2, all
  three required in schema 1 — verify: tests.
- [x] 1.10 `command` and each `lock` are plain relative paths — no
  whitespace or shell metacharacters — refused naming the field and the
  source — verify: parametrized tests.
- [x] 1.11 Every free-text field of a schema-2 manifest — the `[wraps]`
  strings, `[records].kinds` entries and a present `install`/`remove` —
  passes the control-character rule, refused naming the field and the
  source — verify: parametrized tests.

## 2. The change itself

- [x] 2.1 proposal.md, design.md, tasks.md and the extension-manifest delta
  spec are written — verify: openspec validate.
- [x] 2.2 Every scenario in the delta spec is demonstrated by a test whose
  docstring names it — verify: grep the test docstrings against the spec's
  scenario headings.
- [x] 2.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-manifest/spec.md` exists and the change lives
  under `openspec/changes/archive/`.
