+++
schema = 2
id = "CR-108"
title = "A newcomer finds where to report, how to report, and what a change here must carry"
scope = [
  "SECURITY.md",
  ".github/ISSUE_TEMPLATE/",
  ".github/pull_request_template.md",
  "docs/README.md",
  "CONTRIBUTING.md",
  "README.md",
]
acceptance = [
  "SECURITY.md names exactly one private reporting channel, GitHub private vulnerability reporting, and lists what counts as a vulnerability for this tool — at least: bypassing the gate, forging or altering a review or completion record undetected, a leak-scan output that prints what it exists to withhold, and a command that leaves a journal invalid; it promises no response time",
  "the issue form for a finding carries the report format CONTRIBUTING already defines — symptom with the exact command and output, measurements, version, environment, expected — as required fields, and states the language policy in its header; a second form covers a gate refusal whose reason is unclear; config.yml disables blank issues and links to SECURITY.md",
  "the pull-request template lists what this repository's process requires of a change — the task CR-NNN, a diff inside the contract's scope, the local checks passing, an agent declaring itself through AGENTMARSHAL_ACTOR, English public artefacts — and each item matches what CONTRIBUTING.md says",
  "docs/README.md maps every document under docs/ by what a reader wants to do, and README.md links to it",
  "CONTRIBUTING.md says plainly that one person maintains the project and what that means for response time, instead of promising one",
  "nothing links to a feature this repository does not have enabled — no Discussions link, no support channel that does not exist",
]
+++

# CR-108: where to report, how to report, and what a change must carry

## Context

An outside audit of the repository (2026-09-18) found the project's contributor
material strong in substance and absent at the point of use: the report format,
the language policy and the process requirements live inside CONTRIBUTING.md,
not in the form a person fills in when they press "New issue" or "Create pull
request". There is no SECURITY.md, which for a tool whose whole claim is
evidence someone can trust is the sharpest gap. There is no map of docs/.

The adopters who file findings are the outside participants that matter at this
stage, and their channel already works; this task puts it where they will see
it.

## Objective

A newcomer finds, at the moment they act, where to report a vulnerability, how
to report a finding, and what a change here must carry.

## Acceptance Criteria

See the `acceptance` field above.

## Non-Goals

- Repository settings — description, topics, homepage, private vulnerability
  reporting, Discussions, Releases. They are not files; the operator sets them.
- A response-time promise. One person maintains this project.
- CODEOWNERS, good-first-issue labels, and the question of who records the
  independent review for a pull request from a fork: that last one needs a
  decision, not a document, and the other two wait for it.
- Any change in behaviour.
