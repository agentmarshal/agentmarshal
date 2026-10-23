## Why

ADR-0018 decision 3 lets a contract name its permitted implementers and
reviewers — ordered lists of declared actors — and have the gate check
membership: the review that makes a candidate mergeable comes from a
permitted reviewer, judged against the implementers whose commits the
candidate carries. CR-147 landed the schema-3 header that parses the
lists, CR-191 the `status` display of the assignment with exact actor
comparison, CR-186 the declared independence rules — and the lists remain
displayed but unchecked at the merge boundary. ADR-0022 section 5 says
"not checked" where a field a rule needs is absent, but did not settle
membership when a review names no actor. The operator decided on
2026-10-23: the gate refuses — membership is what the contract claims, and
without an actor it cannot be shown; `review --actor` (CR-182) is the
path.

## What Changes

The gate reads the trusted contract's `reviewers` and `implementers` and
prints one line per declared list. The reviewers line judges the latest
review of the candidate's commit — `PASS` when its `reviewer.actor` is in
the list, `FAIL` naming the actor and the list when it is not, and `FAIL`
saying the review is recorded with `--actor` when it carries none — and
reads `NOT EXAMINED` where the run judges without a review. The
implementers line judges the `actor` of every implementer session whose
`commit` is in the candidate's range — `PASS` when all are in the list,
`FAIL` naming each that is not, and `NOT CHECKED` with the reason when no
implementer session carries a commit in the range. Both comparisons are
exact string equality, as `status` compares since CR-191 — and
`distinct-actor` switches to the same exact comparison, the case-folded
one CR-186 gave it equating two actor ids that differ only in case. A
contract declaring neither list produces today's transcript byte for
byte.

## Capabilities

- modified: `contract-governance`

## Impact

`src/agentmarshal/journal/gate.py` gains the two membership checks beside
the declared-rules block; `parse_contract_text`, the record model and
`status` already carry everything the checks read.
