## Why

ADR-0018 decision 1: the `opened` record and every `amendment` carry the
sha256 of the contract text they establish. CR-163 gave the one hash
function and the field (schema 7); no writer sets it yet. The documented
flow — `open`, then fill the contract, then commit — would pin the empty
template, so the operator decided (2026-10-03): `open --contract-file`
takes a contract written first and pins its real hash; `open` without it
keeps pinning what it writes; an edit before the opening commit is
recorded with `amend`; and `status` reminds when the contract and its
last pin differ. From this change on, every new task's `opened` record is
schema 7 — the coordinated upgrade of ADR-0022.

## What Changes

- `agentmarshal open` writes `contract` — the `contract_sha256` of the
  contract it writes — in its `opened` record, which therefore stamps
  schema 7.
- `agentmarshal open --contract-file <path>` takes a contract already
  written (header and body), validates its header as `parse_contract_text`
  does, sets the header's `id` to the assigned task id — naming on stderr
  any different value it replaced — writes it as the task's contract and
  pins its hash. The `id` is rewritten where it is written as `id`,
  `"id"` or `'id'` with a one-line string value on a line of its own in
  the top-level table; a valid contract that writes it any other way is
  refused naming those forms. `--contract-file` refuses combination with
  `--title` or `--scope`, and refuses a missing, unreadable or invalid
  file, writing nothing.
- `agentmarshal amend` pins the `contract_sha256` of the task's
  `contract.md` as it stands at that moment — in a sidecar, the journal
  repository's copy — and refuses a contract that does not parse;
  `migrate` pins the hash of each contract it writes.
- `agentmarshal status <task>` prints one line when the contract's current
  hash differs from the hash in the task's latest `opened` or `amendment`
  record that carries one — naming both short hashes and that the edit
  should be recorded with `amend` — and nothing when they match or no
  record carries a hash; it never fails because of the drift.
- The quickstart opens its task from a contract written first and says
  what happens when a contract is edited after `open`.

## Capabilities

- modified: `contract-governance`

## Impact

Every `opened` record a writer emits is now schema 7 — the coordinated
upgrade of ADR-0022: a reader that does not know schema 7 refuses it, so
the same upgrade-every-reader discipline as every earlier schema applies.
Records written before carry no `contract` and keep validating under
their own schemas; nothing is recomputed. The gate's checks are
untouched — checking the pin against the contract is a later task.
