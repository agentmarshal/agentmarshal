# ADR-0003: Scope is a coordination overlay, not an isolation unit

Status: Accepted
Date: 2026-07-19

## Context

Once the task is the unit of isolation
([ADR-0002](ADR-0002-unit-of-isolation.md)), the question remains what
"scope" — an area of the codebase — means for the model. The tempting
answer, long-lived per-scope branches or per-scope repositories, is a
known anti-pattern: such branches outlive reviewable changes and
accumulate merge drift. Mature ecosystems solve coordination over shared
code differently — ownership metadata over paths (CODEOWNERS-class
mechanisms), module tags and affected-graphs in monorepo tooling — all
overlays on trunk-based development, none of them isolation units.

## Decision

Scope is a **coordination overlay** over paths.

- In the core model, scope is a list of paths in the task contract. The
  merge gate — the server-side authority boundary fixed in
  [ADR-0001](ADR-0001-governance-plane.md) — enforces `diff ⊆ scope`:
  a change outside the declared scope does not merge.
- Scope is never an isolation unit. Long-lived per-scope branches are
  rejected explicitly; all work rides per-task branches into the target
  branch.
- The growth path is an **ownership layer** on top: path sets owned by
  roles or owners, checked at the same gate. A cross-scope task then
  requires a primary owner and review by the owners of every touched
  scope — the pattern the industry already exercises for shared code.
- **Delegated coordination is deferred.** Per-scope leads and
  partitioned task numbering are a scaling mechanism for the day a
  single lead saturates as the serialization point of ADR-0002. Until
  then the single-lead bottleneck is accepted and named, not designed
  around speculatively.

## Consequences

- The core stays cheap: the scope check is a set comparison at the
  gate, available from day one.
- Contracts become more precise: declaring scope up front is part of
  task design, and scope violations surface at the boundary instead of
  in review archaeology.
- Ownership semantics can be added without changing the isolation
  model, because they attach to the same path overlay.
- When delegation does arrive, it partitions coordination (who opens
  and serializes tasks where) — not isolation, which stays per-task.
