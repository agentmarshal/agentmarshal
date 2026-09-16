+++
schema = 2
id = "CR-095"
title = "A contract shows that it changed, and a review says which contract it judged (ADR-0011)"
scope = [
  "docs/adr/ADR-0011-contract-amendment-visibility.md",
  "docs/adr/README.md",
]
acceptance = [
  "the decision record states the defect as it is: the amendment records exist and are intact, the gate reads the contract from the merge-base and the reviewer from the reviewed commit, a review is bound to the SHA it judged, and what is missing is that the judging party is not shown the document's history",
  "for every entity the decision introduces, it says from which side it is read, when it is read, what happens when it is absent, and what happens when it changes; the sidecar placement is answered separately wherever its answer differs",
  "the decision says what it does not decide, and each alternative it rejects carries the reason it was rejected rather than a preference",
  "no absolute claim in the record is broader than the mechanism it describes; a reader who greps it for every, always, never or cannot finds each one defensible",
  "the record names the adopter proposal it answers and this project's own amendment counts, and the ADR index lists it",
]
decisions = ["ADR-0004", "ADR-0006", "ADR-0008"]
+++

# CR-095: ADR-0011, contract amendment visibility

## Context

An adopter's proposal (022 in the current batch) showed that the reviewer is
handed the contract and never the amendment records, so a criterion added after
a round of review is indistinguishable from one written at open time. Their
measurements are in the proposal; this project's journal carries 21 amendment
records across 18 of its 91 completed tasks, and at least one contract was
amended between the second and third round of its own task.

The decision comes before the mechanism, as ADR-0009 and ADR-0010 did. This
task lands the decision only.

## Objective

A decision record that states the defect precisely, chooses where the
amendment history is made visible, says who checks it, and answers the sidecar
placement separately because the reasoning there is not the same.

## Acceptance Criteria

As in the header.

## Threat model and boundaries

The party that amends a contract is usually the party that orchestrates the
implementer and requests the review. The protection this record adds is
visibility to the independent reader, not a new refusal: the embedded journal
already binds a review to its SHA, and a candidate cannot be judged against a
contract it has not incorporated. In a sidecar nothing binds the contract to a
commit, and the record must say so rather than let the reader assume the
embedded reasoning carries over.

## Non-Goals

- Implementing any of it. `amend`, `validate`, the gate and the review record
  change in their own task, after this decision lands.
- Requiring a review of an amendment, or forbidding amendment after a review.
- Anything about the findings lane.
- Re-examining closed tasks whose amendments predate this decision.
