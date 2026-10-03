# ADR-0019: Accounting — time, quota resets and money

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0004](ADR-0004-journal-data-model.md) (evidence is
append-only records; a writer stamps the minimum schema a record needs),
[ADR-0005](ADR-0005-evidence-capture-and-format.md) (measurements are not
lifecycle — a session record is admitted after a terminal record; the
capture classes), [ADR-0014](ADR-0014-where-things-live.md) (raw
accounting belongs to the process log, which the gate never reads) and
[ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)
(a new record field or value arrives under the schema that introduces
it). It answers
[proposal 032](../proposals/032-the-journal-has-no-time-axis.md),
[proposal 024](../proposals/024-provider-quota-stop-cannot-be-recorded.md),
[proposal 018](../proposals/018-session-activity-vocabulary-and-cost.md),
[proposal 034](../proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md)
and the third finding of
[proposal 026](../proposals/026-reviewer-facts-round-convergence-and-two-gaps.md).

This ADR records a decision. The record fields, command behaviour and
report view it describes are **not implemented by this document**; they
follow in their own tasks. The present tense below is how a decision is
written, not a claim about shipped behaviour.

## Context

How it works today:

- a session record carries `role`, `actor`, `activity` (one of
  `implementation`, `review`, `other`, `coordination`), `outcome` — a
  required value checked only for non-emptiness — `tokens` (`input`,
  `output`, `cache`) and an optional `usage` block naming which provider
  the counts came from and whether they were `measured` or `reported`
  (`records.py`, `cli.py`);
- its only time is `created_at` — the moment the record is written
  (`create_session_record` sets it to now), and a session is deliberately
  accepted in any task state because what a task consumed is known when
  the task ends (`session.py`, [ADR-0005](ADR-0005-evidence-capture-and-format.md)
  Decision 3): sessions are often written after completion, so
  `created_at` marks the end of a run, never its span;
- `report` prints `reviews=` and `tokens=` per task and in the summary —
  nothing about time or money (`report.py`);
- `provider-limit` has been the documented `outcome` for a session the
  provider refused to continue since 0.4.1 (`docs/quickstart.md`, the
  0.4.1 changelog entry); the tool neither checks the word nor counts it.

The proposals pressing on this, each with measurements:

- [proposal 032](../proposals/032-the-journal-has-no-time-axis.md): the
  journal has no time axis — a median lead time of 85 minutes over 24
  tasks was reconstructed by hand; rounds are the largest single
  component and the journal cannot say how long one took; the journal
  transaction that records a completion still costs a full run of the
  required check;
- [proposal 024](../proposals/024-provider-quota-stop-cannot-be-recorded.md):
  what stopped the reporter's work was the provider's allowance, not the
  token count — both refusals stated a reset time, and the journal kept
  none;
- [proposal 018](../proposals/018-session-activity-vocabulary-and-cost.md):
  a provider-reported monetary cost has nowhere to go and lives in a
  sidecar file pinned by hash;
- [proposal 034](../proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md):
  a run truncated on its output limit has no documented `outcome` word,
  while `provider-limit` already has one;
- [proposal 026](../proposals/026-reviewer-facts-round-convergence-and-two-gaps.md),
  third finding: recording cost after `complete` needs idempotency — the
  reporter's first attempt would have doubled every task's cost, the
  second lost roles.

## Decision

### 1. A session's start and end are recorded explicitly

`record-session` accepts a start and an end — or a start and a duration,
which is the same fact the wrapper already knows; the record carries
start and end. `created_at` stays the moment the record is written — it
does not become a stand-in for either. The new values arrive under the
schema that introduces them
([ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md));
the record model that names the fields is a later decision — this ADR
decides what is recorded, not what the fields are called.

### 2. `report` shows lead time and its phases

Per task and in aggregate: opened → the start of the first implementer
session → the first review → approval → completion, and the review
rounds with their durations. For a session written before this decision
— one carrying no start and end — the boundary it cannot supply is shown
as **unknown**, never substituted with `created_at`: the write time would
print a wrong number confidently.

### 3. A provider-limit session can carry the reset time

An optional value on a session whose outcome is `provider-limit` records
when the provider's stated allowance resets — the fact the journal
dropped two times out of two in
[proposal 024](../proposals/024-provider-quota-stop-cannot-be-recorded.md)'s
measurement.

### 4. A session can carry a cost

An optional cost: an amount, a currency and its source — `reported` or
`estimated`. It sits beside `tokens`, not in place of them: tokens stay
what the record measures, cost is what the provider charges, and
providers disagree on what a token costs. `report` sums cost per
currency and converts nothing — a sum in one currency is a figure the
journal holds; a conversion would assert a rate it does not.

### 5. `output-limit` is a documented outcome

The outcome vocabulary stays documentation, not code — `outcome` accepts
any non-empty string and the tool neither checks nor counts it, as it
has since `provider-limit` was documented in 0.4.1. `output-limit` joins
it for a session that ended because the provider truncated the run on
its output limit — the same kind of fact as a refusal, said in a word
journals share.

