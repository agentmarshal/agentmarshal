+++
schema = 2
id = "CR-099"
title = "The gate can be asked to judge what does not depend on a review, and the shipped template asks for it"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/cli.py",
  "tests/test_gate.py",
  "templates/github/agentmarshal-governance.yml",
  "docs/github-enforcement.md",
  "openspec/changes/gate-without-a-review/",
  "openspec/changes/archive/",
  "openspec/specs/gate-lanes/",
]
acceptance = [
  "every scenario in openspec/changes/gate-without-a-review/specs/gate-lanes/spec.md is demonstrated by a test whose docstring names it, except the two in section 2 of tasks.md, which the shipped template and the document have no harness for; the implementation follows design.md's decisions or records in design.md why it departed",
  "the mode changes only the case where the candidate has no review record: with a review record present, approving or not, the review-bound checks are evaluated and report what they report without the mode, and a test pins each",
  "a run that does not request the mode produces the transcript it produces today: the pinned 0.3.0 transcript test and the sidecar transcript tests pass with their expectations unmodified",
  "the not-examined lines name both checks and the reason, and a refusal for any other rule is unaffected by the mode",
  "the shipped template asks for the mode, carries no guard of its own and no continue-on-error on that job, docs/github-enforcement.md describes what now exists, and tasks.md's checkboxes are ticked for the work that landed",
]
decisions = ["ADR-0002", "ADR-0005"]
documents = ["openspec/changes/gate-without-a-review/", "openspec/specs/gate-lanes/"]
+++

# CR-099: the gate judges what it can, and says what it did not

## Context

The shipped provider template runs the gate on a pull-request head that cannot
carry its own review record, so it refuses every implementation pull request and
the job is marked tolerated. An adopter reported the consequence: the check-run
is red on every implementation pull request, and the documentation calls it
advisory while the provider has no such state (proposal 017).

The previous task tried to fix this in the template and was refused in review:
the only thing a template can do is skip the gate entirely, which drops the
checks the run does enforce. The capability belongs in the gate.

## Objective

A caller that cannot yet have a review can ask the gate for everything else, and
read in the transcript exactly what was not examined.

## Acceptance Criteria

As in the header.

## Threat model and boundaries

The mode must not be a bypass. It changes one case — no review record at all —
and leaves every other check, and every candidate that has a review, exactly as
they are. A candidate whose review refuses it is refused under the mode too.

Not examined is printed, never implied: a transcript that omits a check reads as
a check that passed, and this project's own merge authority must be able to tell
the two apart at a glance.

## Non-Goals

- Review materialisation from a provider approval; that is what would let a head
  carry its own review, and it is not this task.
- Changing what a recorded review means, or the attestation flag.
- Any change to the findings lane's own not-examined lines.
