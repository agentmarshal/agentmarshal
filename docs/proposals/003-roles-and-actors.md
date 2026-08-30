# 003 — Scope is not bound to an actor

- **Reporter:** Adopter A (Python web service on Linux) · **Observed on:** 0.1.0 · **Disposition:** deferred

## Finding

A contract declares a scope, but nothing connects that scope to who is entitled
to declare it. Preparing to run a second role, Adopter A looked for the
mechanism that would stop a frontend agent from touching backend paths and found
none: any actor can open a task with any scope and pass the gate cleanly.

The report notes that a v1 mechanism, `scope_allow`, disappeared in v2 with no
replacement and no mention in the migration notes, and that scaffolding creates
no place to configure roles.

## Proposed

A notion of actor with an allowed scope, checked when a task is opened.

## Disposition — deferred

The observation is correct and structural rather than cosmetic: AgentMarshal
models tasks and evidence, not actors. It is deliberately outside the current
trust boundary — the gate authenticates neither the recorder nor the actor, and
adding role enforcement without authentication would create the appearance of a
control that a rename could bypass.

Deferred rather than declined because the underlying question is real, and
because the missing migration note about `scope_allow` is a genuine documentation
defect we should fix regardless. Sequencing: record provenance first, then
actors; a role model resting on unauthenticated identity would overclaim.
