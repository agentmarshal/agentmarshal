# CR-003: ADR-0001 — governance plane, not execution plane

Owner: lead
Type: docs
Priority: P2
Created: 2026-07-19
Status: done
Completion-Review: CR-003
Reviewed-Commit: 4b94bf22cfb5832234e5c26940876dd43343295b
Target-Branch: master
Merged-Commit: ef15ed4f4449652be8b9237dae2d40e0710b3d1c
Completed-At: 2026-07-19T01:03:26Z
Completion-Review-Artifact: .agentmarshal/journal/reviews/2026/CR-003-completion-4b94bf22cfb5.md
Completion-Review-SHA256: sha256:751e7d0a969c827cafadf408983bd2b661376ca08ed0ec91c1be2a2ca6514226
Scope:
- .agentmarshal/journal/tasks/open/CR-003-adr-0001-governance-plane.md
- docs/adr/

## Context

The project's founding decision — build the governance plane for
agent-driven development and deliberately not the execution plane — has
so far lived only in working discussions. It must be recorded as the
umbrella architecture decision before further design ADRs (unit of
isolation, scope overlay, journal data model) can reference it.

## Objective

`docs/adr/ADR-0001-governance-plane.md` records the decision, its
context and consequences, self-contained and public-safe.

## Acceptance Criteria

- [ ] The ADR exists under `docs/adr/`, follows a conventional ADR
      structure (Status, Date, Context, Decision, Consequences) and is
      readable standalone — no references to non-public materials.
- [ ] It states what v2 builds (durable, vendor-neutral, SHA-auditable
      evidence rails: contracts, independent SHA-bound review, merge
      gates, completion evidence, measurement; repository as the system
      of record).
- [ ] It states what v2 explicitly does not build (sandboxing,
      permissions, isolation, live orchestration — the harness
      execution plane) and confines harness glue to adapters.
- [ ] It fixes authority placement: gate authority server-side only;
      client-side mechanisms are advisory.
- [ ] It names the follow-up ADRs it anchors (unit of isolation, scope
      overlay, journal model) without deciding them.

## Non-Goals

- No decisions beyond the plane boundary itself; follow-up ADRs are
  separate tasks.
- No process/tooling changes.
