## 1. The gate

- [x] 1.1 `run_gate` selects the in-range implementer sessions once — the
  session records whose `commit` is one of the candidate's
  `merge-base..candidate` commits — whenever the declared rules or the
  declared `implementers` need them — verify: a session outside the range
  is judged by neither check.
- [x] 1.2 A contract declaring `reviewers` prints one line judging the
  latest review's `reviewer.actor` against the list by exact string
  equality — `PASS` in it, `FAIL` naming the actor and the list outside
  it, `FAIL` saying the review is recorded with `--actor` when the review
  carries none — and `NOT EXAMINED` beside the other review-bound lines
  under `--without-review` with no review record — verify: one test per
  line form.
- [x] 1.3 A contract declaring `implementers` prints one line judging
  every in-range implementer session's `actor` against the list by exact
  string equality, with no review needed — `PASS` when all are in it,
  `FAIL` naming each that is not, `NOT CHECKED` with the reason when no
  implementer session carries a commit in the range — verify: one test
  per line form, the multi-offender naming, and the judged-without-a-
  review run.
- [x] 1.4 `distinct-actor` compares actor ids by exact string equality —
  `status`'s comparison — while `distinct-vendor` and `distinct-model`
  keep the strip-and-casefold normalisation — verify: the exact-equality
  test alongside the case-normalisation one.
- [x] 1.5 Every value a membership line prints is escaped as the gate's
  other lines are, and a contract declaring neither list produces today's
  transcript byte for byte — verify: the escaping test and the pinned
  fixtures unchanged.

## 2. The change itself

- [x] 2.1 proposal.md, design.md, tasks.md and the contract-governance
  delta are written — verify: `openspec validate
  gate-assignment-membership --strict`.
- [x] 2.2 Every scenario in the delta is demonstrated by a test whose
  docstring names it — verify: grep the test docstrings against the
  spec's scenario headings.
- [x] 2.3 The change is archived with the archive command — verify: the
  delta's requirements land in
  `openspec/specs/contract-governance/spec.md` and the change lives under
  `openspec/changes/archive/`.
