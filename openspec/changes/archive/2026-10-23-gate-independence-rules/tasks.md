## 1. The gate

- [x] 1.1 `run_gate` enumerates the candidate range's commit ids as
  `_range_emails` enumerates its writers (`merge-base..candidate`) and
  selects the task's implementer sessions — session records whose `commit`
  is one of them — verify: a session outside the range is not judged.
- [x] 1.2 Each declared rule other than `reviewer-not-writer` prints one
  line in the declared order, judging the latest review of the candidate's
  commit: `distinct-vendor` compares `reviewer.vendor` with each session's
  `usage.provider`, `distinct-model` `reviewer.model` with `model`, and
  `distinct-actor` `reviewer.actor` with `actor` where the actor is a key
  of the project's actors table read from the trusted side — verify: one
  test per rule's pass and fail, and per the ordering.
- [x] 1.3 A rule holds only against every in-range session; a failing rule
  refuses the candidate naming the rule and the two compared values, and
  every value from a record is escaped as the other lines are — verify:
  the multi-session and escaping tests.
- [x] 1.4 A rule that cannot be judged — no implementer session in range, a
  compared field absent on the review or a session, an undeclared actor —
  reads `NOT CHECKED` with the reason and neither refuses nor passes —
  verify: one test per cause.
- [x] 1.5 Under `--without-review` with no review record the rule lines
  read `NOT EXAMINED`; with a review they are judged — verify: both tests.
- [x] 1.6 `reviewer-not-writer` stays its single existing line whether or
  not the header names it, and a contract without `independence` produces
  today's transcript byte for byte — verify: the header-declared test and
  the pinned fixtures unchanged.

## 2. The change itself

- [x] 2.1 proposal.md, design.md, tasks.md and the contract-governance
  delta are written — verify: `openspec validate gate-independence-rules
  --strict`.
- [x] 2.2 Every scenario in the delta is demonstrated by a test whose
  docstring names it — verify: grep the test docstrings against the spec's
  scenario headings.
- [x] 2.3 The change is archived with the archive command — verify: the
  delta's requirements land in
  `openspec/specs/contract-governance/spec.md` and the change lives under
  `openspec/changes/archive/`.
