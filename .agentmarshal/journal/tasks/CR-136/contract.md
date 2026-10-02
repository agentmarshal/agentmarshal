+++
schema = 1
id = "CR-136"
title = "ADR-0016: the lifecycle of review findings"
scope = [
  "docs/adr/ADR-0016-the-lifecycle-of-review-findings.md",
]
acceptance = [
  "ADR-0016 renders the decision the operator approved (revision 2 of the draft, with the operator's decisions at its end) faithfully and completely: advisory dispositions at complete (fixed, deferred, rejected with a reason, refused by complete itself before writing, for the review the gate passed on — an approval or an acceptance), a dispositions requirement that adds to ADR-0007 without making advisories blocking; the link between rounds with the prior-findings mode off by default pending a measurement; finding classes from the project's vocabulary with unknown classes recorded as other and why; the changes_required count in status and in the gate's output with a threshold, not blocking; the principle criterion as documentation; what stays deferred and why — no point dropped and none added",
  "the ADR has the form of ADR-0012..0015, builds on ADR-0004, ADR-0007 and ADR-0015, names its additions to ADR-0007 and its revision of the gate-lanes specification (new output lines), and answers proposals 026 (second finding), 027 and 039",
  "every statement about present behaviour matches the file it rests on — what a review record carries, that advisory findings affect no decision today, what an acceptance covers, what status prints per review, that report does not aggregate findings",
  "proposals are referred to as 'proposal NNN' and linked; earlier ADRs are named and linked; the record model is a later decision without a number; nothing names a private document, an adopter, a client, an experiment run by the project, or an unpublished release",
  "the full CI sequence passes",
]
+++

# CR-136: ADR-0016 in English

## Context

The operator approved the decision on the lifecycle of review findings in
Russian on 2026-10-03, after a cross-check against the published decisions:
advisory findings get a recorded disposition at completion, review rounds
are linked, findings carry a class, and the number of changes_required
verdicts becomes visible. It answers proposals 026 (second finding), 027 and
039.

## Objective

ADR-0016 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing anything the ADR decides.
- The documentation map line (added with the next ADRs together).
