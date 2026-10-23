## 1. The hashing core

- [x] 1.1 `extension_trust.py` computes each regular file's sha256 under
  `.agentmarshal/extensions/<name>/` by sorted relative path and one
  directory hash over the sorted path–hash list — verify: hash tests.
- [x] 1.2 The walk refuses a symlink at any depth and a non-regular file,
  naming the relative path, and refuses a symlinked `<name>` directory —
  verify: tests.

## 2. trust.toml

- [x] 2.1 `format = 1`, `[grants.<name>]` with `directory_hash`,
  `granted_by`, `granted_by_source`, `granted_at` and a `.files`
  sub-table; a minimal serializer writes it, `tomllib` reads it —
  verify: round-trip test.
- [x] 2.2 Written atomically under `LocalState.trust_file`; malformed,
  unknown-format and missing-format reads refuse naming the file —
  verify: tests.

## 3. The command group

- [x] 3.1 `trust` grants (replacing an earlier grant), resolving
  `resolve_recorded_by` and refusing when none resolves — verify: tests.
- [x] 3.2 `untrust` removes a grant and refuses a name with none —
  verify: tests.
- [x] 3.3 `list` prints granted / not granted / changed after approval
  naming the first differing file and never writes — verify: tests.
- [x] 3.4 `register`/`run` land the `extension` group in `cli.py` the way
  `step` is — verify: parser test.
- [x] 3.5 One `trust-changed` event per grant and per removal;
  `extension`, `action`, `directory_hash` — verify: event tests.

## 4. The change itself

- [x] 4.1 proposal.md, design.md, tasks.md and the extension-trust delta
  spec are written — verify: openspec validate.
- [x] 4.2 Every scenario in the delta spec is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against
  the spec's scenario headings.
- [x] 4.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-trust/spec.md` exists and the change lives
  under `openspec/changes/archive/`.
