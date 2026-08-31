+++
schema = 1
id = "CR-071"
title = "capture.py states the threat model it was reviewed against"
scope = ["src/agentmarshal/journal/capture.py"]
acceptance = [
  "the module docstring states which boundary the leak scan defends and which it does not",
  "it states that the scan is best-effort by design and can never be a permission to publish",
  "it states, for the policy parser, that project configuration is operator input and not contributor input",
  "nothing about the module's behaviour changes: the same functions, signatures and results",
]
+++

# CR-071: capture.py states the threat model it was reviewed against

## Context

`capture.py` is this project's most-reviewed module: **thirteen review rounds
across CR-029 and CR-041**, more than any other file. The audit that counted
them recorded it as a candidate for a retrospective contract — a threat model
written after the fact, for a module whose original contract never carried one.

Why it attracted that much review is worth stating rather than guessing at. The
module reads two things a security-minded reviewer treats as dangerous by
reflex: **project configuration**, and **arbitrary diff text**. Neither is
contributor-supplied, and the module writes nothing at all — but nothing in the
file says so, so each reviewer rediscovers the question and argues it out again.

Since CR-056 this project has evidence that stating a boundary in a place the
reviewer reads is what stops the argument. The module docstring is that place
for code, as the contract is for a task.

## Objective

Write down the boundary this module actually sits on, so it does not have to be
re-derived.

## Acceptance Criteria

- The docstring states which boundary the leak scan defends — additions in a
  candidate, before they are stored or published — and which it does not.
- It states that the scan is **best-effort by design** (ADR-0005): a pattern
  list cannot enumerate every secret, and a clean scan is never authorization
  to publish. Callers stay private-by-default regardless of the result.
- It states, for the policy parser, that `project.json` is **operator input**,
  read from a trusted tree, and not something a contributor supplies — and that
  the gate reads it from the base side for exactly that reason.
- **No behaviour changes.** The same functions, the same signatures, the same
  results. This task adds prose to a file and nothing else.

## Threat model and boundaries

Recursive, and worth being explicit about: this task edits comments in a module
that performs no I/O. Nothing here can be attacked.

The risk it addresses is one of process rather than security — a file whose
boundary is unstated attracts unbounded review, and this project has an incident
recording where that leads
(`docs/incidents/2026-08-31-scope-warning-scope-creep.md`).

Not a defect in this task: the leak scan's incompleteness. That is the
documented design (ADR-0005), and the point of writing it down is that it stops
being rediscovered as a finding.

## Non-Goals

- **Changing the scan, its patterns, or the policy model.** If a pattern is
  wrong that is a separate task with its own evidence.
- Making the scan blocking, or changing where it is called.
- Adding tests. No behaviour changes, so there is nothing new to assert.
- Revisiting ADR-0005.
