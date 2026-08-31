+++
schema = 1
id = "CR-067"
title = "A closed task can be reopened, and the record says why"
scope = ["src/agentmarshal/journal/records.py", "src/agentmarshal/journal/attestation.py", "src/agentmarshal/journal/status.py", "src/agentmarshal/cli.py", "tests/test_reopen.py"]
acceptance = [
  "`agentmarshal reopen --task <id> --reason <text>` appends a `reopened` record carrying the reason",
  "the projection returns the task to `open`, and work may follow as it does after `open`",
  "reopening a task that is already open is refused, naming its state",
  "reopening an unknown task is refused, naming the task",
  "a `reopened` record is the one record type permitted after a terminal record, and any other lifecycle record after a terminal one stays forbidden",
  "a terminal record after a `reopened` record closes the task again, and the trail keeps every cycle",
  "the record type has a registered predicateType and `agentmarshal validate` accepts a journal containing one",
  "`agentmarshal status <id>` shows the reopening in the trail with its reason",
]
+++

# CR-067: A closed task can be reopened, and the record says why

## Context

Adopter proposal 006, second half. A completed task is final: the projection
forbids any lifecycle record after a terminal one, so work that turns out to be
unfinished has nowhere to go. Both reporters raise it, and one describes the
workaround — open a fresh task for the same work — which splits one piece of
work across two contracts and leaves neither telling the whole story.

The first half landed as CR-057: a contract defect is repaired with a recorded
amendment rather than by abandoning the task. This is the other exit from the
same dead end, for the case where the contract was fine and the work was not
finished after all.

The append-only rule is not in tension with this. Nothing is rewritten: a
reopening is a new record, the completion that preceded it stays exactly where
it is, and the trail reads as the history it was — closed, reopened for this
reason, closed again.

## Objective

Let a closed task be reopened by appending a record that says why, and let the
projection follow.

## Acceptance Criteria

- `agentmarshal reopen --task <id> --reason <text>` appends a `reopened` record
  carrying a non-empty reason.
- The projection returns the task to `open`.
- Reopening an already-open task is refused, and the message names its state.
- Reopening an unknown task is refused, and the message names the task.
- `reopened` is the **one** lifecycle record type permitted after a terminal
  record. Every other lifecycle record after a terminal one stays forbidden,
  and `session` keeps the exemption it already has.
- A terminal record after a reopening closes the task again, and the trail
  retains every cycle rather than collapsing them.
- The record type has a registered `predicateType`, and `agentmarshal validate`
  accepts a journal containing one.
- `agentmarshal status <id>` shows the reopening in the trail with its reason.

## Threat model and boundaries

No adversary is introduced. This command appends a record to the operator's own
journal, and reads nothing a contributor supplies.

What deserves care is the **projection**, because every other guarantee is
computed from it. Two properties must survive:

- a task's state must still be derived only from its records, never stored, so
  that a reopened task cannot claim a state its trail does not support;
- the append-only rule must hold unchanged — a reopening adds a record and
  rewrites nothing, and the completion it follows remains in the trail.

Note what reopening does **not** unlock. The gate reads task state from the base
side, so a reopening only has effect once it is committed there — a candidate
cannot reopen its own task to escape "closed at base" any more than it can widen
its own scope.

Not defects in this task, and not to be guarded against: symlinks or path
traversal on the journal; an operator reopening a task frivolously, which is a
judgement the record makes visible rather than one the tool arbitrates.

## Non-Goals

- **Reopening an abandoned task.** Abandonment states that the work was wrong;
  reviving it is a different claim and needs its own reasoning.
- Any limit on how many times a task may cycle.
- Changing what `complete` or `abandon` do.
- Changing the gate.
