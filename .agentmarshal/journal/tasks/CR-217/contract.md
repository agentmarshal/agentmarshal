+++
schema = 2
id = "CR-217"
title = "Shared extension switches are read from the base: stage run reports a switched-off extension instead of running it, and doctor shows it"
scope = [
  "src/agentmarshal/switches.py",
  "src/agentmarshal/stages.py",
  "src/agentmarshal/doctor.py",
  "tests/",
  "openspec/changes/shared-extension-switches/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "the change shared-extension-switches has a proposal, a design.md and a delta spec on the capability extension-stages with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`.agentmarshal/switches.toml` — `format = 1` and, per extension name, `state` (`on` or `off`), `reason` (required when `off`, at most 1000 characters, passing the forgeable-text rule) and `task` (the operational CR that set it, `CR-<n>`) — is parsed by one function; a malformed file, an unknown format or an entry naming no shared extension is refused naming the file and the entry",
  "`stage run` reads the switches from the base commit, never from the candidate (ADR-0013 decision 6), and for an extension switched off prints `switched off (<task>, <reason>)` as its one result line and does not run it; a switched-off `pre-gate-stop` extension does not pause the process; a malformed switches file at the base is reported on one line and no stage of an extension it names runs",
  "`doctor` shows each switched-off shared extension with its task and reason, read from the working tree; a project without `switches.toml` shows nothing new and every extension is on",
  "every value from the file is escaped on display; the gate is unchanged (the operational lane is a later task); no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-stages/"]
decisions = ["ADR-0013", "ADR-0014", "ADR-0022"]
+++

# Shared extension switches

## Context

ADR-0013 decision 16: switches live apart from the manifest; a shared
extension is switched off only by an operational CR — neither a flag nor a
local setting can switch it off for a run. Decision 17: the operational CR
touches only `.agentmarshal/switches.toml` (name → on/off, reason), and
`status` and `doctor` show "switched off since CR so-and-so, reason".
Decision 6: switches are read from the base. Decision 7: a switched-off
extension still gets a result line. ADR-0022 section 7 gives the file's
shape; ADR-0014 places it. CR-211 runs stages.

Opening the operational CR (`extension switch off`), the gate's operational
lane and personal switches are later tasks.

## Objective

A shared extension switched off by an operational CR is visibly not run,
everywhere it would have run.

## Acceptance Criteria

As in the header.

## Non-Goals

- Personal switches, `--skip-ext`, `extension disable/enable` (with personal
  extensions, a later task).
- `extension switch off` and the gate's operational lane (later tasks).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
