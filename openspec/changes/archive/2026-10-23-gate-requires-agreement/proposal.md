## Why

ADR-0018 decision 2 left the switch to the project: the gate does not
require the agreement record by default; a project whose rules demand
agreement can make it required. ADR-0022 section 6 named the switch —
`contract.require_agreement` (default false), readable since CR-151 —
and CR-177 and CR-180 landed the `agreement` record and the `agree`
command that writes it. Nothing reads the setting yet: a project that
turns it on gets no enforcement at the merge boundary.

## What Changes

- On the implementation lane the gate reads
  `contract.require_agreement` from the journal repository's project
  file — the same working-tree read the `changes_required` threshold
  makes. When the setting is true, one PASS or FAIL line judges whether
  the task's records hold an `agreement` whose `contract` equals the
  `contract_sha256` of the contract the gate judges against — the
  merge-base tree's in the embedded placement, the sidecar working
  tree's in a sidecar — and names the judged contract's short hash. A
  FAIL says agreement is recorded with `agentmarshal agree`; when the
  task carries agreements but none carries the hash, the line says an
  agreement exists for another hash and names the latest `agreement`
  record's short hash beside the judged one.
- Any `agreement` record carrying the hash satisfies the check, whoever
  recorded it — there are no roles (ADR-0018 decision 2). The check
  binds the contract, not a review: it runs however the run was asked,
  and the deterministic lane prints no agreement line, judging no
  contract.
- When the setting is false or absent — the default — the transcript is
  today's, byte for byte, as the pinned default fixtures demonstrate. A
  setting the gate cannot read is reported on a WARN line the way an
  unreadable `changes_required` threshold is: neither a refusal nor a
  silent skip.
- The requirement text that said the gate's `require_agreement` check
  comes with its own task is updated: this is that task.

## Capabilities

- modified: `contract-governance`

## Impact

`src/agentmarshal/journal/gate.py` gains the check beside the scope
line; the record model and the settings module already carry everything
it needs. Roles over who may agree and membership in the contract's
`reviewers` list remain non-goals — the protection is exactly what
ADR-0018 decision 2 promises, no more (docs/threat-model.md).
