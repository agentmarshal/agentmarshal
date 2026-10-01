+++
schema = 1
id = "CR-122"
title = "Intake: proposal 026 (four findings from one file), and corrections to 025"
scope = [
  "docs/proposals/026-reviewer-facts-round-convergence-and-two-gaps.md",
  "docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md",
  "docs/proposals/README.md",
  "docs/README.md",
]
acceptance = [
  "docs/proposals/026-reviewer-facts-round-convergence-and-two-gaps.md digests the reporter's file in English under the pseudonym Adopter A with the profile the earlier digests' headers use, names the source by its sha256 e84a6250930b3145f82be59bcce626562bbd439c048eb13cded9d38f92246d44, quotes its measurements verbatim, and contains no identifier from the reporter's journal or repository — no task ids, record ids, file names, commit hashes, paths, package or client names",
  "the digest treats the file's four findings separately and gives each the disposition the coordinator's dispositions document states, with its reasoning; the leak-scan finding states that upstream reproduced it on 2026-10-01 and that it shares its cause with another adopter's report",
  "proposal 025 is corrected in three places: its disposition of proposal 2 no longer says that nothing in a record names the rules it was written under (every record carries schema and tool_version); the sentence about the run's output and the unread record reads plainly; the index's introduction to the 2026-08-30 batch no longer names one reporter of three",
  "the proposals index lists 026 in the 2026-09-24 batch with its disposition and where it went, and the documentation map has a line for it",
  "no statement names a release, task or document that is not published, and the full CI sequence passes",
]
+++

# CR-122: intake of proposal 026, corrections to 025

## Context

Adopter A's file 008, written 2026-09-03 and sent 2026-09-24, carries four
findings: a reviewer asserting external facts it could not check; review rounds
that do not converge; recording cost after `complete` needing idempotency; and
the leak scan skipping a whole diff that contains a binary file. Upstream
reproduced the last one on 2026-10-01; another adopter reported the same cause
from the review command. The coordinator's dispositions for all four are set.

Proposal 025 landed with three review advisories carried here, because this
task edits the same directory.

The original and the dispositions are private; the implementer reads them where
the frame says. Nothing that identifies the reporter's journal may reach this
public repository: a previous intake let three record identifiers into a pushed
branch.

## Objective

The file's four findings are published with a disposition each, and 025 says
what is true.

## Acceptance Criteria

As in the header.

## Non-Goals

- Adopter D's findings (separate intake tasks).
- Any change in behaviour, including the accepted items themselves.
