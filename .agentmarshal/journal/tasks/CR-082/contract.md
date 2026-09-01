+++
schema = 1
id = "CR-082"
title = "The second install-and-operate path: a journal without rails"
scope = ["docs/sidecar.md", "docs/quickstart.md", "docs/overview.md", "README.md", "pyproject.toml"]
acceptance = [
  "docs/sidecar.md exists and is a complete install-and-operate path: install, initialization, the loop end to end, and inspection",
  "it is labelled experimental and states that the placement is not in the published 0.2.0 release",
  "it states what sidecar evidence establishes and what it does not before it gives any instruction",
  "it names the weakening a reader cannot infer: the gate advises, and the contract is read from the sidecar working tree rather than pinned to a base commit",
  "every command and every quoted transcript in it was run, not composed",
  "it records the frictions found by operating a sidecar, including that a research finding has no commit to bind to",
  "it states the host-inviolability invariant and separates what the tool enforces from what the operator must do",
  "the embedded path stays the default: quickstart, overview and README point at the new document instead of teaching two paths at once",
  "no claim in it asserts enforcement, authentication or verification that 0.2.0 does not perform",
  "the install command it gives is corroborated by the repository itself, so a reader offline can check the source it names",
]
+++

# CR-082: The second install-and-operate path

## Context

ADR-0008 accepted a second journal placement and named its cost outright: the
documentation forks, and that fork is most of the work. CR-079 built the
placement, CR-080 unblocked measurement inside it, CR-081 made the gate advise
and every surface say which regime produced its evidence. Each of those tasks
listed this document in its Non-Goals, deferring it until we had operated a
sidecar rather than imagined one.

We have now. A private research journal over this repository ran the loop and
surfaced frictions no reading of the code would have produced — most
importantly that the tool's vocabulary assumes throughout that a task changes
the host, and that a research finding has no commit to bind a review record to.

## Objective

Write the second install-and-operate path, and leave the first one the default.

## Acceptance Criteria

- `docs/sidecar.md` is a complete path from installing the package to a task
  carrying records: install, sidecar creation, `init --host`, the loop, and
  inspection.
- It is labelled **experimental** at the top, and says the placement is not in
  the published 0.2.0 release.
- It states **what sidecar evidence establishes and what it does not** before
  the first instruction, not in a closing caveat.
- It names, in that section, the two weakenings a reader cannot infer from the
  embedded documentation: the gate **advises**, and the contract is read from
  the sidecar working tree rather than pinned to a base commit — so scope
  discipline rests on the sidecar's history, not on the gate.
- Every command shown, and every transcript quoted, was **run** against this
  build on throwaway repositories.
- It records the frictions found by operating a sidecar, including the one with
  no workaround: a research finding has no commit to bind to, so no existing
  record type can say it was checked.
- It states the host-inviolability invariant, and separates what the tool
  enforces (it writes nothing to the host; `prune --delete` is refused) from
  what only the operator can hold (never adding anything to the host, never
  naming the sidecar in it).
- The embedded placement remains the default everywhere else: `quickstart.md`,
  `overview.md` and `README.md` gain a pointer, not a second lesson.

## Threat model and boundaries

The hazard is **a document that reads as an equal alternative**. A reader who
adopts a sidecar believing it enforces what the embedded placement enforces
gets records that decide nothing and a contract nothing pins, while quoting
them as though a gate had passed. Every honest statement here exists to stop
that reading, which is why they precede the instructions rather than follow
them.

The second hazard is the one ADR-0008 Decision 3 forbids: the host learning
that a sidecar exists. A document that teaches an ignore rule, a config key or
a naming convention inside the host would teach the leak. The instructions must
keep every trace outside the host.

Not defects in this task: the frictions themselves — they are reported, not
fixed here; the absence of a record type for research findings (proposal 005);
and the fact that an advisory gate can be ignored, which is what advisory means.

## Non-Goals

- **Any code change.** This task is documentation, with one amended exception
  (below). A friction found while writing it is recorded in the document and,
  if it deserves fixing, opened as its own task.
- Changing the default placement, or recommending a sidecar where the embedded
  placement is available.
- A record type for research findings. Accepted as proposal 005, built
  separately.
- Translating or restructuring the rest of the documentation set.

## Amendment (2026-09-01)

`pyproject.toml` is added to the scope for one line: `[project.urls]`.

Four consecutive review rounds refused the document's very first command —
`pip install "git+https://github.com/agentmarshal/agentmarshal@<pin>"` — on the
ground that the repository publishes that address nowhere. The premise is true
and checkable: the string occurs exactly once in the whole tree, in the new
document itself, and the published package declares no project URLs at all. The
conclusion drawn from it (that the command was never run) is false — it was run
twice into clean environments — but a reader has no more way to check that than
the reviewer did.

That is a defect in the repository, not a disagreement about the document. A
project whose install instructions cannot be corroborated from its own source is
one line short, and the document cannot satisfy its own acceptance criterion
about verified commands while that line is missing.

The exception is exactly that line. No other code, no other file.
