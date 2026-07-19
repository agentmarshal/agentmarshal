# CR-004: ADR-0002 unit of isolation and ADR-0003 scope overlay

Owner: lead
Type: docs
Priority: P2
Created: 2026-07-19
Status: done
Completion-Review: CR-004
Reviewed-Commit: cf625763df5d119c3b310f29857dd1662aca4211
Target-Branch: master
Merged-Commit: cc114ba839499ceb51617dbf2385e6d0105ec27d
Completed-At: 2026-07-19T01:33:05Z
Completion-Review-Artifact: .agentmarshal/journal/reviews/2026/CR-004-completion-cf625763df5d.md
Completion-Review-SHA256: sha256:4775c5386154994d077af2325f4c3243d7adfee392bebe3142f45870426565e3
Scope:
- .agentmarshal/journal/tasks/open/CR-004-adr-isolation-and-scope.md
- docs/adr/

## Context

ADR-0001 fixed the plane boundary and named its follow-up decisions. Two
of them are ready to record and are naturally paired — the unit of
isolation for parallel work, and the role of scope once it is *not* that
unit. Both are problem-first decisions already exercised in practice by
this repository's own workflow (every task so far rode one branch per
task with a path-scope check at the gate). One task covers both ADRs:
they are small, mutually referencing and share one review context.

## Objective

`docs/adr/ADR-0002-unit-of-isolation.md` and
`docs/adr/ADR-0003-scope-overlay.md` record the two decisions,
self-contained and public-safe.

## Acceptance Criteria

- [ ] ADR-0002 fixes the unit of isolation as the **task**: one
      branch/worktree per task; the implement→review→complete lifecycle
      lives inside it; decomposition escalates to the lead as new tasks
      (no persistent subtasks); the journal stays flat; task creation is
      serialized through the target branch (the opening transaction
      lands before implementation starts).
- [ ] ADR-0002 names runtime isolation (ports, databases, temp state,
      journal location) as governance-side work not assumed from the
      execution plane.
- [ ] ADR-0003 fixes scope as a **coordination overlay**: a list of
      paths in the task contract enforced as `diff ⊆ scope` at the
      gate; never an isolation unit; long-lived per-scope branches are
      rejected explicitly.
- [ ] ADR-0003 records the growth path (ownership layer over paths,
      cross-scope tasks via a primary owner plus review by owners of
      touched scopes) and defers delegated coordination (per-scope
      leads, partitioned task IDs) until a single lead saturates,
      naming the single-lead bottleneck honestly.
- [ ] Both ADRs follow the ADR-0001 structure, cross-reference each
      other and ADR-0001, and contain no references to non-public
      materials.

## Non-Goals

- No ownership/roles implementation, no scope-model code — decisions
  only.
- No journal data-model decisions (that is the next ADR).
