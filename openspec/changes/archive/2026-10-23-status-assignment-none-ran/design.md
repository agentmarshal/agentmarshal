## Context

`_assignment_lines` in `status_view.py` builds the assignment section:
three declaration lines — `implementers`, `reviewers`, `independence` —
then the ran lines, one per implementer session and one per review,
each group in the order the records stand. An undeclared field prints
`(not declared)`; an absent value inside a ran line prints `(absent)`.
But when a declared list's ran side is empty — the contract names
implementers and no implementer session is recorded — the side prints
nothing: the declaration stands, then `Records:`. CR-191's review filed
it as advisory finding A1-ran-side-silent-when-nothing-ran: the silence
contradicts the section's own rule — an absence is stated, not omitted
— and the scope block, which prints `- (none)` for an empty scope.

## Goals

- A declared list whose ran side is empty says so, in the scope
  section's `(none)` wording.
- A `(none)` line stands where its group's lines would: the sessions'
  before the review lines'.
- Everything else `status` prints stays byte for byte.

## Non-Goals

- Any other change to the assignment section or to `status`.
- Membership enforcement — the gate's job, unchanged.
- A `(none)` line for a side whose list the header does not declare:
  `(not declared)` already says there is no assignment to answer.

## Decisions

- **The lines read `- implementer sessions: (none)` and
  `- reviews: (none)`.** The section's lines are `- <what>: <value>` —
  `- implementers: devin, codex`, `- reviewers: (not declared)` — and
  the ran side keeps that shape: the plural name points at the group
  the line replaces, and `(none)` is the mark the scope block already
  prints for an empty list. Two bare `- (none)` lines, one per side,
  would be indistinguishable.
- **The `(none)` line answers a declared list.** What ran is shown
  whether or not the contract declares the role — a session prints
  unmarked when `implementers` is undeclared, and its absence is
  likewise shown only against a declaration: an undeclared side's ran
  lines print when records exist, and when none do the declaration
  line's `(not declared)` is the whole answer — a `(none)` there would
  answer an assignment never made.
- **A `(none)` line occupies its group's place.** Session lines group
  before review lines whatever the record order; an empty side's line
  takes the position its group's lines would, so the section's ran
  half always reads sessions-then-reviews.
- **Every section line is still escaped whole at print.** The `(none)`
  lines are constant — nothing they carry comes from a record or the
  contract — and they go through `escape_for_display` with the rest
  (ADR-0015 decision 5).

## Migration

None — the change is display-side only. A schema-1 or schema-2 contract
cannot carry the fields and keeps the same view; a schema-3 contract
declaring none of the three keeps it byte for byte.

## Risks

- [Two empty ran sides could print ambiguous identical lines] → each
  names its side; the scope block's bare mark was refused for exactly
  that ambiguity.
- [A session under another `role` triggers the line although a session
  exists] → intended: the filter stays `role` is `implementer`, the
  convention `record-session` documents; the session still renders its
  record line below, where it always stood.
