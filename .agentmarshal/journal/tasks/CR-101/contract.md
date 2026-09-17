+++
schema = 2
id = "CR-101"
title = "A review can be launched against a finding, and drift refuses the launch"
scope = [
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/artifacts.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/cli.py",
  "tests/test_review_launcher.py",
  "tests/test_findings.py",
  "tests/test_gate.py",
  "openspec/changes/review-binds-to-a-finding/",
  "openspec/changes/archive/",
  "openspec/specs/findings-review/",
  "docs/sidecar.md",
]
acceptance = [
  "every scenario in openspec/changes/review-binds-to-a-finding/specs/ is demonstrated by a test whose docstring names it; the implementation follows design.md's decisions or records in design.md why it departed",
  "a review launched against a finding of the task records a review that names that finding and no commit, with the reviewer's prose pinned as an artifact the way the commit path pins it",
  "a verdict whose subject is not the finding that was asked about records nothing, and the refusal names both subjects",
  "an artifact that no longer hashes to what the finding recorded refuses the launch before the reviewer runs, and a finding with no locally resolvable reference is refused",
  "the pinned commit-prompt test and the byte-for-byte gate transcript tests pass with their expectations unmodified, and the resolver deciding what resolves locally exists once",
]
decisions = ["ADR-0009", "ADR-0006"]
documents = [
  "openspec/changes/review-binds-to-a-finding/",
  "openspec/specs/findings-review/",
]
+++

# CR-101: A review can be launched against a finding

## Context

ADR-0009 gave a research task a way to land: a `finding` record pinning its
output by hash, a review that binds to that finding instead of a commit, an
acceptance that does the same, and a gate lane that evaluates them. All of it
shipped in CR-085/086 except the launcher: `agentmarshal review
--reviewed-finding` refuses with "not supported in this release; use the human
path".

The consequence showed up the first time the lane was used in earnest. A
research question reached a recorded, hash-pinned conclusion; the lane verified
all four artifacts and refused on one line — no review record for the latest
finding. The only available reviewer was a human, and ADR-0009's independence
check compares git identities: on a single-operator project the human's
identity is the identity the finding's recorder resolves to, so a human review
of it can never be independent. The deciding reviewer channel, which is
independent by construction, had no way in.

## Objective

Point the configured reviewer at a finding, on the bytes the finding pinned, and
record the verdict through the writer that already accepts `reviewed_finding`.

## Acceptance Criteria

See the `acceptance` field above. The scenarios they refer to are in
`openspec/changes/review-binds-to-a-finding/specs/findings-review/spec.md`; the
decisions the implementation is expected to follow, or to depart from with a
recorded reason, are in that change's `design.md`.

## Amended 2026-09-18

`docs/sidecar.md` joins the scope. Its findings-lane runbook routes a review of
a finding to `submit-review --reviewed-finding` — the human path — because that
was the only path when it was written. This task makes the automated path
exist, and both deciding runs named that runbook as the place an adopter would
look. Shipping a path in one release and its documentation in another is how
the adopter batch's finding 016 happened.

## Non-Goals

- Acceptance over a finding's blocking findings: the record and the CLI flag
  exist already and are not touched here.
- Fetching an artifact a reference does not resolve to locally. Named, never
  fetched.
- Any change to the gate's findings lane, the record schemas, or who decides.
- A size or count limit on what a prompt may carry: the commit path has none,
  and inventing one here would be a separate decision.
