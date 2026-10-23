## Context

`run_gate` in `src/agentmarshal/journal/gate.py` reads the contract from
the trusted side — the merge-base tree in the embedded placement, the
sidecar's working tree in the other — and already runs, beside the
verdict check, the declared-identity check and the independence rules
CR-186 added: one line per declared rule other than `reviewer-not-writer`,
judging the latest review of the candidate's commit against the task's
in-range implementer sessions — the session records whose `commit` is one
of the candidate's `merge-base..candidate` commits. CR-191's `status`
section shows the declared `implementers` and `reviewers` next to what
ran, marking a ran actor outside its role's list — by exact string
equality. Nothing yet refuses an undeclared actor at the merge boundary.

## Goals

- A contract declaring `reviewers` gets the latest review's
  `reviewer.actor` checked against the list — `PASS` inside it, `FAIL`
  outside it, and `FAIL` when the review carries no actor, the operator
  decision of 2026-10-23: membership is what the contract claims, and
  without an actor it cannot be shown; `review --actor` (CR-182) is the
  path.
- A contract declaring `implementers` gets every in-range implementer
  session's `actor` checked against the list — `PASS` when all are in it,
  `FAIL` naming each that is not, `NOT CHECKED` with the reason when no
  implementer session carries a commit in the range: a provider's CI run
  can hold no session yet, and the line is neither a refusal nor a pass.
- `distinct-actor` compares actor ids by exact string equality, as
  `status` does — the case-folded comparison CR-186 gave it equated two
  declared actor ids differing only in case.
- A contract declaring neither list produces today's transcript byte for
  byte; the pinned default transcript and fixtures demonstrate it.

## Non-Goals

- Checking the fallback order of the lists or why a run fell back to a
  later entry — the reason is shown, not verified (ADR-0018 decision 3).
- Verifying that an actor label is who it claims to be — declared labels
  until signing (ADR-0006).
- Requiring `reviewers` or `implementers` in a header, and any change to
  `status`, `review` or the record model — the fields and the display
  exist already.

## Decisions

- **The contract is read exactly as today.** `implementers` and
  `reviewers` come from the `ContractHeader` the gate already parses from
  the trusted side, so a contract without them parses `()` and the new
  code adds no line.
- **The reviewers check judges the review the verdict check judges.** The
  latest review of the candidate's commit, whatever its verdict — the
  declared rules already judge that same record, and membership is a
  property of who reviewed, not of how the verdict came out.
- **A review carrying no `reviewer.actor` is a refusal, not a "not
  checked".** ADR-0022 section 5's "not checked" is for a field a rule
  needs being absent on evidence that exists; membership here is the
  claim the contract itself makes, and the operator's decision of
  2026-10-23 is that an actor-less review cannot show it — the gate
  refuses and says the review is recorded with `--actor`.
- **The reviewers check is review-bound; the implementers check is not.**
  With `review_required` false and no review record the reviewers line
  reads `NOT EXAMINED` beside the other review-bound lines, and a run
  refused for want of a review prints no second refusal. The implementers
  line judges with no review at all — the sessions are the candidate's,
  not the review's — so a provider's CI run gets `NOT CHECKED` or a
  verdict on the sessions it holds.
- **Membership is exact string equality, as `status` compares.** Actor
  ids are exact labels — the actors table keys them exactly — so `in`
  against the declared tuple, no strip and no casefold: an actor
  differing from every declared entry only in case or surrounding
  whitespace is not a member.
- **`distinct-actor` gets the same exact comparison.** The casefold
  normalisation stays for `distinct-vendor` and `distinct-model`, whose
  values are freer strings a casing change must not evade; two actor ids
  differing only in case are two declared actors.
- **One session set serves both checks.** The in-range implementer
  sessions the rules judge and the ones membership judges are the same
  selection — computed once when either the rules or the declared
  `implementers` need it, and the `NOT CHECKED` reason is the one the
  rules already print.
- **Every value a line prints is escaped as the gate's other lines are**
  — the transcript line goes through the same `say`/`check` escaping, so
  a record- or contract-carried character can neither add a line nor
  reorder one.
