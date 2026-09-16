+++
schema = 2
id = "CR-094"
title = "Adopter batch D: ten proposals from a from-scratch install, digested with dispositions"
scope = [
  "docs/proposals/",
  "CONTRIBUTING.md",
]
acceptance = [
  "each of the ten source findings has a digest under docs/proposals/ that names the version it was observed on, quotes its measurements verbatim, says what the reporter proposed, and carries a disposition with the reasoning for it",
  "every digest carries a source line pinning the sha256 of the original file, so a reporter can match a published digest to their own finding without either side naming the repository it came from",
  "no digest and no index row contains a repository name, host name, filesystem path, task identifier or code excerpt belonging to the reporter, and the reporter's profile in the index names a setup rather than a product, a client or a domain",
  "the index lists the batch with a column that names where each accepted proposal goes, and a finding already fixed on the default branch says so in its disposition and names the release that will carry the fix",
  "CONTRIBUTING states how a reporter tracks a proposal after sending it: the source hash, the disposition, and the column that names where it went",
]
+++

# CR-094: adopter batch D

## Context

A new adopter installed the published release on a fresh repository and ran the
governed loop on it. Ten findings came back through the outbox convention the
project ships. Nine of the ten are still true on the default branch; one was
fixed after the release and is waiting for it. The batch is the first from a
from-scratch install, which is why it is dense in onboarding defects that no
amount of reading our own code would have surfaced.

This task lands the batch as digests. It does not act on the findings: each of
those is its own task, and the plan says which.

## Objective

Ten sanitized digests with dispositions, an index that says where each accepted
proposal goes, and a stated way for the reporter to track what happened to it.

## Acceptance Criteria

As in the header.

## Threat model and boundaries

The reporter's repository is private and this one is public and cannot
un-publish. A digest must not let a reader reconstruct what it came from: no
names, no paths, no task numbers, no quoted code. The measurements are the part
worth publishing, and they are quoted as written.

The source hash is the correlation token. It is one-way: it identifies the
original to whoever already holds it and says nothing to anyone else. It must
pin the file as sent, so a later edit on the reporter's side does not silently
retarget a published disposition.

## Non-Goals

- Acting on any finding. The fixes are separate tasks, named in the plan.
- The `upstream status` command that would automate tracking: it is a candidate
  for the release after this one, recorded, not built here.
- Changing the outbox layout or the shipped outbox README.
- Re-numbering or re-dispositioning the earlier batch.
