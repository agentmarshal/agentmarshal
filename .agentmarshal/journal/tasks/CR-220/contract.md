+++
schema = 2
id = "CR-220"
title = "agentmarshal extension switch off <name> --reason opens an operational task and writes the switch for it into switches.toml"
scope = [
  "src/agentmarshal/extension_trust.py",
  "src/agentmarshal/switches.py",
  "src/agentmarshal/switch_off.py",
  "tests/",
  "openspec/changes/extension-switch-off/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "the change extension-switch-off has a proposal, a design.md and a delta spec on the capability extension-stages with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal extension switch off <name> --reason <text>` opens a task through the existing `open_task` — a contract whose title names the extension, whose scope is exactly `[\".agentmarshal/switches.toml\"]` and whose acceptance says the extension is switched off with the reason — and writes into the working tree's `.agentmarshal/switches.toml` (creating it with `format = 1` and a `[switches]` table when absent) the entry `state = \"off\"`, `task = <the opened task's id>`, `reason = <text>`, leaving every other entry and the file's other content as they were; it prints the contract and record paths as `open` does, then the switches file's path, and commits nothing (ADR-0013 decisions 16 and 17)",
  "the written file is parsed back by CR-217's parser before the command reports success; the name must be a shared extension the working tree declares (file or directory form) and the reason must pass the parser's own reason rule (at most 1000 characters, the forgeable-text rule), each checked before anything is written; an extension already switched off is refused naming the task that switched it off; a malformed existing switches file is refused naming it; every refusal before the task is opened writes nothing",
  "the switches file is replaced atomically (a temporary file in the same directory, then a rename); if writing it fails after the task was opened, the command says so on one line naming the opened task and exits non-zero rather than leaving the task unmentioned; in a sidecar the command refuses with a line saying operational tasks are not available in a sidecar, writing nothing",
  "every value shown is escaped on display; `extension trust`, `untrust` and `list` are unchanged; the gate and `stage run` are unchanged; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-stages/"]
decisions = ["ADR-0013", "ADR-0014", "ADR-0022"]
+++

# extension switch off

## Context

ADR-0013 decision 16: a shared extension is switched off only by an
operational CR. Decision 17: the operational CR touches only
`.agentmarshal/switches.toml` (name → on/off, reason) and its own task's
records; the reason is mandatory; it is opened with one command —
`agentmarshal extension switch off <name> --reason "…"`. CR-217 parses the
file and reads it from the base; the gate's operational lane is a parallel
task (it admits a candidate that opens its own task and changes only the
switches file).

## Objective

One command produces the whole operational change for a developer to
commit and send through the gate.

## Acceptance Criteria

As in the header.

## Non-Goals

- `switch on` (switching back on is an edit of the file in an operational
  task; a command for it is a later task), personal switches, `--skip-ext`.
- Committing, pushing or opening a pull request.
- The gate's operational lane (a parallel task).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
