## 1. One enumeration

- [x] 1.1 `doctor` enumerates through
  `sorted(shared_extension_names(managed))` at both sites and
  `_extension_names` is removed — verify: the existing doctor tests
  pass unchanged.

## 2. `status`

- [x] 2.1 `_run_status` prints, right after `print_paths` and in the
  listing and the single-task view alike, one
  `switched off: <name> since <task> (<reason>)` line per shared
  extension the working tree's `switches.toml` switches off — the file
  read through `read_switches`, the names from
  `shared_extension_names`, every value escaped — before anything that
  can return early — verify: tests.
- [x] 2.2 No file or nothing switched off prints nothing new; a file
  the parse refuses is named on one
  `switches: unavailable (<reason>)` line and changes neither the exit
  status nor stdout — verify: tests.

## 3. The change itself

- [x] 3.1 proposal.md, design.md, tasks.md and the extension-stages
  delta spec are written — verify: openspec validate.
- [x] 3.2 Every scenario in the delta spec is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against
  the spec's scenario headings.
- [x] 3.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-stages/spec.md` gains each new requirement
  once and the change lives under `openspec/changes/archive/`.
