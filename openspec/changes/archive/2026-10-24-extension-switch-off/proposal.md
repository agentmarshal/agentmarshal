## Why

ADR-0013 decision 16: a shared extension is switched off only by an
operational CR — neither a flag nor a local setting. Decision 17 gives
the operational CR its shape — the diff touches only
`.agentmarshal/switches.toml` (name → on/off, reason) and its own task's
records — makes the reason mandatory, and names the one command that
opens it: `agentmarshal extension switch off <name> --reason "…"`.
CR-217 gave the file a fail-closed parser and its readers — `stage run`
from the base, `doctor` from the working tree — and the gate's
operational lane that admits the diff is a parallel change. Today the
file can be written only by hand and the task opened separately —
nothing produces the whole operational change in one step for a
developer to commit and send through the gate.

## What Changes

- A new `switch` group under `extension`, with `off <name> --reason
  <text>`: it opens the operational task through the journal's own
  `open_task` — a generated contract whose title names the extension,
  whose scope is exactly `[".agentmarshal/switches.toml"]` and whose
  acceptance says the extension is switched off with the reason — and
  writes the switch into the working tree's
  `.agentmarshal/switches.toml` for the task it opened.
- The name is checked to be a shared extension the working tree
  declares (file or directory form), the reason passes the parser's own
  rule — non-empty, at most 1000 characters, the forgeable-text rule —
  and an existing switches file is parsed before the task is opened: a
  malformed file is refused naming it, an extension already switched
  off is refused naming the task that switched it off. Every refusal
  before the task is opened writes nothing.
- The file keeps its text — there is no TOML writer to add one: an
  existing `on` entry's table is replaced, any other extension gains an
  appended `[switches.<name>]` table, and a missing file is created
  with `format = 1` and a `[switches]` table. The whole new text is
  parsed back by CR-217's parser before the file is replaced
  atomically — a temporary file in `.agentmarshal/` renamed over it. A
  failure after the task is opened is reported on one line naming the
  task and exits non-zero.
- The command prints the contract and record paths as `open` does, then
  the switches file's path; it commits nothing. In a sidecar it refuses
  — operational tasks are not available in a sidecar — writing nothing.
  Every value shown is escaped on display.

## Capabilities

- modified: `extension-stages`

## Impact

`src/agentmarshal/switch_off.py` is new — the `switch` group's dispatch
and the `off` subcommand's logic: validation, the generated contract,
the surgical rewrite and the atomic replace.
`src/agentmarshal/extension_trust.py` registers `switch` under the
existing `extension` group and dispatches it; `trust`, `untrust` and
`list` are unchanged. `src/agentmarshal/switches.py` gains no new
rules — its parser is the command's pre-open check and its parse-back
guard. The gate and `stage run` are unchanged — the operational lane
is CR-219 in parallel — and no other command changes. Out of scope by
the contract's own staging: `switch on`, personal switches,
`--skip-ext`, and committing or pushing the change.
