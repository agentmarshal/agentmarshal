## Context

`status_view.py`'s `print_task_detail` prints the task's header lines,
the acceptance trail, the scope block, then one line per record through
the renderer registry, then the agreement and drift notices.
`task.contract` already parses the schema-3 fields — `implementers`,
`reviewers`, `independence` — and the records already carry what ran: a
session's `actor`, `model`, `usage.provider` and `fallback_reason`, a
review's `reviewer.actor`, `reviewer.vendor` and `reviewer.model`.
ADR-0018 decision 3 pairs the declaration with the facts: `status` shows
the declared assignment next to what actually ran, and the reason for a
fallback is shown, not verified.

## Goals

- A contract declaring any of the three fields gets an assignment
  section naming the declared lists in their order and the declared
  rules — `reviewer-not-writer` named as always checked by the gate
  when the header does not name it — a field the header does not
  declare shown as not declared.
- The same section shows what ran: each implementer session's actor,
  vendor from `usage.provider`, model and `fallback_reason` when the
  record carries one; each review's reviewer actor, vendor and model —
  an absent value shown as absent, never derived.
- An actor that ran outside the declared list is marked not declared for
  the role, and only when the contract declares that role's list.
- A contract declaring none of the three keeps today's view byte for
  byte.

## Non-Goals

- Membership enforcement in the gate — a later task, after an operator
  decision.
- Judging the independence rules in `status` — the gate judges them;
  `status` shows the facts.
- Verifying what the records claim — the guarantee stays "declared and
  cross-checked" (ADR-0018 decision 3).

## Decisions

- **The section sits between the scope block and the record lines.** The
  assignment is contract-declared like the scope; placing it there keeps
  the declarations together and leaves `Records:` adjacent to the
  evidence it lists. The trailing notices — agreement, drift — stay
  last.
- **An implementer session is a session record whose `role` is
  `implementer`.** The contract's `implementers` names actors for the
  implementer role and a session's `role` — the `record-session --role`
  worker role — is the same word, so the role, not the activity or the
  commit, decides; a coordination or review-cost session is not
  implementer work. The gate's definition — a `commit` in the
  candidate's range — has no analog in `status`, which reads no
  candidate.
- **Every review record is a review that ran.** There is no role
  question on the review side: the record attests the review, and its
  `reviewer.actor`, `vendor` and `model` are what ran.
- **Absent is shown, never derived.** A missing `usage.provider`,
  `model`, `actor` or `reviewer.actor` prints `(absent)`; the vendor is
  `usage.provider` or absent — never guessed from an actor string like
  `openai/gpt-5`. `fallback_reason` prints only when the record carries
  it: the decision shows the reason for a fallback, and a run with none
  recorded claims none.
- **The mark needs a declared list.** `(not declared for the role)`
  ends a ran line whose actor is outside the contract's list for that
  role — `implementers` for a session, `reviewers` for a review — the
  membership check exact string equality: actor ids are exact labels —
  the actors table keys them exactly — so an actor differing from every
  declared entry only in case or surrounding whitespace is not declared.
  No declared list, no mark; an absent actor shows `(absent)` and no
  mark — there is no name to check against the list.
- **The independence line states the rules in force.** The declared
  rules print in their order; `reviewer-not-writer` runs for every
  candidate whether or not the header names it — the header naming it
  adds no second gate line — so where the header did not name it the
  line adds `reviewer-not-writer (always checked by the gate)`. A
  header declaring no `independence` still says `(not declared)`.
- **An undeclared field says so.** A contract declaring `implementers`
  but not `reviewers` shows `reviewers: (not declared)` — the absence is
  stated rather than omitted, the same honesty the agreement line buys
  by existing.
- **Each section line is escaped whole at print.** The lines are built
  raw and each goes through `escape_for_display`, like every rendered
  line — a contract entry or a record field carrying a refused character
  can neither add a line nor reorder one (ADR-0015 decision 5).

## Migration

None — the change is display-side only. A schema-1 or schema-2 contract
cannot carry the fields and keeps the same view; a schema-3 contract
declaring none keeps it byte for byte.

## Risks

- [A hostile or malformed record reaches the section] → the lines are
  escaped like every rendered line, and the byte pin in
  `test_status_assignment.py` demonstrates refused characters staying on
  their line.
- [`role` is free text, so an implementer could record under another
  word] → the section's filter is named plainly: `role` is
  `implementer`, the convention `record-session` documents and the
  harness writes; a session under another role shows as no implementer
  session rather than a wrong one.
- [An absent `reviewer.actor` could read as an undeclared reviewer] →
  the line shows `actor=(absent)` and no mark: absence is stated, and
  the mark needs a name to check against the list.
