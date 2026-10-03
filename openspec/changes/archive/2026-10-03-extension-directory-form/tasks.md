## 1. The reader

- [x] 1.1 `read_extension_manifest` finds `<name>/manifest.toml` as well as
  `<name>.toml`, refuses both for one name naming both paths, and reports
  neither as `ExtensionManifestMissing` — verify: tests.
- [x] 1.2 Every symlink refusal the file form has applies to the directory
  and to the manifest inside it — verify: tests for a linked `manifest.toml`
  and a linked `<name>` directory.
- [x] 1.3 The directory form refuses `schema = 1` with a message saying the
  directory form requires schema 2 — verify: test.
- [x] 1.4 Each `command` and `lock` a directory-form manifest names must
  exist inside the directory as a regular file — not a symlink, not reached
  through `..` — refused otherwise naming the path — verify: tests.
- [x] 1.5 A schema-2 single file naming a `bin/` or `lock/` path is refused
  naming the path; one declaring none parses as the manifest-only form —
  verify: tests.
- [x] 1.6 `ExtensionManifest` exposes the directory it was read from —
  `None` for the file form and for a parsed manifest — verify: tests.

## 2. The change itself

- [x] 2.1 proposal.md, design.md, tasks.md and the extension-manifest delta
  spec are written — verify: openspec validate.
- [x] 2.2 Every scenario in the delta spec is demonstrated by a test whose
  docstring names it — verify: grep the test docstrings against the spec's
  scenario headings.
- [x] 2.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-manifest/spec.md` gains each new requirement
  once and the change lives under `openspec/changes/archive/`.

## 3. Review fixes

- [x] 3.1 A symlink at the `<name>` directory or at `manifest.toml` —
  dangling or not — is refused as a link before existence is decided; a
  component of the file-form path that is not a directory keeps its
  refusal rather than reporting the manifest missing — verify: tests.
- [x] 3.2 The schema-version requirement says the declared `name` matches
  the extension's name — the file name without `.toml` in the file form,
  the directory name in the directory form — verify: the delta carries it
  as MODIFIED with the exact header.
- [x] 3.3 A `bin/` or `lock/` that is itself a symlink — out of the
  extension directory or dangling — is refused as a link — verify: tests.
