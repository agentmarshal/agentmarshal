## 1. The section

- [x] 1.1 `doctor` discovers the shared extensions under
  `.agentmarshal/extensions/` — `<name>.toml` file form, `<name>/`
  directory form, link entries kept under their name — and prints one
  line per name on stderr: name, form, manifest schema, stages' modes,
  declared `ext` kinds — verify: tests.
- [x] 1.2 A directory-form extension's line carries the clone's grant
  state by the `extension list` computation (`_read_grants`,
  `_hash_directory`, `_changed_after_approval`): `granted`,
  `not granted`, `changed after approval` naming the file — verify:
  tests.
- [x] 1.3 With no `.agentmarshal/extensions/` directory the section
  prints one line saying there are no extensions and the rest of
  `doctor`'s output is unchanged — verify: tests.
- [x] 1.4 A link entry is named, never hashed through; an unhashable
  directory carries the reason in its grant position; an unreadable
  grants file or unresolved local state marks the grant position
  unavailable — verify: tests.

## 2. The checks

- [x] 2.1 `doctor_checks` adds one `extension manifest <name>` check
  per discovered name, failing with the reader's reason the way a
  malformed project setting fails its own check — verify: tests.
- [x] 2.2 A listing that cannot be produced fails one
  `extension manifests` check naming the reason; a project that
  cannot be found marks the section unavailable — verify: tests.

## 3. The change itself

- [x] 3.1 proposal.md, design.md, tasks.md and the extension-manifest
  delta spec are written — verify: openspec validate.
- [x] 3.2 Every scenario in the delta spec is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against
  the spec's scenario headings.
- [ ] 3.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-manifest/spec.md` gains each new
  requirement once and the change lives under
  `openspec/changes/archive/`.
