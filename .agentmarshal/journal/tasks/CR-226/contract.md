+++
schema = 2
id = "CR-226"
title = "Documentation catches up with extension execution: the threat model states what now runs and what it does and does not protect, README stages one task's journal, and complete --target is documented"
scope = [
  "docs/threat-model.md",
  "README.md",
  "docs/self-hosting-workflow.md",
  "openspec/changes/extension-stages-purpose/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "docs/threat-model.md no longer says extension execution is decided but not implemented, or that no extension code runs: it states what runs today — `stage run` and `complete` run the stages shared extensions declare, code and switches read from the base, under a local grant on a workstation, the operational lane and accepted pauses — and, for stage isolation, exactly what the core enforces (a new user and network namespace unless `network = true`; at pre-gate a read-only candidate with the mount's locked flags kept and the working directory re-entered; provider-secret names withheld; capabilities dropped before exec), that whatever it cannot enforce is named on the stage's line, that nothing outside the candidate is made read-only, and that a process of the same OS user outside the stage is not contained — each statement checked against the code and naming the extension-stages requirement it rests on, nothing stated as enforced that is not",
  "README.md's recipe stages one task's journal directory (`git add .agentmarshal/journal/tasks/<id>` or the shipped `templates/journal-transaction.sh`) instead of `git add .agentmarshal`, consistent with docs/quickstart.md",
  "docs/self-hosting-workflow.md documents `complete --target <ref>`: what it decides (whether a pausing pre-gate-stop extension pauses the completion or only warns), that `--base` stays the gate's merge base, and that a wrapper completing after the merge passes the target branch",
  "the unarchived change openspec/changes/extension-stages-purpose/ is removed and no OpenSpec file changes; every link added resolves; no other document changes; the suite and the full CI sequence pass",
]
documents = ["docs/threat-model.md", "README.md", "docs/self-hosting-workflow.md"]
decisions = ["ADR-0001", "ADR-0013", "ADR-0014"]
+++

# Documentation: extension execution

## Context

Wave B landed extension execution (CR-209 trust, CR-211 stage run, CR-217
switches, CR-219 operational lane, CR-220 switch off, CR-221 and CR-223
isolation, CR-224 accepted pause, CR-225 complete runs stages). Deferred
advisories: CR-211 ADV-CLAIM-001 and CR-219 OP-3 (the threat model trails
extension execution), CR-207 (README sweeps `.agentmarshal`), CR-225 F5
(`--target` undocumented), CR-224 (the extension-stages Purpose is stale).

## Objective

A reader of the documentation learns what extension execution does and
what it does not protect, as the code does it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Code changes.
- Personal extensions and dependency checks (later tasks).
- Protection beyond what the published decisions promise.