### 6. Cost recording after completion is idempotent

`record-session --if-missing` makes a repeat write under the same
`task + role + actor + activity` a no-op with a message rather than a
second record —
[proposal 026](../proposals/026-reviewer-facts-round-convergence-and-two-gaps.md)'s
third finding, whose reporter measured both failure modes: a write that
would have doubled the cost, then one that lost roles.

### 7. The journal holds the summary; the process log holds the exports

The session summary stays in the journal, where `report` already reads
it. The raw provider exports the summary is drawn from go to the
process log ([ADR-0014](ADR-0014-where-things-live.md)) — local,
rotated, never read by the gate — alongside the raw accounting that
placement already names.

### 8. What a journal transaction costs is stated — as documentation

[proposal 032](../proposals/032-the-journal-has-no-time-axis.md)'s third
ask lands as a documentation sentence: the workflow documentation states
that completing a task costs one more run of the required check — the
journal transaction that records the evidence is itself a change CI runs
on. The ask's other half — a way for the required check to recognise a
journal-only change — is met by exposing the lane the gate already
computes, and goes to the journal-transactions work of
[proposal 019](../proposals/019-journal-transactions-assume-direct-commits.md)
and
[proposal 035](../proposals/035-journal-transactions-sweep-records-of-other-tasks.md),
as the proposal's disposition says.

## Left open

- The `economics` and `sessions` capture classes of
  [ADR-0005](ADR-0005-evidence-capture-and-format.md) stay outside this
  decision. They belong to the capture policy and its durable private
  store — designed, not built — and nothing here changes what a preset
  commits or where raw material lands under it; the process log of
  Decision 7 is where the raw exports sit until that store ships.
- The record model that names the new fields — a later decision, under
  [ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md).

## Consequences

- A session measures wall-clock work, not a write moment: lead time and
  its phases — the rounds
  [proposal 032](../proposals/032-the-journal-has-no-time-axis.md) could
  not time — become a `report` figure read from the same journal, and a
  session recorded before the new values existed reads "unknown" rather
  than a confident wrong number.
- A `provider-limit` session can say when work resumes — the fact that
  decided the reporter's model comparison in
  [proposal 024](../proposals/024-provider-quota-stop-cannot-be-recorded.md)
  stops living outside the journal.
- Money joins the record without pretending to be tokens: cost is
  optional, carries its currency and its source, and `report` sums per
  currency — two currencies are two sums, not a blended figure with an
  unstated rate.
- The outcome vocabulary stays words journals share — `provider-limit`,
  now `output-limit` — documented and unenforced, so a refusal, a crash
  and a truncation read differently from one another and the same way in
  every project.
- Recording cost after the task closes is safe to repeat: `--if-missing`
  turns the second run of a wrapper into a message, not a doubled
  figure.
- The boundary of [ADR-0014](ADR-0014-where-things-live.md) holds: the
  journal keeps the summary as evidence; the exports stay local.

## Alternatives considered

**Read a session's time from `created_at`.** Refused: it is the write
time, and a session is often written after the task completes, so the
report would state the gap between writes as if it were work. Where the
real times are missing the report says unknown; it does not substitute.

**A single currency for cost.** Refused: a conversion asserts an
exchange rate the journal does not hold, and a figure converted at a
rate nobody recorded is less auditable than two honest sums. The reason
cost sits apart from tokens — providers disagree on the price of a token
— applies to currencies alike.

**Commit the raw provider exports to the journal.** Refused: the journal
is evidence read by everyone forever, and a raw export can carry account
and billing detail no reviewer needs. Where captured raw material lives
is already decided — the capture classes of
[ADR-0005](ADR-0005-evidence-capture-and-format.md) and the process log
of [ADR-0014](ADR-0014-where-things-live.md) — and this decision leaves
that in place.

**Enforce the outcome vocabulary in code.** Refused: `outcome` is free
text and `provider-limit` has worked as documentation since 0.4.1 —
agreeing on the word is what lets two journals be compared, while a
checked enumeration would refuse the next limit a provider invents and
put a schema gate on a value no decision reads.

**Skip the write when the task already holds a session record.** Tried
by [proposal 026](../proposals/026-reviewer-facts-round-convergence-and-two-gaps.md)'s
reporter: it lost the roles that were missing. The deduplication key is
`task + role + actor + activity` for exactly that reason.

## Corrections

- 2026-10-03: the fourth Consequences bullet had the shared vocabulary
  make a refusal, a crash and a truncation "read differently across
  projects"; it makes them read differently from one another and the
  same way in every project.
- 2026-10-03: Decision 8 answered only the documentation half of
  [proposal 032](../proposals/032-the-journal-has-no-time-axis.md)'s
  third ask; it now says the other half — exposing the gate's existing
  journal-only lane to the required check — goes to the
  journal-transactions work of
  [proposal 019](../proposals/019-journal-transactions-assume-direct-commits.md)
  and
  [proposal 035](../proposals/035-journal-transactions-sweep-records-of-other-tasks.md),
  as the proposal's disposition says.
