+++
schema = 1
id = "CR-057"
title = "Record a contract amendment instead of only committing it"
scope = ["src/agentmarshal/journal/records.py", "src/agentmarshal/journal/attestation.py", "src/agentmarshal/journal/status.py", "src/agentmarshal/cli.py", "tests/test_journal.py", "tests/test_attestation.py"]
acceptance = [
  "`agentmarshal amend --task <id> --reason <text>` writes an `amendment` record into the task's records directory",
  "the record carries the reason and is refused when the reason is empty or absent",
  "`agentmarshal validate` accepts a journal containing an amendment record",
  "an amendment record has a registered predicateType, so attestation does not fail closed on it",
  "an amendment does not change the task's projected state: an open task stays open, and amending a task with a terminal record is refused",
  "`agentmarshal status <id>` lists the amendment in the record trail",
  "amending an unknown task is refused with a message naming the task",
]
+++

# CR-057: Record a contract amendment instead of only committing it

## Context

Adopter proposal 006. Twice on one adopter's project the work was sound and
review kept refusing because the defect was in the **contract**, not the code.
With no way to repair a contract mid-task, the only exit is to abandon the task
and reopen it — one criterion took six refusals, another three, and the reopened
task was accepted **on the first run with the same code**. The journal is then
left recording an abandonment that blames the work for a defect in the
specification. That is an evidence-quality problem, not only an ergonomic one.

We have just done the same thing by hand. CR-056's contract was amended through
a journal-only commit, because the reviewer kept raising a boundary the contract
did not state. It worked, and it left no evidence beyond a commit message: the
journal cannot say that the contract was repaired, when, why, or by whom.

The contract file itself must still be edited — the gate reads scope and
acceptance from `contract.md` on the base side, and that is the mechanism that
keeps a candidate from widening its own scope. What is missing is the **record**
that makes the edit evidence rather than a silent rewrite.

## Objective

Make a contract amendment a recorded, appendable event: a new `amendment` record
type carrying the reason, written by a new `amend` command, accepted by
validation and attestation, and visible in a task's record trail.

## Acceptance Criteria

- `agentmarshal amend --task <id> --reason <text>` writes an `amendment` record
  into `.agentmarshal/journal/tasks/<id>/records/` and prints its path.
- The record carries the reason. An empty or missing reason is refused.
- `agentmarshal validate` accepts a journal containing an amendment record.
- The record type has a registered `predicateType`, so attestation does not fail
  closed when it appears.
- The projection is unchanged by an amendment: a task that was open stays open.
  Amending a task that already carries a terminal record is refused.
- `agentmarshal status <id>` lists the amendment in the trail.
- Amending a task that does not exist is refused with a message naming it.

## Threat model and boundaries

**Where an adversary exists in this system, and where one does not.** The gate
reads a task's contract and prior state from the **base** side, never from the
candidate, precisely because a candidate is content a contributor supplies and
may be hostile. That is the boundary the project's existing protections — the
base-side read, the append-only check, the record-path collision check — are
built to defend.

**This command sits on the other side of that boundary.** `amend` runs in the
operator's own checkout, on their own journal, writing a file they could have
written with an editor. It reads no candidate content, parses nothing supplied
by a contributor, and grants no authority: an amendment record does not change
what the gate enforces. Scope and acceptance continue to come from `contract.md`
as committed on the base, so a task still cannot widen its own scope, and an
amendment reaches the base only through the journal-only lane the operator
already controls.

Therefore the following are **not** defects in this task and must not be
guarded against here:

- **Symlinks, path traversal or TOCTOU on the journal path.** The journal lives
  in the operator's checkout; a symlink there was placed by the operator, and
  following it is doing what they asked. The project has recorded an incident
  about exactly this reflex —
  `docs/incidents/2026-08-31-scope-warning-scope-creep.md`.
- **An amendment being used to widen scope.** It cannot: the gate does not read
  amendment records when deciding scope.
- **Concurrent writers racing on the records directory.** Journal integrity
  under concurrent agents is a known, separately recorded question and is out of
  this task's reach.

What *is* worth defending here is narrower and belongs to the record model
itself: a record type that validation or attestation does not know about would
fail closed later, and a record that silently altered a task's projected state
would make the status lie. Both are covered by the acceptance criteria.

## Non-Goals

- **Repairing a completed task.** Proposal 006 also asks for a way to reopen a
  completed task; that changes the lifecycle and needs its own decision.
- **Enforcing that an amendment accompanies a `contract.md` edit.** Nothing here
  detects an unrecorded edit. This makes the honest case expressible, in the
  same sense as `recorded_by` (ADR-0006) — it is not a control.
- **A schema field for the amendment's content or a diff of the contract.** The
  reason is prose; what changed is visible in git.
- **Changing what the gate enforces.**
