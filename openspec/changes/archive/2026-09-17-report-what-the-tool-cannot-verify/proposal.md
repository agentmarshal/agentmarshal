## Why

Two adopter reports describe the same shape: the tool leaves the operator to
configure what its guarantees depend on, and says nothing when it is missing.

[Proposal 014](../../../docs/proposals/014-init-leaves-trust-preconditions-unchecked.md)
counted nine manual steps after `init` before a first governed task could
complete. Two of them corrupt the evidence silently when skipped — squash or
rebase merges left enabled on the provider, which rewrites the reviewed SHA, and
the actor variable unset in an agent's harness, which records an agent's work
under a human's identity. `doctor` reported all four of its checks green with
both unset.

[Proposal 017](../../../docs/proposals/017-provider-template-gate-check-structurally-red.md)
found that the shipped provider template runs the gate on a pull-request head
that cannot yet carry its own review record, so the check is red on every
implementation pull request. The documentation calls it advisory; the provider
has no advisory state. This project works around it in its own merge tooling
and never carried the fix back into the template.

## What Changes

- `init` prints the preconditions it cannot verify, as a checklist, once.
- `doctor` checks what it can: the actor variable, a reviewer command whose
  placeholders resolve, and a CI definition that invokes `validate`. Each
  failure says what breaks if it stays missing.
- The self-hosting document states the branch-naming requirement the template
  imposes: the task identifier is read from the head reference.

## Impact

- `src/agentmarshal/doctor.py` (or its equivalent) and `src/agentmarshal/cli.py`.
- `docs/self-hosting-workflow.md`, `docs/harness-setup.md`.
- No gate change: `doctor` advises and `init` prints.
