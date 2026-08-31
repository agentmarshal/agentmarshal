+++
schema = 1
id = "CR-070"
title = "Harness guidance ages by principle, not by template"
scope = ["docs/harness-setup.md", "docs/templates/claude-code-settings.local.json", "docs/quickstart.md"]
acceptance = [
  "the harness guide states the things that do not depend on a harness version: declare the actor, deliver the contract with `agentmarshal brief`, and never let the agent write the journal",
  "the shipped permission template carries the harness and date it was verified against, and says plainly that it will age",
  "the guide states that the project does not track harness releases and that the reader owns the allowlist",
  "the guide covers operating a repository with more than one remote: pruning and cleanup target the working remote, never a mirror",
  "nothing in the guide claims a permission setting is required by AgentMarshal",
]
+++

# CR-070: Harness guidance ages by principle, not by template

## Context

This repository ships `docs/templates/claude-code-settings.local.json`, an
allowlist for one harness. Harnesses change their permission models and command
names on their own schedule, and this project has no way to track them and no
intention of taking on the obligation. A template that silently rots is worse
than none: a reader copies it, trusts it, and debugs the difference.

The operator's decision is that we do not ship more of them, and that the guide
carries general recommendations instead.

Not everything in that guide ages the same way, though, and the distinction is
the point of this task. Three things are facts about **AgentMarshal**, not about
any harness, and they belong stated concretely:

- an agent that runs the rails should declare itself through
  `AGENTMARSHAL_ACTOR`, or the journal conflates it with the human whose git
  identity it uses (ADR-0006, CR-052);
- an implementer should receive the contract through `agentmarshal brief`, which
  is the only delivery the tool provides (CR-061);
- the journal is not the agent's to write — records come from the commands.

Adopter proposal 010 also asks for a repo-level operations policy, and this is
where it belongs: `agentmarshal prune` never contacts a remote, so the hazard it
warns about — cleanup reaching a backup mirror — lives entirely in the
operator's own tooling and is guidance rather than code.

## Objective

Separate what ages from what does not, mark the template as perishable, and say
who owns it.

## Acceptance Criteria

- The guide states the harness-independent facts above, concretely: the actor
  declaration, `agentmarshal brief`, and the journal boundary.
- The shipped template carries the harness and the date it was verified
  against, and says plainly that it will age.
- The guide states that this project does not track harness releases, and that
  the allowlist is the reader's to maintain.
- The guide covers a repository with more than one remote: pruning and cleanup
  target the working remote, never a mirror, and one provider fails closed past
  roughly a hundred branches, which turns untidiness into an outage.
- Nothing in the guide claims a permission setting is required by AgentMarshal.
  The tool runs the same either way; permissions are about the harness stopping
  to ask.

## Threat model and boundaries

Documentation only. Nothing here executes.

The failure this task exists to prevent is a reader trusting a stale artefact —
so the fix is honesty about the artefact's shelf life, not a mechanism.

Not defects in this task: the template being wrong for some harness version, now
or later. That is the condition being disclosed rather than a problem to solve,
and this project takes on no obligation to track it.

## Non-Goals

- **Shipping a template for any additional harness**, or scaffolding one from
  `init`. That is the decision this task implements, not a question it reopens.
- Removing the existing template. A dated, disclaimed starting point is more
  useful than nothing; what it must not be is undated.
- Any code change, or any new command.
- A machine-readable policy for remotes. The tool contacts none.
