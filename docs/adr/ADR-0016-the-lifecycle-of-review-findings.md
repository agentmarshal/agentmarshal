# ADR-0016: The lifecycle of review findings

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0004](ADR-0004-journal-data-model.md) (evidence is
append-only records; a writer stamps the minimum schema a record needs),
[ADR-0007](ADR-0007-operator-acceptance.md) (the gate decides on the
verdict or on an acceptance covering exactly the blocking findings, and
advisory findings are neither required nor permitted there) and
[ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)
(a new record field or value arrives under the schema that introduces
it). **It adds to ADR-0007 and revises the
[gate-lanes](../../openspec/specs/gate-lanes/spec.md) specification**:
the gate's default output gains a line, and that specification pins the
default transcript byte for byte. It answers
[proposal 027](../proposals/027-advisory-findings-have-no-lifecycle.md),
[proposal 039](../proposals/039-review-findings-do-not-feed-back-into-the-next-round.md)
and the second finding of
[proposal 026](../proposals/026-reviewer-facts-round-convergence-and-two-gaps.md).

This ADR records a decision. The record fields, command behaviour, gate
line and report view it describes are **not implemented by this
document**; they follow in their own tasks. The present tense below is
how a decision is written, not a claim about shipped behaviour.

## Context

A review record carries two finding lists — `findings`, the blocking
ones, and `advisory_findings` — and both are ids the reviewer invents
(`records.py`). The gate decides on the verdict, or, where the latest
review does not approve, on an acceptance that names exactly the blocking
list ([ADR-0007](ADR-0007-operator-acceptance.md), `gate.py`); neither
path reads the advisory list. `status` prints each review with its
verdict and the two counts — `verdict=… findings=N advisory=N`
(`cli.py`) — so an advisory is visible but **decides nothing**, and
ADR-0007 says in terms that shipping over an advisory overrides nothing.
`report` counts reviews and does not aggregate findings (`report.py`).
Nothing links one review of a task to the next, and nothing counts a
task's `changes_required` verdicts.

Three proposals press on this, each with measurements:

- [proposal 027](../proposals/027-advisory-findings-have-no-lifecycle.md):
  `approved` quietly absorbs known defects — across the reporter's last
  ten tasks, 18 approved reviews carried 55 advisory findings, and seven
  implementation rounds ran after an approval because a person judged an
  advisory to be a real defect;
- [proposal 026](../proposals/026-reviewer-facts-round-convergence-and-two-gaps.md),
  second finding: rounds do not converge — a review ran eight rounds on a
  document unchanged after the first, and rounds kept producing findings
  on lines that had existed since round one;
- [proposal 039](../proposals/039-review-findings-do-not-feed-back-into-the-next-round.md):
  findings do not feed back — repeat rounds are the reporter's largest
  single cost, the same classes of finding recur across tasks, and for
  edge-case tasks the reviewer names one new instance of a covered class
  per round.

## Decision

### 1. An advisory finding gets a disposition at `complete`

For the review the gate passed on — an approving review, or the
non-approving review an acceptance covered — `complete` takes a
disposition for each of that review's advisory findings:

- `fixed`;
- `deferred`, with a reason, and optionally naming a follow-up task;
- `rejected`, with a reason. There is no separate `not-a-defect`: a
  finding that is not a defect is rejected, and the reason says why.

`complete` runs the gate itself today and writes the `completed` record
only when the gate passes; the new check sits in `complete` itself, which
refuses **before** writing `completed` when any advisory finding of that
review lacks a disposition. The refusal lands at write time — the point
where the coordinator can still supply the answers. The dispositions are
recorded in the `completed` record.

What is required is that a disposition exists, not which one it is. This
**adds to
[ADR-0007](ADR-0007-operator-acceptance.md)** and says so: an advisory
finding still blocks nothing, and shipping past one still overrides
nothing — but silence is replaced by a recorded choice. `status` and
`report` show the deferrals still open. The findings lane — the task lane
of [ADR-0009](ADR-0009-research-findings-lifecycle.md) — is untouched.

### 2. Reviews of one task link in order

A review launched by the `review` command records the previous review of
the same task, so a task's reviews form a chain a reader can walk.

