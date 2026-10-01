# 033 — Reviewing the contract before implementation does not pay off: a measured withdrawal

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:46fcb32756b8597a687760e1fc23f4f4424d582034d32bf2cca87c17552df136` · **Disposition:** accepted *(it is the reporter's own measured withdrawal of proposal 031's third suggestion)*

## Finding

The reporter's earlier file — published here as
[proposal 031](031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md)
— made three suggestions. The third was that the reviewer could
optionally be pointed at the contract before implementation, which that
file called the cheapest of the three to try and the only one that would
have caught its motivating case before a round was spent. The reporter
tried it, measured it, and withdraws that part. The first two suggestions
— pin the contract hash where it is written, and a record for agreement —
are not affected.

What the reporter built: a launcher that ran the same model reviewer
against the contract text with a checklist — statements about the code
verified against the repository; criteria checkable in the implementer's
environment; no contradictions between criteria and existing commands,
tests and documents; scope covering what the criteria require; every "do
not change X" stated as a criterion; for schema changes, the affected
tables and a no-data-loss requirement. Opening a task and every amendment
required an approving verdict on the current contract hash; an override
needed a recorded reason.

Measurements, as reported — first and only application, to one task
contract of nine criteria across five subsystems:

| pass | verdict | blocking findings | cost | reviewer time |
|---|---|---|---|---|
| 1 | changes_required | 2 | $3.89 | 32.5 min |
| 2 | changes_required | 4 | $3.73 | 10.2 min |
| 3 | changes_required | 2 | $4.46 | 10.9 min |
| 4 | approved | 0 | $3.53 | 8.6 min |
| 5 | changes_required | 1 | $3.51 | 11.7 min |
| 6 | changes_required | 3 | $3.87 | 10.1 min |
| 7 | changes_required | 1 | $4.03 | 10.4 min |
| total | | 13 blocking, 65 advisory | **$27.02** | **~95 min** |

Pass 5 came after the coordinator edited the approved text once more and
lost the approval. The task never reached an implementer; the operator
stopped the experiment after pass 7 and removed the mechanism.

For comparison, the complete candidate-review cycle — all rounds — of the
six tasks the reporter completed the same day cost $1.55, $6.30, $7.50,
$8.07, $8.13 and $18.24, the last a data migration with two returns.
Reviewing one contract cost more than reviewing any of those
implementations, and delivered nothing.

What the passes found was not worthless, the reporter notes: a
stage-verification script the change would have broken; an integration
test placed on a database another test recreates; a missing prohibition
on publishing draft data; a menu address the coordinator had changed
against a recorded operator decision. All four are factual — about the
code, the data or recorded decisions — as were the six specification
defects that motivated the earlier file.

The reporter's diagnosis of why it cannot pay off: the implementation is
checked against the contract; the contract has nothing to be checked
against. There is no reference text that defines a correct contract, so
the review has no stopping point — each pass finds a smaller ambiguity,
each fix adds text and new seams, and the approved state is one edit away
from being lost. Two goals compete — "do the right thing" and "say it so
precisely that the right thing gets done" — and the second consumes the
first.

What the reporter suggests be kept instead is narrower: the two
journal-level suggestions of the earlier file stand; if anything is
checked before implementation it should be facts, not prose quality —
statements about code and data with a definite answer, and consistency
with recorded decisions, one pass, advisory, no gate; and the rest of the
defect class is cheaper caught downstream, by the candidate review and by
giving the implementer the checks the coordinator's environment lacks.

## Proposed

- Amend the disposition of the earlier file's third suggestion with this
  data, so another adopter does not repeat the experiment as a gate.
- Keep its first two suggestions open.

## Disposition — the withdrawal is recorded

This file asks for no mechanism; it retracts one. The suggestion's fate
is therefore not a disposition of ours but the reporter's: they built it,
measured it, and took it back, and the measurements above travel with the
retraction so the next adopter does not have to rerun the experiment.
Proposal 031 names this digest where it speaks of the withdrawn
suggestion; its first two suggestions keep the dispositions stated there.

The narrower observation the reporter leaves — that a pre-implementation
check worth having looks at facts with definite answers, once, advisory —
is recorded here with them, as guidance rather than as an ask.

## Where

Nothing to ship: the file is a retraction. Proposal 031 names this digest
where it refers to the withdrawal.
