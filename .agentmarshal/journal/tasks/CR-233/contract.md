+++
schema = 2
id = "CR-233"
title = "Personal extensions in the clone: stage run and complete run them from .git/agentmarshal/extensions marked personal, with no authority over the journal or the server-side process, and a developer can skip or disable them"
scope = [
  "src/agentmarshal/stages.py",
  "src/agentmarshal/switches.py",
  "src/agentmarshal/extension_trust.py",
  "src/agentmarshal/doctor.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/personal-extensions/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "the change personal-extensions has a proposal, a design.md and a delta spec on the capability extension-stages with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`stage run` (and `complete`, through the shared runner) also runs the stages of personal extensions in the clone — directory-form manifests under `.git/agentmarshal/extensions/<name>/`, located through the local-state paths the code already resolves (ADR-0013 decisions 9–11, ADR-0014) — read from that directory (not from the base), on a workstation only (never in CI), under the same isolation as shared stages and with no local grant required; each result line is marked `personal`; a personal `pre-gate-stop` stage that pauses pauses the local run, marked personal; a personal extension named like a shared one is not run and is named on one line (the shared one wins)",
  "a personal manifest that declares `footprint`, `documents` or `artifacts` is refused by `doctor` and not run (decision 10); a personal extension cannot write `ext` records (`record-ext` accepts only kinds a shared extension declares — unchanged); `doctor` lists personal extensions with the scope `personal`",
  "personal switches (decision 16): `stage run --skip-ext <name>` and `complete --skip-ext <name>` skip a personal extension for that run, printing `<name>: skipped for this run (personal)`; `agentmarshal extension disable <name>` / `enable <name>` write the switch to `.git/agentmarshal/switches.toml` and a disabled personal extension prints `<name>: disabled (personal)`; naming a shared extension in any of these is refused with a line saying a shared extension is switched off only by an operational task (`extension switch off`)",
  "a clone with no personal extension prints exactly what it prints today, which the existing stage, complete and doctor tests demonstrate unchanged; the gate is unchanged; every value is escaped on display; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-stages/"]
decisions = ["ADR-0013", "ADR-0014"]
+++

# Personal extensions

## Context

ADR-0013 decisions 9–11 and 16: the personal-in-clone scope
(`.git/agentmarshal/extensions/<name>/`) adds extensions for one developer
in all their worktrees; a personal extension is invoked at its stage, may
pause a local run (marked personal) but never the server-side process,
writes no `ext` records and has no footprint; it is switched off by a flag
for one run (`--skip-ext`) or until re-enabled (`extension disable`,
`.git/agentmarshal/switches.toml`). The first release with extensions
ships the shared and the personal-in-clone scopes; the user scope waits
for an adopter. The shared runner (CR-211, CR-225), isolation (CR-221,
CR-223) and shared switches (CR-217) are in place.

## Objective

A developer can run their own checks at the declared stages without giving
them any authority over the journal or the merge.

## Acceptance Criteria

As in the header.

## Non-Goals

- The user scope (`~/.config/agentmarshal/extensions/`).
- Installing dependencies.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
