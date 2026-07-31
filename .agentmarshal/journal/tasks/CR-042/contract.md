+++
schema = 1
id = "CR-042"
title = "user docs: quickstart + overview (brief, terminology, config, roadmap)"
scope = ["README.md", "docs/quickstart.md", "docs/overview.md"]
acceptance = [
  "docs/quickstart.md walks the full loop (install, init, open, implement, independent review, gate, complete, validate) with commands verified against published agentmarshal 0.1.0",
  "docs/quickstart.md has a Configuration section covering every user-facing setting in one place: AGENTMARSHAL_REVIEWER_CMD, AGENTMARSHAL_PIPELINE_OK_SHA, the model-reviewer verdict protocol, gate --attestation modes, contract scope/acceptance, and project.json",
  "docs/overview.md is a brief: purpose, the core idea, a simplified implementation scheme, a terminology glossary (incl. host repo), and a roadmap marked as roadmap",
  "docs do not overstate 0.1.0: capture policy and leak_scan are marked not-active-in-0.1.0, and no unimplemented guarantee is presented as active",
  "all cross-document links resolve; README links to overview and quickstart",
  "no code, schema, or gate change; validate/pytest/ruff/format/mypy stay green",
]
+++

# CR-042: user docs: quickstart + overview (brief, terminology, config, roadmap)

## Context

The repository is public and the package is on PyPI, but there is no
user-facing "how do I use this" documentation — the single biggest gap for a
new adopter. A reader had to reach the review step before discovering the
reviewer is configurable, and there is no brief explaining the product's
purpose, design, vocabulary, or direction.

## Objective

Ship two grounded documents — a hands-on Quickstart (with a consolidated
Configuration reference) and an Overview brief (purpose, simplified scheme,
terminology, roadmap) — so that a reader who has never seen the source can set
up a correct governance workflow in a new host repo. Every command is verified
against the published 0.1.0, and the 0.1.0 boundary is stated honestly.

## Acceptance Criteria

- [ ] `docs/quickstart.md` walks the full loop with commands verified against
      published 0.1.0, and consolidates every user-facing setting in one
      Configuration section (env vars, reviewer verdict protocol, attestation
      modes, contract fields, project.json).
- [ ] `docs/overview.md` gives the purpose, the core idea, a simplified
      implementation scheme, a terminology glossary (including "host repo"),
      and a roadmap explicitly marked as roadmap.
- [ ] No 0.1.0 overclaim: capture policy and `leak_scan` are marked
      not-active-in-0.1.0; unimplemented guarantees are not presented as live.
- [ ] All cross-document links resolve; README links to both docs.
- [ ] No code/schema/gate change; validate, pytest, ruff, format, mypy stay
      green.

## Non-Goals

- No Windows-specific instructions yet — those will be built from a real
  Windows-from-scratch run against these public docs, not written speculatively.
- No code, schema, or gate change; documentation only.
- Not a full manual — a quickstart and a brief, refined further as needed.
