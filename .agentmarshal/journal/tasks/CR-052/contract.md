+++
schema = 1
id = "CR-052"
title = "convention: an agent running AgentMarshal declares itself"
scope = ["docs/quickstart.md", "CONTRIBUTING.md"]
acceptance = [
  "docs/quickstart.md states the convention: when an agent runs AgentMarshal on someone's behalf, its session sets AGENTMARSHAL_ACTOR so records say an agent wrote them",
  "it explains why the actors table cannot do this: an agent commonly shares the human's git identity, so identity alone cannot separate them and only a declaration can",
  "it says where to put the setting durably — the harness session environment — rather than relying on remembering it per command",
  "CONTRIBUTING.md carries the same expectation for anyone contributing with an agent",
  "the honest limit is stated: this is a declaration an agent makes about itself, not a control, and an agent that does not set it is indistinguishable from the human whose identity it uses",
  "no code change; validate/pytest/ruff/format/mypy stay green",
]
+++

# CR-052: convention: an agent running AgentMarshal declares itself

## Context

CR-051 made records carry `recorded_by`, derived from the invoking git identity.
Dogfooding it here exposed the gap immediately: this project's own records now
read `recorded_by: <operator address> | git-identity`, because the agent commits
under the repository's configured identity. The field is correct and useless for
the case it exists for — it names the checkout, not the party.

The reason is structural, not a defect: an agent working on someone's behalf
normally *shares* that person's git identity, so the actors table, which maps
identity to actor, cannot separate them. Only a declaration can, which is what
the `AGENTMARSHAL_ACTOR` override is for.

Without a convention the mechanism half-works: the field exists, nobody sets it,
and the journal keeps conflating the two parties it was built to distinguish —
the conflation that produced six review records marked `vendor: human` here.

## Objective

State the convention where an adopter and a contributor will meet it: an agent
declares itself, in its session environment rather than per command, and the
limit of what that declaration establishes is stated plainly.

## Acceptance Criteria

- [ ] Quickstart states the convention and the environment variable.
- [ ] It explains why the actors table cannot substitute (shared git identity).
- [ ] It says to set it in the session environment, not per command.
- [ ] `CONTRIBUTING.md` carries the same expectation for agent contributors.
- [ ] The limit is stated: a self-declaration, not a control.
- [ ] No code change; suite green.

## Non-Goals

- Not enforcing it: nothing can detect an agent that declines to declare itself,
  and pretending otherwise would be the overclaim this project keeps correcting.
- Not a per-harness setup guide beyond naming where the setting belongs.
