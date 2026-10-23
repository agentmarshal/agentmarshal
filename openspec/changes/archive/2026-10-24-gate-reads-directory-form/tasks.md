## 1. The tree reader

- [x] 1.1 `_manifest_from_tree` finds `<name>/manifest.toml` as well as
  `<name>.toml`, refuses both for one name naming both, and reports
  neither as missing — verify: tests.
- [x] 1.2 A symbolic-link entry at either manifest path, or at the
  `<name>` directory, is refused as a link — before absence is decided —
  and a non-blob entry at a manifest path is refused — verify: tests.
- [x] 1.3 The directory form at the base requires `schema = 2` —
  verify: test.
- [x] 1.4 A contract naming only file-form extensions, or none, produces
  today's transcript byte for byte — verify: the pinned fixtures and the
  existing suite.

## 2. Removal

- [x] 2.1 A candidate deleting `<name>/manifest.toml` is recognised as
  removing `<name>` and its former footprint is checked the same way —
  verify: tests.
- [x] 2.2 A deletion of another file under `<name>/` — `bin/`, `lock/` —
  is not a removal — verify: test.

## 3. The change itself

- [x] 3.1 proposal.md, design.md, tasks.md and the extension-manifest
  delta spec are written — verify: openspec validate.
- [x] 3.2 Every scenario in the delta spec is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against the
  spec's scenario headings.
- [x] 3.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-manifest/spec.md` gains each new requirement
  once and the change lives under `openspec/changes/archive/`.
