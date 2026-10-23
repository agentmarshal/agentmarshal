+++
schema = 2
id = "CR-180"
title = "agentmarshal agree records that the recorder agrees with the task's contract at its current hash"
scope = [
  "src/agentmarshal/agree.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/agree-command/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change agree-command has a proposal, a design.md and a delta spec on the capability contract-governance with ADDED requirements for the command; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal agree --task <id>` writes one `agreement` record whose `contract` is the hash of the task's contract as it now stands, computed by `contract_sha256` — the function `open` and `amend` pin with — and prints that hash and the recorder; the command is registered from its own module the way the `step` group is",
  "with `--contract <hash>` the command writes only when the given hash equals the current one; otherwise it refuses naming both hashes, so an actor can agree with exactly the text it read",
  "the command refuses, writing nothing and exiting non-zero with a message naming the reason, when: the task is unknown; the task is completed or abandoned; the contract's current hash differs from the task's latest pinned hash (the latest `opened` or `amendment` record that carries one), naming both short hashes and that the edit is recorded with `amend` first; no recorder identity can be resolved; a recorder that is not a declared actor is accepted and the output says it is not a declared actor",
  "recording agreement again on the same task is allowed; no other command's behaviour or output changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
decisions = ["ADR-0018", "ADR-0022"]
+++

# agentmarshal agree

## Context

ADR-0018 decision 2: a declared actor can record agreement with the
contract at a stated hash; any declared actor may, there are no roles, and
the gate does not require the record by default. ADR-0022 section 3 gives
the `agreement` record (`contract`, `recorded_by` required) and admits a
recorder that is not a declared actor. CR-177 landed the record; nothing
writes it yet. `open --contract-file` (CR-171) pins the hash of the text
the task opens with, `amend` pins every later text, and `status` already
reports drift between the current text and the latest pin.

Agreeing with a text that no record pins would be agreement with something
the journal cannot name, which is why a drifted contract is refused until
`amend` records the edit. A task opened before contract hashes existed has
no pin; agreement then pins the current text and the refusal does not apply.

## Objective

An actor can put its agreement with a task's contract on the record with
one command, bound to the exact text.

## Acceptance Criteria

As in the header.

## Non-Goals

- The gate's `require_agreement` check, and `status` showing agreement and
  the declared assignment (later tasks).
- Roles, or any rule about who may agree (ADR-0018 decision 2).
- Documentation of the command in the quickstart or release notes (the
  release documentation task).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
