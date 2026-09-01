+++
schema = 1
id = "CR-078"
title = "Re-read the deferred proposals, and pay the two debts their dispositions named"
scope = ["docs/proposals/003-roles-and-actors.md", "docs/proposals/004-provider-ci-integration.md", "docs/proposals/005-research-findings-have-no-record-type.md", "docs/proposals/009-lifecycle-extension-points.md", "docs/proposals/README.md", "docs/migration-v1-to-v2.md"]
acceptance = [
  "each of the four deferred dispositions carries a dated re-read note stating what changed since deferral and what the decision now is, with the original text left standing",
  "proposal 005's disposition becomes accepted, with the sequencing that avoids designing the record type twice",
  "proposals 003, 004 and 009 remain deferred, each with the reasoning re-checked against what has landed since",
  "the batch table and its counts in the proposals README match the dispositions, counted rather than eyeballed",
  "the migration document gains the scope_allow note that 003 called a documentation defect, and states that the empty integration directories are v1 leftovers the published v2 never creates",
]
+++

# CR-078: Re-read the deferred proposals, and pay the two debts their dispositions named

## Context

Four adopter proposals were deferred in the 2026-08-30 intake, each with a
recorded reason. The 0.3.0 plan requires re-reading them one at a time with
that reason in front of us — not flipping them in bulk, which would devalue the
disposition record itself.

Since the deferrals, the ground moved: `recorded_by` landed (the sequencing
precondition two deferrals named), ADR-0007 hardened the argument about
enforcement over declared identity, ADR-0008 decided journal placements and
gave research-class records a natural home, and the signing plan schedules the
in-toto projection that 005's deferral was waiting on. One external data point
arrived as well: a published practitioner workflow demonstrating hand-rolled
research journals outside the repository.

Two dispositions also named side debts to fix regardless of the decisions:
the missing `scope_allow` migration note (003), and the undocumented empty
integration directories (004). Measured while preparing this task: those
directories are **v1 leftovers** — the published v2 `init`, checked against an
installed 0.1.0 and against current source, creates none of them.

## Objective

Four explicit decisions with their reasoning, and two debts paid where they
belong — in the migration document.

## Acceptance Criteria

- Each deferred disposition gains a dated re-read note: what changed since, and
  the decision now. The original deferral text stays — the disposition history
  is the point of the record.
- **005 becomes accepted**: its sequencing blocker dissolves inside the 0.3.0
  plan (projection scheduled, sidecar placement decided), and the design is
  sequenced so the record type is shaped once — during the sidecar dogfood,
  alongside the projection work.
- **003, 004 and 009 remain deferred**, each re-checked: 003 until identity can
  be verified rather than declared; 004 until there are provider integrations
  beyond the two we run ourselves; 009's general hooks unchanged, with its
  narrower storage case noted as partly landed via artifacts pins and
  placements.
- The README batch table and its counts match the dispositions — counted
  programmatically, per the standing lesson about arithmetic in prose.
- The migration document states what `scope_allow` was, that v2 replaced it
  with the contract's scope as the only scope mechanism, and that the empty
  `integrations/`/`plugins/` directories are v1 leftovers safe to delete.

## Threat model and boundaries

Documents recording judgements. Nothing executes.

The hazard is **disposition drift**: re-reading four deferrals and flipping the
convenient ones without new evidence would turn the disposition record into
decoration. Each decision below must cite what actually changed, and a deferral
re-affirmed is as much a result as an acceptance.

Not defects in this task: implementing 005 (sequenced into wave J/S work);
disagreement by a reporter with a re-affirmed deferral, which is the channel
working as designed.

## Non-Goals

- Implementing anything, including 005's record type.
- Re-opening the accepted or declined dispositions of the batch.
- Rewriting the original deferral texts. Notes are appended, history stands.
