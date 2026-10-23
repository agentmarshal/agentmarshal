## 1. The runtime check

- [x] 1.1 `_extension_checks` reads each discovered manifest and adds
  one `extension runtime <name>` check beside the manifest check for
  each extension declaring `[wraps].runtime` — none for a manifest
  without `[wraps]` or one that cannot be read — verify: tests.
- [x] 1.2 The check resolves the declared `<name>` through the same
  injected resolver the git check uses (`shutil.which` by default) and
  runs the resolved path with `--version` as an argv call — never
  `shell=True` — under a short time limit — verify: tests putting a
  fake runtime on a temporary `PATH`.
- [x] 1.3 The version is read as the first run of numeric
  dot-separated components in the answer, a leading `v` ignored, and
  compared component by component against the declared minimum — an
  unreadable answer reported unreadable rather than guessed; not
  found, failed, timed out, unreadable and below-minimum each fail
  the check naming what it learned — verify: tests.
- [x] 1.4 Every value a result names is escaped on display — verify:
  tests.

## 2. The change itself

- [x] 2.1 proposal.md, design.md, tasks.md and the extension-manifest
  delta spec are written — verify: openspec validate.
- [x] 2.2 Every scenario in the delta spec is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against
  the spec's scenario headings.
- [x] 2.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-manifest/spec.md` gains each new
  requirement once and the change lives under
  `openspec/changes/archive/`.
