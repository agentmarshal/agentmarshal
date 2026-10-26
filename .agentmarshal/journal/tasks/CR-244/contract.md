+++
schema = 2
id = "CR-244"
title = "The guides under docs/ state what 0.6.0 does: record types, the user scope, versions, quoted output, the operational lane's contract source, and the threat model's write-time and outbox protections"
scope = [
  "docs/",
  "CONTRIBUTING.md",
]
acceptance = [
  "docs/known-defects.md names the record types the 0.6.0 registry declares (attestation.py RECORD_TYPES; thirteen), not nine (release-audit finding AUD-docs-claims-2-1)",
  "docs/harness-setup.md no longer says user-level directories (~/.config/agentmarshal, ~/.local/share/agentmarshal) hold trust, switches or extension code in 0.6.0: the user scope is decided but not implemented (ADR-0014, CHANGELOG); trust, switches and personal extensions live under the clone's local state (.git/agentmarshal/) (AUD-docs-claims-2-2)",
  "where docs/ says a contract is read only from the base and never from the candidate (threat-model ~23 and ~228, self-hosting-workflow ~155 and any other place), it also states the one exception the code and the gate-lanes spec make: a switches-only operational task's opening contract is read from the candidate, under the conditions gate.py checks (found by the interrupted docs-claims-2 run)",
  "docs/threat-model.md lists, among write-time protections, the timestamp fields and review artifact references CR-236 refuses, and, among the outbox's protections, the refusals CR-241 added (a symlinked outbox or path component; staged bytes that differ from the checked bytes); its sidecar paragraph quotes the lines the tool prints (AUD-docs-claims-2-7, -8)",
  "docs/quickstart.md and docs/sidecar.md pin and describe 0.6.0 where they pinned 0.5.0 or 0.4.1, sidecar's transcripts match what 0.6.0 prints and its doctor note says doctor resolves the placement but checks nothing about the host; docs/github-enforcement.md quotes the gate's closing line exactly; docs/self-hosting-workflow.md and docs/templates/ no longer describe am-merge, mr.sh or scripts as files in this repository (they are operator tooling outside it) (AUD-docs-claims-2-3 to -6, AUD-whole-project-3, -4)",
  "every statement is checked against the code at master; dated history notes are not rewritten; every link resolves; no file outside docs/ and CONTRIBUTING.md changes (CONTRIBUTING.md only for the base-only contract sentence, which gets the operational-lane exception); the suite and the full CI sequence pass",
]
documents = ["docs/"]
decisions = ["ADR-0013", "ADR-0014"]
+++

# Documentation claims, part 2 (docs/)

## Context

Release audit 0.6.0, docs-claims part 2: two astra runs hit the 5-hour
Codex window with no result (the second, before it stopped, flagged the
operational lane's contract source); the operator moved the area to Claude
Fable, which reported two blocking false statements (record type count;
user-level directories) and seven advisory ones. The whole-project Fable
pass of 25.10 flagged the same version pins.

## Objective

A reader of any guide under docs/ learns what 0.6.0 does.

## Acceptance Criteria

As in the header.

## Non-Goals

- The extension-stages spec scenario wording about trust.toml (a spec
  change; 0.7.0).
- brief.py's wording (code; 0.7.0).
- docs/proposals/ (CR-243 handled them).
