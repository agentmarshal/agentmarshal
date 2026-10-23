## 1. The command surface

- [x] 1.1 `switch` is registered under the existing `extension` group —
  `off <name> --reason <text>` — and `extension_trust.run` dispatches
  it to `switch_off.run` — verify: parser test, `trust`/`untrust`/`list`
  tests unchanged.
- [x] 1.2 A sidecar refuses on one line — operational tasks are not
  available in a sidecar — writing nothing — verify: test.

## 2. `switch_off.py`

- [x] 2.1 Name, reason and the existing file are checked before the
  task is opened — a declared shared extension in either form, the
  parser's reason rule, the shared parser over the existing file, an
  already-off entry refused naming its task, a link at the file's path
  refused — every refusal writing nothing — verify: tests.
- [x] 2.2 The task opens through `open_task` with a generated contract
  passed as `contract_file=` — title naming the extension, scope
  exactly `[".agentmarshal/switches.toml"]`, acceptance saying the
  extension is switched off with the reason — and the replaced-id
  notice prints as `open` prints it — verify: tests.
- [x] 2.3 The file keeps its text — an `on` entry's table replaced, a
  new `[switches.<name>]` appended, the file created with `format = 1`
  and `[switches]` when absent, `reason` quoted as a TOML basic string —
  and the new text is parsed back before replacing — verify: tests.
- [x] 2.4 The replace is atomic — a temporary file in `.agentmarshal/`
  then `os.replace` — and a failure after the task is opened is
  reported on one line naming the task, exit non-zero — verify: tests.
- [x] 2.5 The command prints the contract and record paths as `open`
  does, then the switches file's path, commits nothing, and escapes
  every shown value — verify: tests.

## 3. The change itself

- [x] 3.1 proposal.md, design.md, tasks.md and the extension-stages
  delta spec are written — verify: openspec validate.
- [x] 3.2 Every scenario in the delta spec is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against
  the spec's scenario headings.
- [x] 3.3 The change is archived with the archive command — verify:
  `openspec/specs/extension-stages/spec.md` gains each new requirement
  once and the change lives under `openspec/changes/archive/`.
