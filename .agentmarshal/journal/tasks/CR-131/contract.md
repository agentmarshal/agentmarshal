+++
schema = 1
id = "CR-131"
title = "Intake: Adopter D's proposals 041-043 (the next step, unattended liveness, integration before review)"
scope = [
  "docs/proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md",
  "docs/proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md",
  "docs/proposals/043-review-before-integration-makes-every-merge-stale.md",
  "docs/proposals/README.md",
  "docs/README.md",
]
acceptance = [
  "each of 041-043 digests one of the reporter's files 026-028 in English under the pseudonym Adopter D in the form 037-040 use, ending with a Where section, states the release the reporter observed it on, names the source by the sha256 the frame gives, and quotes the file's measurements verbatim with no identifier from the reporter's journal, repository or code",
  "each digest gives every part of its file the disposition the coordinator's dispositions document states, in the index's vocabulary; a need met by something the project supplies rather than by the tool says so; a part not taken says by whom and why; ADR-0012 and ADR-0013 are named and linked where a disposition rests on them, and no unpublished decision is named",
  "every statement about present behaviour matches the file it rests on — for example that the tool has no next-step command, which outcome values are documented, what ADR-0013 says about stages and their candidates, that the gate never merges",
  "the proposals index has a section for the 2026-10-03 batch, newest first, with a true introduction and a row for each of 041-043; the documentation map has a line for each; the line that still calls proposal 009 deferred is corrected",
  "nothing names a document, release or decision that is not published, and the full CI sequence passes",
]
+++

# CR-131: intake of Adopter D's proposals 041-043

## Context

Adopter D sent three files on 2026-10-03 (their 026-028): the next step of a
task is decided outside the tool, so every adopter writes a driver that
misreads why a step failed; the liveness of an unattended loop is watched by
hand, and the reporter offers its step watchdog and loop monitor as a
reference extension; reviewing before integrating makes every merge stale the
next approval. The operator accepted the coordinator's dispositions the same
day. A carried point from CR-130: the documentation map still calls proposal
009 deferred.

## Objective

The batch is published with a disposition for every part.

## Acceptance Criteria

As in the header.

## Non-Goals

- Building anything the dispositions accept.
- The route by which the reporter's code may reach this repository (not yet
  decided).
