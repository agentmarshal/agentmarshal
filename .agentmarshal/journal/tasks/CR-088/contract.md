+++
schema = 1
id = "CR-088"
title = "Contract header schema 2: decisions, documents and extensions reach brief and the reviewer"
scope = [
  "src/agentmarshal/journal/contracts.py",
  "src/agentmarshal/journal/extensions.py",
  "src/agentmarshal/journal/open_task.py",
  "src/agentmarshal/journal/brief.py",
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/cli.py",
  "tests/test_journal.py",
  "tests/test_brief.py",
  "tests/test_review_launcher.py",
  "tests/test_extensions.py",
  "docs/overview.md",
  "docs/quickstart.md",
  "UPGRADING.md",
]
acceptance = [
  "a contract header may carry `decisions`, `documents` and `extensions` as arrays of strings; a header that carries any of them declares `schema = 2`; the parser accepts schema 1 and schema 2, and refuses a schema-1 header carrying one of the new fields with a message that names the field and the schema it needs",
  "a header without the new fields, at schema 1 or 2, parses to the same header values as today, and `open` keeps writing schema-1 contracts",
  "`documents` entries, and a manifest's `footprint`, `documents` and `artifacts` entries, are validated to the scope syntax — an exact path, or a directory prefix ending in a slash; an entry containing `*`, `?` or `[`, or starting with `/`, is refused with a message that says which entry and why",
  "one function reads a manifest at `.agentmarshal/extensions/<name>.toml`, returns its fields, and refuses a manifest whose `documents` or `artifacts` entry is not under one of its `footprint` entries, naming the entry",
  "`brief` appends, after the contract body, one section per named decision holding the text of `docs/adr/<id>-*.md`, and one section per file under the named documents (the contract's, plus each named extension's from its manifest), each introduced by its path; a decision or documents path that resolves to nothing is reported in the brief as missing, not skipped",
  "the review prompt lists the named decisions and documents by identifier and path and says a finding may cite a contradiction with a named decision; a contract that names none of the fields produces the prompt written today, character for character",
  "`open` prints a warning when a scope entry lies under `docs/adr/`, saying that the contract should name in `decisions` the decisions the task serves once written; it prints no such warning for other scopes",
  "docs/overview.md and docs/quickstart.md describe the three fields in a sentence each where the contract header is described today; UPGRADING gains a 0.3.0 → 0.4.0 section whose first entry names the header schema change and states that 0.3.0 refuses a schema-2 contract",
  "the existing gate and placement tests pass with their expected transcripts unmodified",
]
+++

# CR-088: contract header schema 2

## Context

ADR-0010 decides that a third-party process tool enters the lifecycle through
a declared manifest, and that a contract may name the decisions it serves, the
documents that must reach the implementer, and the extensions whose footprint
and documents join the task. This task builds the reading side of that
decision: the header fields, the manifest reader with its invariants, and the
two places the named material must reach — the implementer's brief and the
reviewer's prompt. The gate's lines (effective scope, the documents check, the
removal check) are the next task, so that this one changes no transcript.

The same discussion produced the `decisions` field for a second reason:
contracts have been checked against code and never against the ADRs they
implement, and decisions were re-argued in review rounds because nothing put
them in front of the implementer or the reviewer. Naming them is the cheapest
repair; enforcing them is not this task's.

## Objective

Make a contract able to name decisions, documents and extensions; read a
manifest safely; and put the named material into `brief` and the review
prompt — while a contract that names none of it behaves, parses and briefs as
in 0.3.0.

## Acceptance Criteria

As in the header, with these clarifications:

- Schema 2 is declared by content, as record schemas are (ADR-0009): a header
  carrying one of the new fields needs `schema = 2`; a header without them may
  say 1 or 2 and means the same thing. 0.3.0 refuses `schema = 2` with its
  existing unknown-schema message, which is the intended, loud failure.
- "Under a footprint entry" follows the scope matcher: an exact path equals
  an entry, or lies under an entry that ends in `/`.
- The brief's added sections come after everything the brief prints today;
  the existing brief tests keep their expectations for the existing text.
- The `open` warning is the same kind of line as the existing scope warnings
  and goes to the same stream.

## Threat model and boundaries

A contract that names a manifest it does not control could try to widen its
own inputs; this task reads manifests only from the working tree for `brief`
(context, not authority) and leaves every enforcing read to the gate task,
where the base-side rule of ADR-0010 D2 applies. The invariant that documents
and artifacts lie under the footprint is checked at read time so the gate
task never sees a manifest that makes a contract unlandable.

A brief that inlines large documents can flood the implementer's context.
This release imposes no cap and says so in the brief's documentation string;
the size question is for the dogfood to answer.

## Non-Goals

- Any gate change: effective scope from `extensions`, the documents line, the
  removal check — all the next task. This task's diff-lane transcripts are
  unchanged, and the last criterion holds it to that.
- `extension add` / `extension remove` commands, templates for any tool, and
  any execution of a manifest's `install` or `remove` strings.
- Verifying at `open` that a named decision file exists; `brief` reports a
  missing one, which is enough for this release.
- Deciding how the reviewer weighs a named decision against the contract; the
  prompt says a finding may cite one, and that is the whole of it.
- A size cap or summarisation for documents in the brief.
