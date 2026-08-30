+++
schema = 1
id = "CR-046"
title = "ADR-0006: actors, declared identity, and multi-operator work"
scope = ["docs/adr/ADR-0006-actors-and-identity.md"]
acceptance = [
  "the ADR decides what an actor is in the model and that records carry a recorded_by actor, separate from the semantic reviewer field, while stating plainly that recorded_by is a declaration and not authentication",
  "it states exactly what the tool claims and does not claim before review records are signed, and requires the gate's own output to describe the independence check as a comparison of declared identities",
  "it decides decision rights as opt-in project policy with defaults preserving current behaviour: distinct-actor review, who may override findings, whether one actor may carry a task end to end",
  "it decides the multi-operator coordination questions it can decide without new machinery (task-number allocation by landing the opening first, one checkout per operator) and says why no reservation mechanism is added",
  "it states its own boundary: signing, role permissions and hooks are out of scope and named as dependent later work",
  "no code, schema or gate change in this task; validate/pytest/ruff/format/mypy stay green",
]
+++

# CR-046: ADR-0006: actors, declared identity, and multi-operator work

## Context

Two questions arrived together and turn out to be the same question.

An operator asked whether AgentMarshal is ready for two human operators on one
project. The evidence model is: records are append-only with collision-resistant
identifiers, state is a projection, the contract is read from the base side, and
separate checkouts remove working-tree contention. The identity layer is not:
records do not say who created them, and the gate's independence check compares
an email string.

At the same time this project demonstrated the consequence on itself. Six review
records marked `vendor: human` under an operator's address were produced by an
agent; every gate passed, including a line reading "reviewer is independent of
the candidate's writers". Nothing in the evidence distinguishes those records
from ones a person created. With one operator that is self-deception; with two it
becomes impersonation of a colleague, and the record looks identical either way.

Adopter proposal 003 asks for roles bound to scope; it was deferred on the
grounds that enforcement over unauthenticated identity creates the appearance of
a control. That reasoning now has a demonstration behind it, and it needs to be
written down as a decision rather than a disposition note.

## Objective

Decide the actor model, state honestly what identity in the journal does and does
not establish before signing exists, and settle the multi-operator questions that
can be settled without new machinery — so that later work on signing, roles and
overrides has a stated foundation instead of an implicit one.

## Acceptance Criteria

- [ ] Actor defined; `recorded_by` decided and explicitly named a declaration.
- [ ] Claim boundary stated; the gate's independence line must describe a
      declared-identity comparison.
- [ ] Decision rights as opt-in policy, defaults unchanged.
- [ ] Coordination decided without new machinery, with the reasoning.
- [ ] Own boundary stated (signing, roles, hooks are later and dependent).
- [ ] No code change; the suite stays green.

## Non-Goals

- Not implementing `recorded_by`, the policy checks or the gate wording — this
  task decides; the changes follow as separate tasks.
- Not designing the signing scheme.
- Not deciding role-to-scope permissions (proposal 003) beyond stating the
  dependency.
