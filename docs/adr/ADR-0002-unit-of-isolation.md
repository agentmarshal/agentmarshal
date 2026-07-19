# ADR-0002: The unit of isolation is the task

Status: Accepted
Date: 2026-07-19

## Context

Parallel agent work needs an isolation boundary: what gets its own
branch (and, at execution time, its own worktree)? The candidates seen
in practice are per-agent branches, per-role or per-scope branches, and
per-task branches. The industry converged during 2026 on
worktree-per-task as the default execution pattern in agent harnesses,
and AgentMarshal v1 ran task-scoped branches end to end; both point the
same way. Per-agent and per-scope branches share a failure mode: they
outlive any single reviewable change, so review loses its natural unit
and merges drift.

This ADR builds on [ADR-0001](ADR-0001-governance-plane.md): isolation
*execution* (worktrees, sandboxes) belongs to the harness; what is
decided here is the governance-side unit that contracts, reviews, gates
and evidence attach to.

## Decision

The unit of isolation is the **task**.

- One branch per task, machine-parseable as protocol data; at execution
  time, one worktree per task on the executor's side.
- The whole lifecycle — implement, review, complete — happens inside
  that unit and ends at the merge boundary.
- Decomposition escalates upward: when work splits, the lead opens new
  tasks. There are no persistent subtasks; hierarchy is allowed in
  planning but stays ephemeral, and the journal remains flat.
- Task creation and numbering are serialized through the target branch:
  the opening transaction (the task contract) lands in the target
  branch *before* implementation starts. The contract is visible to
  everyone; only the work is isolated.
- Worktrees isolate files and sandboxes isolate processes — execution
  concerns that stay with the harness per
  [ADR-0001](ADR-0001-governance-plane.md). What no harness isolates is
  shared runtime resources: ports, databases, registries, temporary
  state, journal-location resolution. For these, governance defines
  task-scoped naming and allocation rules in contracts and tooling so
  parallel tasks do not collide; provisioning and enforcement of the
  execution environment itself remain with the harness.

## Consequences

- Parallelism is bounded by task independence; making tasks independent
  is a planning obligation, not a tooling afterthought.
- Review always has a natural unit: the task's diff at an exact commit.
- The lead is the serialization point for opening tasks and therefore a
  bottleneck by design. This is accepted at the current scale;
  [ADR-0003](ADR-0003-scope-overlay.md) records the deferred relaxation
  path.
- Long-lived branches other than the target branch have no place in the
  model.
