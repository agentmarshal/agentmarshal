+++
schema = 1
id = "CR-130"
title = "Proposal dispositions catch up with ADR-0013 and with every adopter finding moving into the next release"
scope = [
  "docs/proposals/009-lifecycle-extension-points.md",
  "docs/proposals/018-session-activity-vocabulary-and-cost.md",
  "docs/proposals/020-leak-scan-names-no-file-and-self-matches.md",
  "docs/proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md",
  "docs/proposals/033-contract-review-before-implementation-does-not-pay-off.md",
  "docs/proposals/039-review-findings-do-not-feed-back-into-the-next-round.md",
  "docs/proposals/README.md",
]
acceptance = [
  "proposal 009 and part 7 of proposal 039 are answered by ADR-0013: each says what ADR-0013 decided for the ask — extension stages, an extension as a separate step before the gate that can only pause it, the rule for future stages — what of the ask it covers and what it does not, and links ADR-0013; the earlier reasoning stays visible as the history of the disposition, dated, not erased",
  "proposal 018's cost field and the third part of proposal 020 (an acknowledged-and-proceed path for a leak-scan hit) move from deferred to accepted, not shipped yet, stating that the project took every adopter finding into the next release; neither names a release or an unpublished decision",
  "proposals 031 and 033 describe the reporter's withdrawal of 031's third suggestion the same way, in the index's disposition vocabulary",
  "each changed digest says the same in its header, its Disposition section, its Where section where it has one, and its row in the proposals index; the index's batch introductions stay true",
  "nothing names a document, release or decision that is not published, and the full CI sequence passes",
]
+++

# CR-130: dispositions catch up

## Context

Three things moved after these digests were published. ADR-0013 (CR-128)
gives extensions stages — a separate step before the gate that can pause it,
and one after completion — which answers proposal 009 (deferred: "a hook
interface is easy to add and hard to remove") and part 7 of proposal 039
(declined with ADR-0010's reasoning). The operator took every adopter finding
into the next release, which moves proposal 018's cost field and proposal
020's third part from deferred to accepted. And two review rounds of CR-125
found 031 and 033 describing the reporter's withdrawal differently; 031 was
out of that task's scope.

## Objective

The published dispositions say what is now decided.

## Acceptance Criteria

As in the header.

## Non-Goals

- Proposals 003 and 004 (deferred at the first intake; not part of this
  decision).
- Any change in behaviour.
