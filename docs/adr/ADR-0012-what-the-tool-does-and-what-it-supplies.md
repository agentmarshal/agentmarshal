# ADR-0012: What the tool does itself and what it supplies as a compatible replacement

Status: Accepted
Date: 2026-10-02

Builds on [ADR-0001](ADR-0001-governance-plane.md) (a governance plane, not an
execution plane) and [ADR-0010](ADR-0010-process-extensions.md) (process
extensions with a declared footprint).

This ADR records a decision. The contract fields, templates, gate lines and
commands it describes are **not implemented by this document**; they follow in
their own tasks. The present tense below is how a decision is written, not a
claim about shipped behaviour.

## Context

[ADR-0001](ADR-0001-governance-plane.md) makes the tool a governance plane:
sandboxing, tool permissions, isolation, live orchestration and session
management belong to the execution environment. When
[proposal 019](../proposals/019-journal-transactions-assume-direct-commits.md) —
the finding that journal transactions assume direct commits to the base
branch — was accepted, providers, branch-protection schemes and merge policies
were assigned to the harness layer: the pattern ships as documentation and an
example script rather than a command, because a command would have to know
about them.

Four adopter findings with measurements press on this line:

- [proposal 034](../proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md) —
  the contract does not name its implementer and reviewer: six mid-task
  implementer switches over 69 tasks, and the choice expressed only in the
  launch wrappers' environment variables;
- [proposal 035](../proposals/035-journal-transactions-sweep-records-of-other-tasks.md) —
  28% of journal transactions carried the records of other tasks;
- [proposal 038](../proposals/038-an-adopter-setup-cannot-be-carried-to-the-next-repository.md) —
  the adopter's layer (about 2,700 lines of wrappers and 3,800 lines of tests)
  cannot be carried to the next repository without a separate instruction;
- [proposal 040](../proposals/040-in-flight-steps-are-invisible-and-journal-writes-contend-on-one-checkout.md) —
  six stalls of 30–45 minutes in two days, every one detected by a person
  or the coordinating agent polling — none by the tool.

A fifth need comes from the adopter who left for a spec tool: a living
description of the system, fed into the agent's context.

Answering "that is the harness layer" leaves an adopter with a need and no
solution, and an adopter cannot put several process tools into one repository:
they contend over branches, worktrees, pull requests and hooks. The tools that
closed these needs did so as execution environments with their own base; for
an adopter whose loop AgentMarshal runs, they are not a replacement.

## Decision

### 1. The rule for where a measured need is met

A measured adopter need is met **by the tool** if it is a durable fact about
the task, checkable against the repository's records with no live process;
otherwise it is met by a **supplied compatible replacement**. The ADR-0001
boundary holds for the core: it does not execute, does not schedule and holds
no live state. An extension may drive the process; a separate decision on how
extensions run governs that.

### 2. No refusal without a replacement

A disposition that places a need outside the tool names a replacement, or
says plainly that none exists yet and why.

### 3. Declared extension, supplied extension

A declared extension is what ADR-0010 defines: recorded, unpinned, unchecked.
A supplied extension is one the project recommends, and it carries
obligations:

- a compatibility test in the project's CI — the extension writes only to its
  own footprint and never to the journal; it does not bypass the gate with
  hooks or checks; it does not take over branches, worktrees or pull
  requests; a full task cycle passes under it; the gate refuses where it
  must; removal is clean; `validate` and `leak-scan` show no false positives;
- a pinned version with a package-integrity value — the pin lives in the
  extension's manifest, a form the separate decision on how extensions run
  extends beyond ADR-0010's `version` field, which is informational and
  pins nothing;
- the pin re-reviewed with each release;
- a `doctor` warning when the installed version is not the one checked —
  `doctor` joins `brief` and the gate as a reader of manifests;
- removal from the supplied set is announced.

The guarantee is compatibility with the task cycle at the pinned version —
**not** the quality or the security of the tool. Supplying is not bundling: a
supplied extension is installed only at the adopter's choice, and ADR-0010's
refusal of a bundle stands.

### 4. The adopter kit

The project supplies templates for the harness-layer parts — a
journal-transaction helper, reviewer selection, implementer launch, a
watcher for waits at the provider. The adopter copies a template and owns
the copy. Templates ship with a release and are checked by the project's
tests. `init` creates the standard adopter-layer layout under
`.agentmarshal/`, as it already creates the outbox; the layer's manifest
lists its files, and `doctor` reports discrepancies.

