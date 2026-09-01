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

### Re-read 2026-09-01 — remains deferred

What changed since: the sequencing precondition is met — `recorded_by` and its
source landed (ADR-0006), so records now say who created them. What did not
change is the blocker itself, and it has since hardened: ADR-0007 rejected a
distinct-party rule as a *default* for exactly the reason this deferral gave —
a rule requiring a different name is satisfied by typing a different name. The
opt-in record signing now planned covers review and acceptance records per
invocation; that is a foundation to build toward, not yet a base broad enough
to enforce roles against.

So the decision stands: role enforcement waits for identity that is verified
rather than declared. When it lands, ADR-0006's configurable policy layer is
where this belongs. The `scope_allow` migration note this disposition called a
documentation defect is now fixed in
[migration-v1-to-v2.md](../migration-v1-to-v2.md).
