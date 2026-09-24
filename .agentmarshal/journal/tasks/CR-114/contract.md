+++
schema = 2
id = "CR-114"
title = "The forgeable-text rule refuses only what can break a line or reorder text"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/contracts.py",
  "src/agentmarshal/journal/validate.py",
  "tests/",
  "UPGRADING.md",
  "openspec/changes/narrow-the-forgeable-text-rule/",
  "openspec/changes/archive/",
  "openspec/specs/record-text-safety/",
]
acceptance = [
  "every scenario in the change's delta spec is demonstrated by a test whose docstring names it; the implementation follows design.md's decisions or records in design.md why it departed",
  "the rule refuses exactly the characters that can add a line, reorder text, or fail to encode — Unicode categories Cc, Cs, Zl and Zp, and the bidirectional marks, embeddings, overrides and isolates U+061C, U+200E, U+200F, U+202A-U+202E and U+2066-U+2069 — and accepts every other character, including the space separators U+00A0, U+2007, U+2009 and U+202F and private-use codepoints; one predicate decides this for every place that asks, and none of them reads str.isprintable()",
  "a journal whose review record carries a finding id containing U+202F validates, and a test pins that case with a record written under schema 2 by an earlier release, as an adopter's journal has it",
  "the purpose the rule exists for still holds: a value carrying a newline, a carriage return, U+2028, U+2029 or a bidirectional override is refused wherever it was refused before, with a test per class, and the refusal message still names the field",
  "UPGRADING.md tells an adopter whose 0.4.0 validate refused a historical review record what to do, and names no mechanism that does not exist",
  "no record is rewritten, no allowlist is introduced, and the full CI sequence passes",
]
decisions = ["ADR-0004", "ADR-0007"]
documents = ["openspec/specs/record-text-safety/"]
+++

# CR-114: the forgeable-text rule refuses only what can break a line

## Context

An adopter on a pinned 0.3.0 ran 0.4.0's `validate` over its journal before
upgrading, read-only, and it refused two review records that 0.3.0 accepts:
`review record finding id must not contain control characters`. Upstream
reproduced it the same day on that journal with the published 0.4.0 — exit 1,
the same two records.

The character is U+202F NARROW NO-BREAK SPACE, eleven occurrences across three
records written by 0.1.0, inside finding ids whose text is a sentence and uses
it as a thousands separator. `str.isprintable()` is false for every `Zs`
separator except U+0020, so the rule refuses it. None of those separators can
end a line, which is what the rule exists to prevent (a value must not be able
to add a line to generated text, including one that reads as an approval).

The check itself is older than 0.4.0; what 0.4.0 changed (CR-086) is that it
now applies to review `findings` and `advisory_findings`, not only to
acceptance finding ids. Record validation runs on read, so the stricter rule
reached records an earlier release had already accepted and the gate will not
let anyone change: both tasks are closed, and the journal is append-only.
For that adopter the upgrade is blocked, because whole-journal `validate` runs
in their CI and their merge wrapper reproduces that job.

## Objective

The rule refuses what can forge a line or hide text, and nothing else, so a
journal that was valid stays valid.

## Acceptance Criteria

As in the header. The scenarios in the delta spec are the behaviour;
design.md holds the decisions, including which categories are refused and why
the bidirectional controls are in that set.

## Amended 2026-09-24 (the refused set)

The set in criterion 2 is Cc, Cs, Zl, Zp and every bidirectional mark,
embedding, override and isolate. Two classes joined it during the work, both
found by review: an unpaired surrogate, which cannot be encoded as UTF-8 at all,
so a record carrying one could not be written back out; and the bidirectional
marks U+061C, U+200E and U+200F, which reorder displayed text as the overrides
do. The first criterion let the implementation depart from design.md, not from
the contract, so the contract says it here.

## Amended 2026-09-24 (scope)

`src/agentmarshal/journal/validate.py` joins the scope. The same printability
test guards a review artifact's `ref` there, for the same stated purpose — a ref
that could add a line to the failure output — and on the read side, where the
retroactivity this task is about applies. Two narrowed copies and one left
stricter would be the drift the task exists to remove.

## Amended 2026-09-24

The delta spec goes to a new capability, `record-text-safety`, not to
`record-lifecycle`. That capability's Purpose is which records a closed task
admits; what a record's text may contain is a different question, and naming it
there would mislabel both.

## Non-Goals

- **Rules scoped to the schema that introduced them.** The adopter also asks
  that a new validation rule never apply to records written before it. That is
  the right principle and a larger decision — it needs a record-level rule
  about which schema's rules a reader applies — and it is not what unblocks
  them today. It gets its own decision record.
- An allowlist of accepted-as-is records in `project.json`.
- Escaping on display instead of refusing.
- Rewriting any record, or the release's version number and changelog: the
  release that carries this fix is its own task.
