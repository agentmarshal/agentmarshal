+++
schema = 2
id = "CR-202"
title = "When the project requires agreement, the gate refuses a candidate whose task holds no agreement with the contract it judges against"
scope = [
  "src/agentmarshal/journal/gate.py",
  "tests/",
  "openspec/changes/gate-requires-agreement/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change gate-requires-agreement has a proposal, a design.md and a delta spec on the capability contract-governance with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "when the project's `contract.require_agreement` is true — read from the same project file the gate reads its other settings from — the gate checks that the task's records hold an `agreement` whose `contract` equals the hash, by `contract_sha256`, of the contract the gate judges against (the trusted side it reads today), and prints one PASS or FAIL line naming the short hash; a FAIL says the agreement is recorded with `agentmarshal agree`",
  "an agreement with an earlier text of the contract does not satisfy the check — the FAIL line says an agreement exists for another hash and names both short hashes; any recorder satisfies it (no roles, ADR-0018 decision 2)",
  "when the setting is false or absent (the default) the gate prints no new line and its transcript is byte for byte today's, which the pinned default transcript and the fixtures demonstrate; an unreadable setting is reported the way the gate already reports an unreadable threshold, and does not pass silently",
  "no other gate check changes; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
decisions = ["ADR-0018", "ADR-0022"]
+++

# The gate can require agreement

## Context

ADR-0018 decision 2: the gate does not require the agreement record by
default; a project whose rules demand agreement can make it required.
ADR-0022 section 6 gives the key `contract.require_agreement` (default
false), landed in CR-151; CR-177 landed the record and CR-180 the `agree`
command, which pins the contract's current hash. The gate reads the
contract from the trusted side (the merge-base tree, or the sidecar's
working tree) and computes hashes with `contract_sha256` since CR-163.

## Objective

A project that requires agreement gets it enforced at the merge boundary,
bound to the exact text the gate judges against.

## Acceptance Criteria

As in the header.

## Non-Goals

- Roles or any rule about who may agree.
- Membership in the contract's `reviewers` list (a later task, after an
  operator decision).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
