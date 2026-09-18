+++
schema = 1
id = "CR-113"
title = "Intake: a provider quota stop cannot be recorded (proposal 024)"
scope = [
  "docs/proposals/024-provider-quota-stop-cannot-be-recorded.md",
  "docs/proposals/README.md",
  "docs/quickstart.md",
  "README.md",
]
acceptance = [
  "docs/proposals/024-provider-quota-stop-cannot-be-recorded.md digests the adopter's finding in English under the reporter's existing pseudonym and profile, quotes every measurement verbatim, names the source by its sha256, and states a disposition with reasoning for each of the three things proposed",
  "the proposals index lists 024 in a batch table with its disposition and where it went, and says how a reporter can match a file in their outbox to its digest",
  "the quickstart's step on recording cost says that token counts are not what a provider charges, and documents an outcome value for a session the provider refused to continue, without describing any behaviour the tool does not have",
  "README.md no longer says the journal's token measurements are what each task cost",
  "no statement names a release, task or document that is not published; the full CI sequence passes",
]
+++

# CR-113: intake of a provider quota stop finding (proposal 024)

## Context

Adopter D, whose first batch became proposals 014–023, sent an eleventh finding:
a session that ended because the provider refused further work is recorded
like any other failed session, the reset time the provider stated is lost, and
the documentation presents token counts as what a task cost, while the
provider meters something else. Two of the reporter's thirteen implementer
sessions ended that way, and a choice between models rested on a ratio the
journal could not hold.

The same reporter could not tell from this repository which of its first ten
findings had been handled. Each digest names its source by sha256, which is
enough to match them, but nothing says so.

## Objective

The finding is published with a disposition; the two parts that need only
documentation are done in the same task; a reporter learns from the index how
to find the digest of their own file.

## Acceptance Criteria

As in the header.

## Non-Goals

- A record field for the provider's stated reset time, or any schema change.
- Validating or aggregating `outcome` values in `record-session` or `report`.
- Any change in behaviour.
