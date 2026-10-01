+++
schema = 1
id = "CR-118"
title = "Intake: 0.4.0 validate refused records an earlier release wrote (proposal 025)"
scope = [
  "docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md",
  "docs/proposals/README.md",
  "docs/README.md",
]
acceptance = [
  "docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md digests the reporter's finding in English under the pseudonym Adopter A with the profile the index already uses for them, names the source by its sha256 4b86c6ddfac756a2270d29c2b8041c680d82606ecb0806e41023307029c84ce6, and quotes every measurement in its evidence table verbatim, without naming the reporter's own task identifiers",
  "the digest states the mechanism as the code has it: the check existed before 0.4.0 for acceptance finding ids, 0.4.0 extended it to review findings and advisory findings, and record validation runs when a journal is read",
  "the digest gives a disposition with reasoning for each of the four proposals: narrowing the rule accepted and done in 0.4.1 (CR-114); not tightening a rule over records an earlier release wrote accepted as a principle and not yet decided as a mechanism; validating a release against an adopter's journal before publishing accepted and done for 0.4.1 (CR-115); an allowlist of known-bad records declined, because it declares a record acceptable around the gate",
  "the proposals index lists 025 in a batch table dated 2026-09-24 with its disposition and where it went, and the documentation map in docs/README.md has a line for it",
  "no statement names a release, task or document that is not published, and the full CI sequence passes",
]
+++

# CR-118: intake of proposal 025

## Context

Adopter A, whose earlier findings became proposals 001, 002, 005, 006, 007 and
010, ran 0.4.0's `validate` over their journal before upgrading and it refused
review records an earlier release had written. The defect was reproduced the
same day, fixed by CR-114 and published as 0.4.1 on 2026-09-24. The finding
itself, with its four proposals, has not been published yet.

The original is staged privately; the implementer reads it there. It is in
Russian and names the reporter's own task identifiers, which the digest leaves
out.

## Objective

The finding is published with a disposition for each of its proposals, and the
reporter can match it to their file by hash.

## Acceptance Criteria

As in the header.

## Non-Goals

- The reporter's other new finding (their file 008): it is taken in with the
  next batch of proposals.
- Deciding how a reader knows which rules a record was written under.
- Any change in behaviour.
