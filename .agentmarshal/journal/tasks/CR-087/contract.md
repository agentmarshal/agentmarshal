+++
schema = 1
id = "CR-087"
title = "ADR-0010: process tools plug in through a declared footprint, not a hook"
scope = ["docs/adr/ADR-0010-process-extensions.md"]
acceptance = [
  "the ADR exists at the scoped path, reads Status: Accepted, and states up front that it decides and does not implement",
  "it names the extension manifest and its fields, states that footprint and documents entries use the scope syntax (an exact path, or a directory prefix ending in a slash), and states that AgentMarshal executes none of the manifest's commands",
  "it states which command reads the manifest at which lifecycle point (open, brief, complete, gate), and that no extension-defined code runs inside the gate",
  "it fixes the operator's decisions of 2026-09-06: installing or removing an extension is a task with review; a contract that names documents makes a candidate that leaves them untouched a gate refusal; the contract header moves to schema 2 with optional fields while schema-1 contracts keep their behaviour",
  "it states what a governed extension establishes and what it does not, in the manner of ADR-0006 and ADR-0009 §5",
  "it records the alternatives considered — lifecycle hooks, bundling a tool, an SDK with a registry, harness-native plugins alone, a sandbox — and why each was not taken",
  "the diff touches the one scoped file and nothing else",
]
+++

# CR-087: ADR-0010

## Context

An adopter declined AgentMarshal in favour of OpenSpec: a living, agent-written
system description fed into the model's context. Proposal 009 asked for
lifecycle hooks and was deferred because a hook running at a gate boundary
becomes something the gate trusts. Both point at the same missing seam: a
third-party process tool has no governed place in our lifecycle — its
footprint is unbounded, its output never reaches the implementer's context
through us, and removing it is a matter of memory.

The operator considered and rejected a plugin platform (installer, sandbox,
SDK, registry) and chose the smallest governed form: a declared manifest whose
footprint is scope, whose documents reach the implementer and the reviewer,
whose untouched documents the gate refuses, and whose removal is verified.

## Objective

Record that decision as ADR-0010 with its claim boundary and alternatives, so
the implementation tasks (contract header fields, `brief` and reviewer prompt,
one gate line, the first manifest for OpenSpec) have a decision to be reviewed
against — as ADR-0009 did for CR-086.

## Acceptance Criteria

- `docs/adr/ADR-0010-process-extensions.md` exists, reads `Status: Accepted`,
  and says in its preamble that the mechanism is not implemented by the
  document.
- It names the manifest (`.agentmarshal/extensions/<name>.toml`) and its
  fields, states that `footprint` and `documents` entries use the scope
  syntax — an exact path, or a directory prefix ending in `/` — and that the
  `install` and `remove` strings are recorded, never executed by AgentMarshal.
- It states which command reads the manifest where: `open` (footprint into
  effective scope when the contract names the extension), `brief` (documents
  and decisions into the implementer's context, named in the reviewer prompt),
  `complete` (artifacts pinned; removal refused while footprint paths remain
  in the candidate tree), `gate` (one line for named documents) — and that
  no extension-defined code runs inside the gate.
- It fixes the three operator decisions of 2026-09-06 named in the header.
- It states what a governed extension establishes and what it does not.
- It records the alternatives considered and why each was not taken.
- The diff touches the one scoped file and nothing else.

## Threat model and boundaries

The hazard is an ADR that reads as shipped behaviour, or as a safety claim:
"installed under governance" must not be read as "vetted". The preamble and
the establishes/does-not section hold both boundaries.

The second hazard is a gate whose decision depends on third-party code. The
ADR closes it by construction: the gate reads manifests and diffs and executes
nothing.

Not a defect here: that nothing is built. That is the next tasks.

## Non-Goals

- **Any code.** No contract field, no `brief` change, no gate line, no CLI.
- Updating proposal 009's disposition, the overview, quickstart or sidecar
  docs — they follow the implementation, where they can point at what exists.
- Shipping or describing an OpenSpec template; the ADR may name OpenSpec as
  the first intended extension and as the example in its manifest, and that
  is permitted.
- Deciding `extension add` / `extension remove` commands; the ADR may say
  they are decided after the dogfood, and that is permitted.
- Specifying the `decisions` header field beyond naming it alongside
  `documents` and `extensions` as a schema-2 field fed to `brief`; its
  `open` warning and reviewer wording belong to the implementation task.
