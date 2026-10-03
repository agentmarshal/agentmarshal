+++
schema = 1
id = "CR-159"
title = "ADR-0023: next — the next step of a task"
scope = [
  "docs/adr/ADR-0023-next-the-next-step-of-a-task.md",
]
acceptance = [
  "ADR-0023 renders the decision the operator approved (revision 2 of the draft with the operator's decisions at its end) faithfully and completely, no point dropped and none added: the command and its inputs, that it executes and writes nothing (the conflict check uses a temporary object store; in a sidecar the host is only read), the nine actions, the eleven-rule first-match table with its definitions (the head, the latest review of the head, records older than a reopening ignored), what counts as an attempt, the output in text and JSON (escaped in text only), the reference driver in the adopter kit, and what is left open",
  "the two operator decisions are stated as decisions: a time-limit session with its report ready is not refused by proposal 036's unfinished-candidate rule (a refinement of 036's disposition, named as such); the round threshold that stops `next` counts changes_required verdicts since the latest contract amendment, while status keeps counting over the whole task",
  "the ADR names every published text it revises or extends — ADR-0019 decision 5 (the outcome is now read, by `next`, and stays free text), proposal 036's disposition (the refinement above), and ADR-0014 (`next` is a further local reader of the process log; the gate still never reads it) — and every statement about present behaviour matches the file it rests on (how the gate derives the task from the branch and the default base, which gate checks can be decided from records without a pipeline, that `git merge-tree --write-tree` writes objects)",
  "the ADR has the form of ADR-0012..0022 with Context, Decision, Left open, Consequences and Alternatives considered, derived from the decision; proposals are referred to as 'proposal NNN' and linked, earlier ADRs named and linked",
  "nothing names a private document, an adopter, a client or an unpublished release, and the full CI sequence passes",
]
+++

# CR-159: ADR-0023 in English

## Context

Proposal 041 asked for `next`: the decision every adopter's driver
re-implements after each step. The operator decided on 2026-10-03 that the
decision belongs in 0.5.0 and approved the Russian draft, revision 2, after
it was cross-checked against everything published, with two decisions:
a time-limit run with its report ready is reviewable, and `next` counts the
round threshold from the latest contract amendment.

## Objective

ADR-0023 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing `next`, the plan file reader or the driver.
- Editing proposal 036, ADR-0019 or ADR-0014 (a later documentation task
  amends them; this ADR names the revisions).
- The documentation map line.
