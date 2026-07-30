+++
schema = 1
id = "CR-040"
title = "built in the open: transparency narrative in README"
scope = ["README.md"]
acceptance = [
  "README gains a 'Built in the open' section stating the repo dogfoods its own governance (real contracts, SHA-bound review verdicts, token-economics records under .agentmarshal/journal/)",
  "the section states that the repository was opened with full history on purpose (mistakes, abandoned tasks, token spend) and that history is not rewritten because the SHA-bound audit trail is the product",
  "the section links to ADR-0004, ADR-0005 and docs/migration-v1-to-v2.md as the honest 0.1.0-boundary account",
  "all links resolve to existing files; no claim overstates a 0.1.0 guarantee",
  "docs-only, no code behaviour change; validate, pytest, ruff, format, mypy stay green",
]
+++

# CR-040: built in the open: transparency narrative in README

## Context

The repository is now public. It opened with full history and its own
governance journal — deliberately, as a transparency and credibility asset —
but the README has no section that explains this to a first-time visitor. The
strongest signal the project has (an honest, SHA-bound record of how it was
actually built, including mistakes and token economics) is currently
undiscoverable without reading the journal directly.

## Objective

Give the README a short, honest "Built in the open" section that frames the
full history and the dogfooded journal as the point, not an accident, and
points readers to the design docs that already state the 0.1.0
implemented-vs-roadmap boundary (ADR-0004/0005, the v1→v2 migration note).

## Acceptance Criteria

- [ ] README gains a "Built in the open" section: the repo governs its own
      development; `.agentmarshal/journal/` holds real contracts, review
      verdicts bound to commit SHAs, lifecycle records and token-economics
      measurements.
- [ ] The section states the full history was published on purpose (mistakes,
      abandoned tasks, token spend) and that history is not rewritten — the
      SHA-bound audit trail is the product.
- [ ] The section links to [ADR-0004], [ADR-0005] and
      `docs/migration-v1-to-v2.md` as the honest 0.1.0-boundary account, and
      no sentence overstates a 0.1.0 guarantee.
- [ ] All links resolve; `uv run agentmarshal validate`, pytest, ruff, format
      and mypy stay green.

## Non-Goals

- No CONTRIBUTING.md, governance policy, or process docs — only the README
  narrative section (those can follow separately).
- No code, schema, or gate change.
- No new claims about implemented capability; the section only points to the
  existing honest boundary docs.
