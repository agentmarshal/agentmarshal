+++
schema = 1
id = "CR-123"
title = "Intake: Adopter D's proposals 027-031 (advisory lifecycle, check outcomes, outbox scaffold, what a verdict executed, who governs the contract)"
scope = [
  "docs/proposals/027-advisory-findings-have-no-lifecycle.md",
  "docs/proposals/028-check-outcomes-are-not-evidence.md",
  "docs/proposals/029-outbox-has-no-scaffold-and-its-name-is-taken.md",
  "docs/proposals/030-review-verdicts-do-not-say-what-was-executed.md",
  "docs/proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md",
  "docs/proposals/README.md",
  "docs/README.md",
]
acceptance = [
  "each of 027-031 digests one of the reporter's files 012-016 in English under the pseudonym Adopter D with the profile the earlier Adopter D digests' headers use, states the release the reporter observed it on, names the source by the sha256 the frame gives, and quotes the file's measurements verbatim",
  "each digest gives every part of its file the disposition the coordinator's dispositions document states, with its reasoning; a part accepted but not built says so without naming a release; a part declined or withdrawn says by whom and why",
  "no digest names a document, release or proposal number that is not published when this task lands, and none contains an identifier from the reporter's journal or repository: no task ids, record ids, file names, paths, commit hashes, package or client names",
  "the proposals index has a section for the 2026-10-01 batch, newest first, whose introduction is true of the whole batch and not only of the five files digested here, with a row for each of 027-031 giving its disposition and where it went; the documentation map has a line for each",
  "the full CI sequence passes",
]
+++

# CR-123: intake of Adopter D's proposals 027-031

## Context

Adopter D sent fourteen files on 2026-10-01 (their 012-025). They are published
as 027-040, in four intake tasks because each edits the proposals index. This is
the first: files 012-016, about advisory findings that have no fate, check
outcomes the journal never hears, an outbox convention with no scaffold, review
verdicts that do not say what the reviewer ran, and a contract written by the
agent that is then measured against it.

The coordinator's dispositions for all fourteen are set; the implementer reads
them where the frame says. The originals are already free of the reporter's
identifiers; nothing may be added that would identify them.

## Objective

Five of the batch's findings are published with a disposition each, and the
index introduces the batch.

## Acceptance Criteria

As in the header.

## Non-Goals

- Files 017-025 of the batch (later intake tasks).
- Any change in behaviour or in documentation other than the proposals, the
  index and the map, including the accepted items themselves.
