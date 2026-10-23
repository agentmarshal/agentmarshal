+++
schema = 2
id = "CR-222"
title = "status names each switched-off shared extension with its task and reason, and doctor enumerates extensions with the shared rule CR-220 introduced"
scope = [
  "src/agentmarshal/cli.py",
  "src/agentmarshal/doctor.py",
  "tests/",
  "openspec/changes/status-shows-switches/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "the change status-shows-switches has a proposal, a design.md and a delta spec on the capability extension-stages with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal status` — the listing and the view of one task alike — prints on stderr, after the lines naming where the journal, the process log and the local state live, one line per shared extension the switches file switches off: `switched off: <name> since <task> (<reason>)` (ADR-0013 decision 17), every value escaped for display; the file is the one `doctor` reads, through the same function, against the names `switches.shared_extension_names` enumerates",
  "stdout is unchanged byte for byte in every case, which the existing status tests demonstrate unchanged; a project with no switches file or with no extension switched off prints nothing new on stderr either; a switches file that cannot be read is named on one stderr line and does not change status's exit status or its stdout",
  "`doctor` enumerates extensions through `switches.shared_extension_names` instead of its own `_extension_names`, which is removed; doctor's output is unchanged byte for byte, which its existing tests demonstrate unchanged",
  "no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-stages/"]
decisions = ["ADR-0013", "ADR-0014"]
+++

# status shows switched-off extensions

## Context

ADR-0013 decision 17: `status` and `doctor` show "switched off since CR
so-and-so, reason". CR-217 gave `doctor` that line; `status` has none.
CR-220 added `switches.shared_extension_names` with exactly doctor's
enumeration rule and left doctor moving onto it as a follow-up, so the rule
lives in one place. `status`'s stdout is a documented parser contract; the
places-of-things lines already go to stderr (ADR-0014 decision 13).

## Objective

Whoever reads `status` sees that a shared check is switched off, by which
task and why, without a second command.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any change to status's stdout.
- Personal switches (a later task).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