### 5. Core and optional

The core is what the gate needs to decide: the contract, the records and
their schema, `validate`, `gate`, the trusted path that writes a review.
Everything else — accounting and `report`, the outbox, the reviewer launcher,
the v1 migration, `prune`, the process templates — is optional. Gate code
imports no optional module; a test checks that.

### 6. Application to the findings

- [proposal 034](../proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md) —
  **the tool**: optional contract fields (the allowed implementers and
  reviewers, and the independence rule), a gate check on them, and `status`
  showing the declared assignment next to the actual one. The gate already
  checks one thing about independence: the reviewer e-mail declared in the
  review record is compared with the author and committer addresses of the
  candidate's commits — the `merge-base..candidate` range — which refuses a
  reviewer who wrote the candidate, but cannot tell the intended reviewer
  from a misconfigured launch or check independence by vendor or model.
  The fields give that check a declared assignment to check against: the
  review that makes a candidate mergeable must come from a permitted
  reviewer and satisfy the independence rule against the implementers
  whose commits the candidate carries. The tool neither picks nor launches
  a model. The guarantee is "declared and cross-checked", not "proven":
  the record of who implemented is written by an agent.
- [proposal 035](../proposals/035-journal-transactions-sweep-records-of-other-tasks.md) —
  **template and gate**: the transaction helper stages only its own task's
  directory, and the gate warns when a journal transaction carries another
  task's `opened` or amendment records.
- [proposal 038](../proposals/038-an-adopter-setup-cannot-be-carried-to-the-next-repository.md) —
  **the kit** of Decision 4. Export and a profile update with three-way merge
  are deferred until the layout settles.
- [proposal 040](../proposals/040-in-flight-steps-are-invisible-and-journal-writes-contend-on-one-checkout.md) —
  **the process log** that a separate decision on where local state lives
  defines: it carries a "step started, deadline" entry, and `status` and
  `doctor` show the overdue ones. Its second half — a journal write that
  does not need the shared checkout — is accepted into the
  journal-transactions work of
  [proposal 019](../proposals/019-journal-transactions-assume-direct-commits.md)
  and
  [proposal 035](../proposals/035-journal-transactions-sweep-records-of-other-tasks.md).
  And **a watcher template** for waits at the provider — an unmergeable
  pull request, a quota refusal — together with a fail-fast rule. There are
  no heartbeats and no mutual-exclusion locks.
- The living system description — **a supplied OpenSpec extension**, the
  first under Decision 3: a manifest, a method for wiring it in, the
  pitfalls, an example contract.

### 7. What the core does not do

The core does not run someone else's code in a way that could permit a merge
— that belongs to the separate decision on how extensions run. It does not
launch or schedule agents. It does not accept another execution
environment's records in place of its own — revisited when an adopter asks.

## Left open

When an optional component moves into a package of its own. The signs — all
three required:

- the "the gate imports no optional module" boundary of Decision 5 has held
  for at least one release;
- at least one of: the component needs to ship more or less often than the
  core (for example, it follows a third-party tool's releases); an adopter
  directly asks not to install it together with the core;
- the core interface the component uses is declared stable.

## Consequences

- An adopter gets a checked replacement instead of "that is not ours".
- The project takes on a maintenance commitment. ADR-0010 warned that a
  commitment of this kind, for a list of neighbouring tools, has already
  failed to be kept — so the supplied set is short (currently one) and its
  re-review rests on a test.
- Existing adopters lose nothing: the new parts are optional, the cycle does
  not change, and new records arrive through a single schema transition.

## Alternatives considered

**A strict boundary that refuses
[proposal 038](../proposals/038-an-adopter-setup-cannot-be-carried-to-the-next-repository.md)
and
[proposal 040](../proposals/040-in-flight-steps-are-invisible-and-journal-writes-contend-on-one-checkout.md).**
Leaves a measured need with no solution at all.

**A plugin SDK and registry.** Rejected in ADR-0010; rejected again for the
same reasons.

**An own runner in the core.** Competes with the execution environments with
a single maintainer behind it.

**Accepting other environments' records in place of our own.** No adopter has
asked, and it would blur the cycle the records describe.

**Bundling the spec tool.** Rejected in ADR-0010. Supplying it by choice,
pinned, is a different decision.
