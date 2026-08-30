+++
schema = 1
id = "CR-043"
title = "CONTRIBUTING: contribution language policy + governed-flow guide"
scope = ["CONTRIBUTING.md"]
acceptance = [
  "CONTRIBUTING.md states the language rule by artifact type: public artifacts (docs, ADRs, proposals, commit messages, PR text, code comments) are English; incoming reports are English-preferred but accepted in any language, with an explicit caveat that we may ask for English if we cannot process it",
  "it gives a report template whose value is in measurements (symptom, exact command/output, counts, tool version, environment, expected behaviour) so the English bar is low",
  "it explains that this repository governs itself with AgentMarshal: a contribution must pass the same gate the tool ships (contract scope, independent review with reviewer email != commit authors, pipeline attestation) and points at the fork-PR trust boundary",
  "it documents the proposals channel: adopters collect findings downstream, upstream lands them under docs/proposals/ as English digests with a disposition",
  "it lists the local CI sequence and the licence; validate/pytest/ruff/format/mypy stay green",
]
+++

# CR-043: CONTRIBUTING: contribution language policy + governed-flow guide

## Context

The repository is public and has adopters sending upstream proposals, but there
is no `CONTRIBUTING.md` at all. Two gaps hurt today:

- **Language is undefined.** Everything public is English, while incoming
  proposals arrive mostly in Russian. Without a stated rule the choice is made
  ad hoc, and an "English only" rule would contradict the intake pipeline
  (originals stay with the reporter, upstream publishes English digests) and be
  broken by our own first submissions.
- **The governed flow is undocumented for contributors.** This repository is
  self-hosted on AgentMarshal: a pull request must pass the same gate the tool
  ships — contract scope, independent review, pipeline attestation. A
  contributor who does not know this gets refused without understanding why.

## Objective

Add `CONTRIBUTING.md` that states the language rule by artifact type, lowers the
English bar with a measurement-first report template, documents the proposals
channel, and explains the governed contribution flow including the fork-PR trust
boundary.

## Acceptance Criteria

- [ ] Language rule split by artifact type: public artifacts English; incoming
      reports English-preferred, any language accepted, with the honest caveat.
- [ ] Report template centred on measurements, not prose.
- [ ] Governed-flow section: contract scope, reviewer independence, pipeline
      attestation, fork-PR trust boundary (pointer to github-enforcement.md).
- [ ] Proposals channel documented (downstream collection -> `docs/proposals/`
      English digests + disposition).
- [ ] Local CI sequence + licence; the suite stays green.

## Non-Goals

- Not creating `docs/proposals/` or importing any proposal yet (separate task).
- Not a code of conduct, not a governance/maintainer policy.
- No code, schema, or gate change.
