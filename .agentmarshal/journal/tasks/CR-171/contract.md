+++
schema = 2
id = "CR-171"
title = "open, amend and migrate pin the contract's hash; open can take a contract already written; status says when the contract drifted from its last pin"
scope = [
  "src/agentmarshal/journal/open_task.py",
  "src/agentmarshal/cli.py",
  "src/agentmarshal/migrate.py",
  "src/agentmarshal/journal/status_view.py",
  "tests/",
  "docs/quickstart.md",
  "openspec/changes/pin-contract-hash/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change pin-contract-hash has a proposal, a design.md and a delta spec modifying contract-governance (ADDED requirements for the writers, `--contract-file` and the drift line; MODIFIED with exact headers where one becomes untrue); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal open` writes `contract` — the `contract_sha256` of the contract it writes — in its `opened` record, which is therefore schema 7; `agentmarshal open --contract-file <path>` takes a contract already written (header and body), validates its header as `parse_contract_text` does, sets the header's `id` to the assigned task id (naming on stderr any different value it replaced) — rewriting it where it is written as the key `id`, `\"id\"` or `'id'` with a one-line string value on a line of its own in the header's top-level table, and refusing, with a message naming those forms and writing nothing, a valid contract that writes its `id` any other way (an escaped key, a value spanning lines), writes it as the task's contract and pins its hash; `--contract-file` refuses to be combined with `--title` or `--scope`, and refuses a file that is missing, unreadable or not a valid contract, writing nothing",
  "`agentmarshal amend` pins the `contract_sha256` of the task's contract.md as it is at that moment (in a sidecar, the journal repository's copy) and refuses a contract that does not parse; `migrate` pins the hash of each contract it writes",
  "`agentmarshal status <task>` prints one line when the contract's current hash differs from the hash in the task's latest `opened` or `amendment` record that carries one — naming both short hashes and that the edit should be recorded with `amend` — and nothing when they match or no record carries a hash; it never fails because of the drift",
  "docs/quickstart.md shows opening a task from a contract written first (`open --contract-file`) as the main path and says what happens when a contract is edited after `open`; the documented transcripts a test pins still match; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
+++

# CR-171: pinning the contract's hash where it is written

## Context

ADR-0018 decision 1: the `opened` record and every `amendment` carry the
sha256 of the contract text they establish. CR-163 gave the one hash
function and the field (schema 7). The documented flow — `open`, then fill
the contract, then commit — would pin the empty template, so the operator
decided (2026-10-03): `open --contract-file` takes a contract written first
and pins its real hash; `open` without it keeps pinning what it writes, an
edit before the opening commit is recorded with `amend`, and `status`
reminds when the contract and its last pin differ; the quickstart shows the
file path. From this task on, every new task's `opened` record is schema 7 —
the coordinated upgrade of ADR-0022.

## Objective

Every contract a task establishes is pinned by its hash, and a drift is
visible.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any gate check of the hash or of agreement (later tasks).
- Recomputing hashes in existing records.
- Changing README.md, docs/sidecar.md or docs/self-hosting-workflow.md (their
  `open --title` examples stay true).
