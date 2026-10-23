## Context

`run_gate` in `src/agentmarshal/journal/gate.py` reads the contract from
the trusted side — the merge-base tree in the embedded placement, the
sidecar's working tree in the other — and already runs one independence
check: the latest review's `reviewer.email` must differ from the
candidate's declared authors and committers over `merge-base..candidate`.
CR-147 parsed `independence` (ADR-0022 section 5's vocabulary) into
`ContractHeader.independence`; this change makes the gate read it.

## Goals

- A schema-3 contract that declares `independence` gets each declared rule
  other than `reviewer-not-writer` judged at the merge boundary — one
  transcript line per rule, in the declared order.
- A rule that fails refuses the candidate and names the rule and the two
  compared values; a rule that cannot be judged reads `NOT CHECKED`
  (ADR-0022 section 5) and under `--without-review` reads `NOT EXAMINED`,
  as the existing review-bound lines do.
- Every contract without `independence` — every schema-1 and schema-2
  contract — produces today's transcript byte for byte; the pinned fixtures
  demonstrate it.

## Non-Goals

- Membership of reviewer and implementer in the contract's `reviewers` and
  `implementers` lists — a later task with an open question (what to do
  when the review names no actor).
- Verifying that a session's recorded vendor, model or actor is true — the
  guarantee stays "declared and cross-checked" (ADR-0018 decision 3).
- `status` showing the declared assignment next to what ran.

## Decisions

- **The contract is read exactly as today.** `independence` comes from the
  `ContractHeader` the gate already parses from the trusted side — the
  merge-base tree, or the sidecar working tree — so a contract without the
  field parses `()` and the new code adds no line.
- **The candidate's commits are enumerated as the writers' are.** A new
  helper lists the full commit ids of `merge-base..candidate` — the same
  range `_range_emails` enumerates — and a session record of the task is an
  implementer session for these rules exactly when its `commit` names one
  of those commits: `commit` is the field recording "the commit the
  implementer run produced" (session-activity specification).
- **The rules judge the latest review of the candidate's commit.** That is
  the record the review check already selects; a review bound to another
  commit is not judged, and a non-approving latest review is still judged —
  the rules describe independence, not the verdict.
- **Vendor and model compare by exact equality after casefold.** The values
  are labels the writers chose, so the normalisation is the identity
  check's own — strip and casefold — and casing cannot evade the rule.
- **`distinct-actor` requires both actors declared.** The actors table is
  read from the trusted side (the merge-base tree, or the sidecar's working
  file), and an actor is a key of its `actors` section — the test
  `reviewer_actor_note` runs at submit time. A session whose `actor` is no
  key of the table, and a review whose `reviewer.actor` is none, leave the
  rule `NOT CHECKED`: an actor is a declared label, and a pass or fail over
  a label no table vouches for would be a claim the journal cannot stand
  behind (ADR-0006, ADR-0022 section 3).
- **Whatever is absent reads `NOT CHECKED`, and a demonstrated failure
  outranks it.** No in-range implementer session, a missing
  `reviewer.actor`/`vendor`/`model`, a missing `usage.provider`/`model`
  on a session — each is a `NOT CHECKED` naming the reason, never a pass
  over nothing and never a refusal for what could not be seen. When one
  session fails the comparison while another could not be judged, the rule
  fails: reporting a demonstrated violation is no overclaim.
- **`--without-review` reports `NOT EXAMINED`.** The declared rules are
  review-bound: with no review record the run prints each rule's
  `NOT EXAMINED` line beside the two existing ones, and a candidate that
  carries a review is judged by it however the run was asked.
- **`reviewer-not-writer` stays one line.** The existing check runs for
  every candidate as today; the header naming it is consumed by the skip in
  the rule loop, so no second line appears.
- **Every value a line prints is escaped as the gate's other lines are** —
  the transcript line goes through the same `say` escaping, so a
  record-carried character can neither add a line nor reorder one.
