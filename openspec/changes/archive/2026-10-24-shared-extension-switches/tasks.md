## 1. The file and its parser

- [x] 1.1 `switches.py` parses `.agentmarshal/switches.toml` — `format = 1`,
  `[switches.<name>]` entries of `state` (`on`/`off`), `task` (`CR-<n>`)
  and `reason` (required when `off`, refused when `on`, at most 1000
  characters, forgeable-text clean) — fail-closed, refusing a malformed
  file, an unknown or missing format, a non-table `switches`, a non-table
  entry, an entry naming no shared extension the caller knows, or a
  field outside its shape, each naming the file and where one exists the
  entry; `SwitchesError` carries the entry names the file declares —
  verify: parser tests.
- [x] 1.2 `read_switches` reads the working-tree file — a missing file
  is every extension on — and `SwitchesError.names` is `None` when the
  file's own entries cannot be enumerated — verify: tests.

## 2. `stage run`

- [x] 2.1 The base enumeration lists every shared extension's name in
  both forms — directory trees and `<name>.toml` blobs — keeping the
  link refusals — verify: tests.
- [x] 2.2 `_base_switches` reads the file at the merge base — missing
  is all-on, a link or non-blob at its path is the file's own
  malformation — and parses it against the base's names — verify: tests.
- [x] 2.3 A stage of a switched-off extension prints
  `<name>: switched off (<task>, <reason>)` and never runs — no
  materialization, no grant check, no pause for `pre-gate-stop`, no
  warning for `pre-gate-warn`; its `extension-event` carries decision
  `switched-off` — verify: tests.
- [x] 2.4 A switches file the parse refuses is reported on one stderr
  line and no stage of an extension it names runs — each is
  `not run (shared switches file unreadable)`; an unreadable file
  leaves every stage `not run` — verify: tests.

## 3. `doctor`

- [x] 3.1 The extensions section reads the working-tree
  `switches.toml` and shows each switched-off shared extension —
  `switched off since <task> (<reason>)` — on its line, both forms
  and the unreadable-manifest line alike — verify: tests.
- [x] 3.2 No file shows nothing new; a file the parse refuses is named
  on one `switches: unavailable` line and fails no check — verify:
  tests.

## 4. The change itself

- [x] 4.1 proposal.md, design.md, tasks.md and the extension-stages
  delta spec are written — verify: openspec validate.
- [x] 4.2 Every scenario in the delta spec is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against
  the spec's scenario headings.
- [x] 4.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-stages/spec.md` gains each new
  requirement once and the change lives under
  `openspec/changes/archive/`.
