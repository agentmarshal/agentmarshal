+++
schema = 2
id = "CR-098"
title = "The tool reports the preconditions it cannot verify, and the shipped template stops failing a head that cannot carry its review"
scope = [
  "src/agentmarshal/doctor.py",
  "src/agentmarshal/cli.py",
  "src/agentmarshal/project.py",
  "tests/test_doctor.py",
  "tests/test_cli.py",
  "templates/github/agentmarshal-governance.yml",
  "docs/self-hosting-workflow.md",
  "openspec/changes/report-what-the-tool-cannot-verify/",
  "openspec/changes/archive/",
  "openspec/specs/trust-preconditions/",
]
acceptance = [
  "every scenario in openspec/changes/report-what-the-tool-cannot-verify/specs/trust-preconditions/spec.md is demonstrated by a test whose docstring names it, except the template scenarios, which the shipped file has no harness for and whose reasoning is in design.md; the implementation follows design.md's decisions or records in design.md why it departed",
  "doctor reports on the actor variable, on whether the configured reviewer command's placeholders resolve, and on whether a CI definition invoking validate exists; no report prints the reviewer command's value, and a test asserts a secret in it does not appear",
  "an unmet precondition does not change doctor's exit status, and the summary line does not claim that all checks passed when one is unmet",
  "the template's gate job decides neutrality by the absence of a review record for the head SHA rather than by catching the gate's refusal, says so in its output, and no longer carries continue-on-error",
  "init prints the preconditions once with what each costs to skip, configures no provider and no harness, and tasks.md's checkboxes are ticked for the work that landed",
]
decisions = ["ADR-0001", "ADR-0006"]
documents = ["openspec/changes/report-what-the-tool-cannot-verify/", "openspec/specs/trust-preconditions/"]
+++

# CR-098: what the tool cannot verify, it reports

## Context

Two adopter reports describe one shape. Nine manual steps stand between `init`
and a first governed task, two of them corrupt the evidence silently when
skipped, and `doctor` reported four green checks with both unset (proposal 014).
The shipped provider template fails the gate check on every implementation pull
request, because the head cannot carry its own review record, and this project
worked around that privately instead of fixing the template (proposal 017).

## Objective

An operator is told what the tool's guarantees depend on and cannot check, is
told what it can check, and is not trained to ignore a red check that is red by
construction.

## Acceptance Criteria

As in the header.

## Threat model and boundaries

The two silent preconditions are the point. A guarantee that fails loudly costs
an operator an hour; one that fails silently costs the evidence. `doctor` stays
a report and gains no authority: provider and harness configuration belong to
those layers ([ADR-0001](../../../docs/adr/ADR-0001-governance-plane.md)), and
querying a provider would give `doctor` credentials and a network.

A check that is red by construction is worse than no check, because it teaches
an operator that red is normal.

## Non-Goals

- Querying a provider for its merge methods, or configuring anything.
- A wizard; the reporter explicitly did not ask for one.
- Review materialisation, which is what would let a head carry its own review.
- The remaining adopter findings: leak-scan, the reviewer's discarded stderr and
  the journal-branch pattern are the next task.
