+++
schema = 1
id = "CR-124"
title = "Intake: Adopter D's proposals 032-036 (time axis, contract review withdrawn, named roles, transaction sweep, unfinished candidate), and the batch's carried corrections"
scope = ["docs/proposals/032-the-journal-has-no-time-axis.md", "docs/proposals/033-contract-review-before-implementation-does-not-pay-off.md", "docs/proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md", "docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md", "docs/proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md", "docs/proposals/027-advisory-findings-have-no-lifecycle.md", "docs/proposals/028-check-outcomes-are-not-evidence.md", "docs/proposals/029-outbox-has-no-scaffold-and-its-name-is-taken.md", "docs/proposals/030-review-verdicts-do-not-say-what-was-executed.md", "docs/proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md", "docs/proposals/README.md", "docs/README.md"]
acceptance = [
  "each of 032-036 digests one of the reporter's files 017-021 in English under the pseudonym Adopter D with the profile and header form 027-031 use, states the release the reporter observed it on, names the source by the sha256 the frame gives, and quotes the file's measurements verbatim with no identifier from the reporter's journal, repository or code",
  "each digest gives every part of its file the disposition the coordinator's dispositions document states, with its reasoning, in the disposition vocabulary the proposals index defines; a part accepted but not built names no release; a declined or withdrawn part says who declined or withdrew it and why",
  "every digest of the 2026-10-01 batch published so far (027-036) ends with a Where section in the form 024-026 use, consistent with its index row; 027 says who declined the rename; 031 names 033 where it refers to the reporter's withdrawal, now that 033 is published",
  "the proposals index has rows for 032-036 with disposition and where, the batch introduction's account of the batch matches the fourteen files without naming unpublished numbers, and the documentation map has a line for each new digest",
  "no statement names a document, release or proposal number that is not published when this task lands, and the full CI sequence passes",
]
+++

# CR-124: intake of Adopter D's proposals 032-036

## Context

The second of the four intake tasks for Adopter D's 2026-10-01 batch: files
017-021, about a journal with no time axis, a contract review before
implementation that the reporter measured and withdrew, a contract that does
not name its implementer and reviewer, journal transactions that carry other
tasks' records, and a review that accepts a candidate whose implementer did not
finish.

The first intake task (CR-123) landed with review advisories carried here
because this task edits the same files: four of its five digests lack the
Where section the others have, 027 does not say who declined the rename, and
the batch introduction lists thirteen themes for fourteen files.

## Objective

Five more of the batch's findings are published with a disposition each, and
the batch's digests so far share one form.

## Acceptance Criteria

As in the header.

## Non-Goals

- Files 022-025 of the batch (the last intake task).
- Any change in behaviour or in documentation other than the proposals, the
  index and the map, including the accepted items themselves.
- Deciding where the contract's implementer and reviewer fields go: 034 states
  the disposition as written; the boundary decision is separate work.
