# Tasks

## 1. Implementation

- [x] 1.1 `src/agentmarshal/journal/validate.py`: a
  `_addressee_warnings` helper run per task after the `OK`/`FAIL`
  lines — for each `ext` record, resolve `<name>`'s manifest through
  `read_extension_manifest` (the file form or the directory form),
  lazily and cached by name across tasks; a kind the manifest does not
  declare draws `WARN: <task>: ext record <id> kind '<kind>': addressee
  not found`; a missing manifest declares nothing silently, a manifest
  that cannot be read is named once on a WARN line of its own and
  declares nothing; every contributed value passes through
  `escape_for_display`; `passed` is never touched and a journal with no
  `ext` records reads no manifest.

## 2. Tests

- [x] 2.1 `tests/test_validate_addressee.py`: a test per delta-spec
  scenario, each docstring naming the scenario — the addressee warning
  on a missing manifest and on an undeclared kind, the declared kinds in
  the file and the directory form, the unreadable manifest named once
  across tasks, the unchanged verdict and exit status, the journal with
  no `ext` records pinned byte for byte with the manifest reader armed,
  and the escaped value on the warning line.

## 3. Change and archive

- [x] 3.1 `openspec/changes/validate-addressee-not-found/`:
  proposal.md, design.md, tasks.md, and the delta spec under
  `specs/extension-records/` — the ADDED requirement and the MODIFIED
  requirement whose "`validate`'s warning comes with its own task"
  tail is now stale.
- [x] 3.2 `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.13.2
  archive validate-addressee-not-found --yes`, once implementation and
  tests are complete.
