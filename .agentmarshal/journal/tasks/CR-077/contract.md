+++
schema = 1
id = "CR-077"
title = "ADR-0008: journal placements and what each placement can claim"
scope = ["docs/adr/ADR-0008-journal-placements.md"]
acceptance = [
  "the ADR decides that placement is a property of a journal within one tool, and names the two placements",
  "it decides that a task lives in exactly one journal and that state is never projected across journals",
  "it decides the reference direction: a sidecar references its host, and a host repository carries no reference to — and no marker of the existence of — any private journal",
  "it decides where a sidecar journal lives relative to the host worktree, with the reasoning",
  "it decides what running without rails means: which machinery works, what the gate is in that mode, and how every surface keeps advisory evidence distinguishable from gated evidence",
  "it states the claim boundary of sidecar evidence in the manner of ADR-0006",
  "it names the documentation consequence — a second install-and-operate path — without writing those documents",
]
+++

# CR-077: ADR-0008 — journal placements and what each placement can claim

## Context

The journal lives in `.agentmarshal/` of the governed repository, and the rails
depend on that: the gate reads the contract from the base side of the same
history the candidate belongs to. That is the right design where the operator
controls the repository — and a hard wall where they do not.

Two measured pressures, one from each side of that wall:

- **Our own operation.** Evidence that the method itself depends on — research
  notes, pre-registered findings, incident context — lives in a private
  repository beside this one, invisible to the tool: no records, no SHA
  binding, no report. The practice that caught real defects three times this
  release exists as loose files.
- **Adoption.** A practitioner working in an employer's repository cannot
  install anything into it, and demonstrably keeps a hand-rolled journal
  outside it instead — PRD files in a personal directory, with attempt logs and
  artifacts. The demand is real; the machinery is absent.

The operator has set three requirements for the design: private and public
journals must coexist over one project **without duplication and without the
private side's existence leaking into the public repository**; the tool must be
usable **without rails** at all; and the answer must say what it does to
installation and operating documentation, which it will cut across.

## Objective

Decide the model before building it: what placements exist, what each can
honestly claim, and which direction references may flow.

## Acceptance Criteria

- Placement is a property of a **journal**, not a separate product; the two
  placements are named and the tool stays one tool.
- A task lives in exactly one journal; state is never projected across
  journals.
- Reference direction is decided: a sidecar references its host; the host
  repository and any embedded journal carry **no reference to, and no marker of
  the existence of**, any private journal. Any disclosure toward a private
  store is an explicit opt-in, never a default.
- Where a sidecar lives relative to the host worktree is decided, with
  reasoning.
- Running without rails is defined: which machinery works, what the gate is in
  that mode, and how surfaces keep advisory evidence distinguishable from
  gated evidence — the principle already set by "accepted never reads as
  approved".
- The claim boundary is stated in the manner of ADR-0006: what sidecar
  evidence establishes and what it does not.
- The documentation consequence is named, not written.

## Threat model and boundaries

This task writes one document. Two hazards belong to the *decision* and must
shape its wording:

- **Information flow.** The public side must not learn that a private journal
  exists — not through a reference, a marker file, an ignore rule, or a
  convention. One wrong default here and every adopter with a private journal
  leaks its existence into their employer's history.
- **Overclaim by indistinguishability.** Evidence produced without enforcement
  must never present as enforced. This project has a recorded relapse pattern
  around attestation claims, and a placement whose records read identically to
  gated ones would be that relapse built into the format.

Not defects in this task: implementing anything; the exact config keys or
command flags, which belong to the implementing tasks.

## Non-Goals

- **Implementing any of it.** Code follows in its own tasks.
- Multi-host journals — one sidecar spanning several host repositories. Named
  as future work; deciding it now without a driving case would be design in
  the dark.
- Synchronisation or hosting of a shared sidecar. It is a git repository;
  teams share it the way they share any repository.
- Changing anything about the embedded placement, which remains the default
  and is untouched.