Whether the reviewer is **shown** the previous round's findings is a
mode, **off by default**; turning it on waits on a measurement of what it
does to review quality. There is no automatic matching of findings by id:
a finding's status against the previous round is not computed.

### 3. Findings carry a class

A finding carries a class from the project's vocabulary — declared in
`project.json`, with the default `correctness`, `contract-mismatch`,
`claim-accuracy`, `scope`, `test-gap`, `security`, `style`.

A finding whose class is not in the vocabulary is recorded as `other`
with a warning — not refused: a verdict is the output of a paid review
run, refusing the record over a mistyped class would lose the run, and
the class is reference markup that no decision rests on.

`report --findings` shows the classes across tasks, with counts and
examples — the recurring-classes view the findings were already carrying
the data for.

### 4. The count of `changes_required` verdicts is shown

`status` shows the task's count of `changes_required` verdicts, and the
gate's output gains a line carrying the same count — flagged when the
count reaches the project's threshold (default 3). It blocks nothing: it
is the signal to stop and revisit the contract that a person today has
to notice unaided.

The new gate output line **revises the
[gate-lanes](../../openspec/specs/gate-lanes/spec.md) specification**,
whose default-run requirement pins today's transcript byte for byte.

### 5. A defect class can be closed by a principle — as documentation

Proposal 039's third ask — the principle criterion — is accepted as
**documentation**, not machinery. The contract guidance states the
pattern the reporter measured: an acceptance criterion may name a class
of defect as a principle covering the whole class and how the class is
closed, and a line of the review protocol asks that a new instance of an
already-covered class be reported as advisory unless the principle itself
is violated.

## Left open

- A curated base of worked defects, fed back to the implementer
  ([proposal 039](../proposals/039-review-findings-do-not-feed-back-into-the-next-round.md),
  items 2 and 6 — the self-check and the findings base). Delivery to the
  implementer already exists: a contract's named documents reach it
  ([ADR-0010](ADR-0010-process-extensions.md)). The coordinator keeps
  such a base by finding class; how it is collected stays open pending a
  measurement.
- `review --since`
  ([proposal 026](../proposals/026-reviewer-facts-round-convergence-and-two-gaps.md)) —
  still deferred, revisited if the round links of Decision 2 prove not to
  be enough.
- A plugin interface for lifecycle steps
  ([proposal 039](../proposals/039-review-findings-do-not-feed-back-into-the-next-round.md),
  item 7) — answered by the stages of
  [ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md);
  nothing here adds to it.

## Consequences

- An approval stops being a silence about known defects: every advisory
  lands as `fixed`, `deferred` or `rejected`, with a reason in the
  journal — and accepting a defect stays a cheap, legitimate decision,
  which is the point of requiring an answer rather than a fix.
- Deferrals stay visible after the task closes, in `status` and
  `report`, instead of dissolving into a review record nobody re-reads.
- A task's reviews become a chain; whether the reviewer should see the
  previous round is measured before the mode is on.
- A project gains a vocabulary for its recurring defects and a visible
  count of `changes_required` verdicts — neither blocks anything.
- The record fields this decision needs — the dispositions in
  `completed`, the previous-review link, the finding class — arrive under
  the schema that introduces them
  ([ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)),
  named by the later decision on the record model. This ADR decides what
  is recorded, not what the fields are called.

## Alternatives considered

**Make advisories blocking.** Refused — the reporter of
[proposal 027](../proposals/027-advisory-findings-have-no-lifecycle.md)
names it the wrong fix: a finding is blocking when it violates an
acceptance criterion, and many real defects do not. A disposition
requirement converts silence into a recorded choice without letting the
gate judge severity.

**A separate `not-a-defect` disposition.** Declined: `rejected` with a
reason already says it, and a fourth value would only split the
vocabulary.

**Block the merge at the `changes_required` threshold.** Refused: the
count is a signal to stop the loop and revisit the acceptance criteria —
the remedy its measurements point at — not a verdict the gate can make.
The threshold marks the count; a person reads it.

**Automatic matching of findings across rounds by id.** Not taken: the
review records link, and the decision automates no per-finding status
across the link.
