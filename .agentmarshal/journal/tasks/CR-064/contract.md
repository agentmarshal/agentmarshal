+++
schema = 1
id = "CR-064"
title = "ADR-0007: the operator accepts work over findings"
scope = ["docs/adr/ADR-0007-operator-acceptance.md"]
acceptance = [
  "the ADR states what an acceptance overrides and, explicitly, what it does not",
  "it states that an acceptance requires a non-approving review of the same commit to exist, so it cannot be used to skip review",
  "it decides whether an author may accept their own work, and states the reasoning either way",
  "it states where an accepted-over-findings task must be distinguishable from an approved one",
  "it states the claim boundary: what an acceptance record does and does not establish",
]
+++

# CR-064: ADR-0007 — the operator accepts work over findings

## Context

Adopter proposal 007. The gate merges only on an `approved` verdict, and there
is no other path — so in effect the acceptance decision belongs to the reviewer,
while the operator is accountable for the product and the reviewer is a tool.

While findings are real this is correct. The problem is non-convergence: the
remarks change from round to round, the verdict stays `changes_required`, and
the work is fit for purpose. The reporter's measurements: one task at **13
review runs, not closed**; another at 6, not closed; three abandoned and
reopened to escape. We have measured the same root cause independently — five
verdicts on one identical commit in this repository, one pass and four refusals
with different findings each time — and hit the dead end ourselves on CR-056.

The disposition we published constrains the design: an acceptance must be a
**first-class record** naming who accepted, over which findings, and why —
never a flag that makes a merge look reviewed.

## Objective

Decide the design before building it: what an acceptance is, what it overrides,
what it must never override, and what it does and does not establish.

## Acceptance Criteria

- States precisely what an acceptance overrides, and enumerates what it does
  **not** — the gate's other checks are not in its reach.
- States that an acceptance requires an existing non-approving review of the
  same commit, so the path cannot be used to merge unreviewed work.
- Decides whether someone may accept work they authored, with the reasoning.
- States where an accepted-over-findings task must be distinguishable from an
  approved one, and that it must never read as approved anywhere.
- States the claim boundary in the manner of ADR-0006: what the record
  establishes, and what it does not.

## Threat model and boundaries

This task writes one document. It changes no behaviour, so nothing in the
running system can be attacked through it.

Its risk is of a different kind and worth naming: **a decision recorded loosely
here becomes a hole built faithfully later.** The care belongs in the wording,
not in guarding a file.

## Non-Goals

- **Implementing anything.** No record type, no command, no gate change; those
  follow in their own task.
- Deciding the record's field names or the command's spelling. The ADR settles
  the shape of the decision, not its syntax.
- Revisiting reviewer non-determinism itself. That it exists is measured; this
  ADR is about who owns the decision when it does.
