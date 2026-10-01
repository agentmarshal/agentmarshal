+++
schema = 1
id = "CR-125"
title = "Intake: Adopter D's proposals 037-040, and the batch's statuses after the operator moved every adopter finding into the next release"
scope = [
  "docs/proposals/037-review-crashes-on-a-diff-that-is-not-utf-8.md",
  "docs/proposals/038-an-adopter-setup-cannot-be-carried-to-the-next-repository.md",
  "docs/proposals/039-review-findings-do-not-feed-back-into-the-next-round.md",
  "docs/proposals/040-in-flight-steps-are-invisible-and-journal-writes-contend-on-one-checkout.md",
  "docs/proposals/024-provider-quota-stop-cannot-be-recorded.md",
  "docs/proposals/026-reviewer-facts-round-convergence-and-two-gaps.md",
  "docs/proposals/032-the-journal-has-no-time-axis.md",
  "docs/proposals/033-contract-review-before-implementation-does-not-pay-off.md",
  "docs/proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md",
  "docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md",
  "docs/proposals/README.md",
  "docs/README.md",
]
acceptance = [
  "each of 037-040 digests one of the reporter's files 022-025 in English under the pseudonym Adopter D in the form 032-036 use, ending with a Where section, states the release the reporter observed it on, names the source by the sha256 the frame gives, and quotes the file's measurements verbatim with no identifier from the reporter's journal, repository or code",
  "each digest gives every part of its file the disposition the coordinator's dispositions document states, its top section overriding the rows, in the index's vocabulary; a need met by something the project will supply rather than by the tool says so; a part still deferred or declined says by whom and why; a defect says what upstream reproduced and what it did not",
  "024 and 026 carry the dispositions the override sets — their reset-time field and evidence field accepted, not shipped yet; review --since still deferred, with its reason — the same in header, Disposition, Where and index row",
  "the corrections carried from CR-124 are made: 032 says the gate already computes a journal-only lane and the accepted part is exposing it to the required check; 035's index row lists every accepted part; 033's header agrees with its body; 034's Where names where its deferred decision sits without naming an unpublished document",
  "the proposals index has rows for 037-040 and its batch introduction is final for fourteen files; the documentation map has a line for each new digest; no statement names a document, release or proposal number not published when this task lands; the full CI sequence passes",
]
+++

# CR-125: intake of Adopter D's proposals 037-040

## Context

The last of the four intake tasks for Adopter D's 2026-10-01 batch: files
022-025, about `review` failing on a diff that is not UTF-8, an adopter layer
that cannot be carried to the next repository, review findings that do not feed
back into the next round, and steps in progress the journal cannot see while
journal writes contend on one checkout.

After CR-123 and CR-124 landed, the operator moved every adopter finding into
the next release. Parts of 024 and 026 that their published digests call
deferred are now accepted and not shipped. The operator also decided that a
need the tool does not meet itself is met by something the project supplies
and checks against its own cycle — which is how 038 and 040 are disposed.

CR-124 landed with review advisories carried here because this task edits the
same files.

## Objective

The batch is published in full, and every digest of it, with 024 and 026, says
what is now planned.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any change in behaviour or in documentation other than the proposals, the
  index and the map, including the accepted items themselves.
- Writing the decision on what the tool supplies; the digests state the
  dispositions without naming that decision's document.
