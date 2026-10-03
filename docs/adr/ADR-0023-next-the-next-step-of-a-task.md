# ADR-0023: `next` — the next step of a task

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0007](ADR-0007-operator-acceptance.md) (an acceptance
substitutes for the approving verdict and names exactly the latest
review's blocking findings),
[ADR-0008](ADR-0008-journal-placements.md) (the sidecar placement; the
host is only ever read),
[ADR-0012](ADR-0012-what-the-tool-does-and-what-it-supplies.md) (the core
executes nothing and holds no live state; measured needs outside it are
met by the adopter kit),
[ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md) (an
extension's `pre-gate-stop` pause, lifted by an acceptance over the
pause itself),
[ADR-0014](ADR-0014-where-things-live.md) (the process log — local,
rotated, never read by the gate — and where local state lives),
[ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)
(strings from records are escaped on display),
[ADR-0016](ADR-0016-the-lifecycle-of-review-findings.md) (the
`changes_required` count and the advisory dispositions `complete`
requires),
[ADR-0018](ADR-0018-governing-the-contract.md) (the contract's ordered
implementer and reviewer lists, the independence rules, the agreement
record),
[ADR-0019](ADR-0019-accounting-time-quota-resets-money.md) (session start
and end, `resets_at`, the outcome vocabulary as documentation) and
[ADR-0022](ADR-0022-the-0-5-0-record-model-one-transition.md) (the record
model this command reads: a session's `commit`, `report_ready`,
`resets_at`, `cli_session`, `fallback_reason`, `mode: resolution` with
`carried_approval`, the step events, the plan file) — and on the
dispositions of
[proposal 034](../proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md),
[proposal 036](../proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md),
[proposal 041](../proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md),
[proposal 042](../proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md)
and
[proposal 043](../proposals/043-review-before-integration-makes-every-merge-stale.md).
**It revises
[ADR-0019](ADR-0019-accounting-time-quota-resets-money.md)'s decision 5**
— the outcome vocabulary was declared unread: `next` now reads it, and
`outcome` stays free text — **refines
[proposal 036](../proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md)'s
disposition** — a `time-limit` session whose report is ready does not
trip the unfinished-candidate refusal, decided as decision A below —
**and extends
[ADR-0014](ADR-0014-where-things-live.md)**: `next` is a further local
reader of the process log, which only `status` and `doctor` read before;
the gate still never reads it. The texts of ADR-0019, proposal 036 and
ADR-0014 are amended by a later documentation task; this ADR names the
revisions.

This ADR records a decision. The command, the rule table and the driver
it describes are **not implemented by this document**; they follow in
their own tasks. The present tense below is how a decision is written,
not a claim about shipped behaviour.

## Context

Nothing today answers the question an unattended loop asks after every
step: what is the next step for this task, and should it be taken now.
The journal records what happened, `gate` says whether a candidate may
merge, and every adopter writes the deciding driver itself.
[Proposal 041](../proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md)
measured what one such driver costs: a provider usage limit consumed the
queue's attempt budget within a minute; a run that had finished its work
when the time limit hit was counted a failure and re-done instead of
reviewed; an output-length truncation was retried on the same model as
if it were an environment error; and the queue took 20 launches in two
days — every launch beyond the first a manual change of the plan that a
data-driven queue would have absorbed as an edit — because its order
lived in the driving process's arguments.

How it works today:

- the gate derives its inputs when the flags are omitted: the task id
  from the branch's name under the `<class>/<task-id>-<slug>` policy
  (classes `feat`, `fix`, `docs`, `ci`, `completion` — a branch matching
  nothing, or naming two task ids, is refused), the candidate commit
  from the checked-out head, and the base from `origin/HEAD` — `master`
  when no `origin/HEAD` exists — refusing when no default base resolves
  (`gate_context.py`);
- `git merge-tree --write-tree` performs a real merge in-core and writes
  the resulting tree objects to the object database (`git help
  merge-tree`);
- several of the gate's checks are decidable from the records and git
  alone, with no pipeline: the refusal of an empty `merge-base..commit`
  range ("candidate range contains no changes"), the contract read from
  the merge-base tree with the refusal "the opening transaction must
  merge before implementation" when it is absent there, the scope check
  against that base-side contract, the latest review of the exact commit
  or an acceptance covering exactly its blocking findings, and the
  declared reviewer identity compared with the candidate's writers over
  the same range. The pipeline attestation is the check that is not:
  it takes the attested SHA from the invoker (`gate.py`);
- `complete` re-runs the gate and takes `--base`, which must be an
  ancestor of the candidate — the merge-base it was gated against, not
  the post-merge tip (docs/self-hosting-workflow.md);
- an in-flight step lives in the process log — a `step-started` event
  with its deadline, closed by a `step-ended` event or by the record it
  ends with — read by `status` and `doctor`, never by the gate
  ([ADR-0014](ADR-0014-where-things-live.md),
  [ADR-0022](ADR-0022-the-0-5-0-record-model-one-transition.md)).

One placement note: the merge slot of
[proposal 043](../proposals/043-review-before-integration-makes-every-merge-stale.md)
is a supplied extension pausing at `pre-gate-stop`; for `next` its pause
is an ordinary extension pause, handled by rule 11 like any other.

## Decision

### 1. The command

`agentmarshal next <task> [--branch …] [--base …] [--json]` prints one
action and its reason. The task is a required argument — the form
without it is left open below. `--branch` defaults to the current
branch; `--base` derives the way `gate` derives its default base —
`origin/HEAD`, `master` when no `origin/HEAD` exists, a refusal when
neither resolves (`gate_context.py`).

The command executes nothing and writes nothing — not to the journal,
not to the process log, not to refs, not to the object store. The
conflict check runs `git merge-tree --write-tree`, which writes tree
objects, so it runs in a temporary object store with the repository's
objects reached through alternates; in a sidecar the host's object store
is only ever read
([ADR-0008](ADR-0008-journal-placements.md)). Exit code 0 means an
action was determined; otherwise the output says what to do.

### 2. What `next` reads

- the task's journal;
- git — the head, the base, the conflict check, and whether the latest
  contract amendment reached the branch;
- the plan file — `hold`, `not_before`, `implementer`;
- the process log — an open step for the task;
- the project settings — the `changes_required` threshold
  (`review.changes_required_threshold`, default 3, of
  [ADR-0022](ADR-0022-the-0-5-0-record-model-one-transition.md)).

A missing plan file, log file or field is not an error: the rule that
needs it does not fire, and the output carries `inputs_missing`. In a
sidecar the journal, the plan and the log come from the journal
repository; git state is read from the host, read-only; and the log is
visible only on the machine that wrote it — the process log promises no
visibility between machines
([ADR-0014](ADR-0014-where-things-live.md)).

### 3. The actions

`done` · `hold` · `wait` (until a stated time) · `stop` (a person is
needed, with the reason) · `integrate` · `implement` · `fix` (which
implementer; the latest review's findings; `resume` as a hint for
continuing the session) · `review` (which reviewer, where the rule names
one; with `mode: resolution` and `carried_approval` where they apply) ·
`complete` (with the base for `complete --base`, and the ids
of the advisory findings that still need a disposition).

### 4. The table — first match, top to bottom

Definitions. **The head** is what `--branch` resolves to — the current
branch's tip by default. **The latest review of the head** is the latest
review record whose `reviewed_commit` equals the head. **After a
`reopened` record, everything older than it is not counted** — reviews,
sessions and acceptances alike.

1. The task is closed → `done`.
2. The contract is not in the base tree — the opening transaction has
   not merged (`gate.py`) → `stop` "merge the opening".
3. An open step for the task in the process log — a `step-started` with
   neither a `step-ended` nor a record of its kind after the start: its
   deadline not yet reached → `wait` until it; passed → `stop` "step
   overdue".
4. The plan: `hold` set → `hold`; `not_before` in the future → `wait`
   until it.
5. The latest session — an implementer's or a reviewer's — ended
   `provider-limit`, and the latest review of the head (if any) does not
   approve it — where one does, this rule does not fire: a quota stop
   cannot demote an approved head to `fix`, and rule 8 decides.
   Otherwise `resets_at` in the future → `wait` until it; with no reset
   recorded, by whose session it was: an implementer's — a next
   implementer in the contract's list → `fix` by them with
   `fallback_reason: provider-limit`; a reviewer's — a next reviewer in
   the contract's list → `review` by them —
   [ADR-0018](ADR-0018-governing-the-contract.md)'s decision 3 orders
   both lists — and either list exhausted or absent → `stop`.
6. The head conflicts with the base → `integrate`. In the embedded
   placement: the latest contract amendment is not an ancestor of
   merge-base(head, base) → `integrate` "merge the amendment" — the rule
   does not apply in a sidecar, whose contract is not in the host's
   history.
7. No commits over the base → `implement` — including the retry after a
   first run's failure.
8. A latest review of the head exists:
   - it approves → rule 11;
   - it does not approve, but the latest acceptance of this commit names
     exactly its blocking findings
     ([ADR-0007](ADR-0007-operator-acceptance.md)) → rule 11;
   - it does not approve, and the `changes_required` count has reached
     the threshold → `stop` "round threshold reached: amend the
     contract, accept or abandon" — the count is taken since the latest
     contract amendment (decision B below);
   - otherwise → `fix` with that review's findings.
9. No review of the head, and the head is a merge of the base into a
   previously approved candidate → `review` in `resolution` mode with
   `carried_approval`
   ([proposal 043](../proposals/043-review-before-integration-makes-every-merge-stale.md),
   [ADR-0022](ADR-0022-the-0-5-0-record-model-one-transition.md)).
10. No review of the head — decide by the latest implementer session
    (one whose `commit` is the head, or that carries none):
    - `implemented` → `review`;
    - `time-limit` with `report_ready` → `review` — the unfinished-
      candidate refusal does not fire (decision A below);
    - `output-limit` → `fix` by the same implementer, continued; two in
      a row since the latest review → the next implementer from the
      contract's list; the list exhausted or absent — a contract header
      below schema 3 → `stop`;
    - `stalled`, `safety-limit` → `fix` with `resume` set to the
      session's `cli_session` — a hint; a CLI that will not resume falls
      back to a new round
      ([proposal 042](../proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md));
    - `environment-failure` → retry the same step — not a round;
    - `failed`, or `time-limit` without a report → `fix`; two in a row
      since the latest review → the next implementer —
      [proposal 034](../proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md)'s
      switch after two failed rounds; the list exhausted → `stop`;
    - an outcome the vocabulary does not know → `stop` "outcome not
      recognised";
    - no sessions at all → `review`, marked "origin not recorded" — the
      behaviour
      [proposal 036](../proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md)
      keeps for a candidate no session names.
11. Before `complete`: the gate checks decidable from the records,
    without a pipeline — the scope check against the contract at the
    base, the reviewer not a writer of the candidate, the reviewer list
    and the independence rules,
    [proposal 036](../proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md)'s
    refusal, the agreement record where the project requires it, an
    extension pause standing without its acceptance. Any one fails →
    `stop` naming the check. All pass → `complete`, with the ids of the
    advisory findings still without a disposition
    ([ADR-0016](ADR-0016-the-lifecycle-of-review-findings.md)).

### 5. What counts as an attempt

`environment-failure` is not a round — the outcome vocabulary of
[ADR-0022](ADR-0022-the-0-5-0-record-model-one-transition.md) marks it
so — and neither is `provider-limit`, on
[proposal 041](../proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md)'s
own ground: the provider's refusal did not consume the attempt. Together
they are the distinction proposal 041's first measurement missed. Rounds
for the threshold are `changes_required`
verdicts
([ADR-0016](ADR-0016-the-lifecycle-of-review-findings.md)). The
"two in a row" counters of rule 10 count implementer sessions since the
latest review.

### 6. Output

Text: `next: <action> — <reason>`, followed by detail lines; strings
taken from records are escaped on display
([ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)).
`--json` prints the same unescaped: `{action, reason, task, until?,
implementer?, reviewer?, resume?, findings?, mode?, carried_approval?,
fallback_reason?, base?, advisories?, inputs_missing}`.

### 7. Two points decided by the operator

**A. A `time-limit` session whose report is ready is reviewable.**
[Proposal 036](../proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md)'s
disposition has `review` and the gate refuse a candidate whose producing
session did not end `implemented`. A run the time limit stopped after
the work was finished and the report written is not that case, and
treating it as one is the second failure class proposal 041 measured —
a finished candidate marked failed and re-done instead of reviewed. The
refusal therefore does not fire on `time-limit` with `report_ready`:
this is a **refinement of proposal 036's disposition**, decided here and
named as such — not an override spent case by case. The alternative —
`next` answering `review` carrying the unfinished-candidate override and
a reason, passing every such run through it — was considered and not
taken: the override is for a case the operator judges, and a finished
run with its report written needs no judgement. The explicit override
proposal 036's disposition leaves the operator — `review
--allow-unfinished` — stays a flag of `review`, outside `next`.

**B. The round threshold counts since the latest contract amendment.**
[ADR-0016](ADR-0016-the-lifecycle-of-review-findings.md)'s count of
`changes_required` verdicts runs over the whole task and blocks nothing;
the remedy it names is revisiting the contract. If `next` counted the
same way, the remedy would never lift the stop: after the amendment the
counter would still stand at the threshold, and `next` would refuse to
continue a task whose contract had just been fixed. Rule 8's threshold
therefore counts the `changes_required` verdicts recorded since the
latest `amendment` record; `status` keeps showing the whole-task count
ADR-0016 gave it. The alternative — counting over the whole task and
leaving a task at `stop` to the person, without `next` — was considered
and not taken: it makes the prescribed remedy permanently unusable.

### 8. The reference driver — in the adopter kit

The loop over `next`, about twenty lines, ships in the adopter kit —
the same place
[proposal 038](../proposals/038-an-adopter-setup-cannot-be-carried-to-the-next-repository.md)'s
layer templates live — per
[proposal 041](../proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md)'s
disposition and
[ADR-0012](ADR-0012-what-the-tool-does-and-what-it-supplies.md)'s rule.
It walks the plan in order; on `wait` and `hold` it takes the next task;
on `stop` it shelves that task rather than the queue; and the final
stage follows
[proposal 043](../proposals/043-review-before-integration-makes-every-merge-stale.md)'s
order — integrate, review, merge.

## Left open

- `next` with no task argument — the first ready task in plan order —
  comes after 0.5.0.
- The texts this ADR names as revised — ADR-0019's decision 5, proposal
  036's disposition, ADR-0014's list of local readers — are amended by
  the documentation task that follows; this document is the decision,
  not the edit.

## Consequences

- The decision every adopter's driver re-implements is made once, in the
  tool, and drivers only execute: the eleven-rule table is a published
  promise to adopters, and changing a line of it is a new decision, not
  a patch note.
- `next` is safe to run anywhere, at any time, as often as a driver
  wants: it executes nothing and writes nothing — the conflict check's
  temporary object store disappears with it, and in a sidecar the host
  is touched by reads alone, as
  [ADR-0008](ADR-0008-journal-placements.md) requires.
- Two machines can print different actions for the same task: the
  process log does not travel, and neither does the plan. That is the
  boundary of reading local inputs, stated openly — the journal-decided
  part of the table agrees everywhere, the step and plan rules do not
  promise to.
- The outcome vocabulary gains its first reader inside the tool, and
  stays free text: a word the table does not know lands on `stop`
  "outcome not recognised" — visible — rather than being silently
  misread. A new outcome a provider invents costs a rule, not a schema.
- A run killed by the time limit after finishing its work reaches review
  without spending the manual override — the second misread of
  [proposal 041](../proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md)
  closed — while the refusal still stands over a run that ended before
  its work did.
- `status` and `next` can disagree about the `changes_required` count,
  by design: one shows the whole-task signal
  [ADR-0016](ADR-0016-the-lifecycle-of-review-findings.md) prints, the
  other the count since the contract last changed — the difference is
  what makes the remedy usable.
- The gate is untouched: `next` re-decides the checks it can and
  substitutes for none of them — `complete` still re-runs the gate, and
  the pipeline attestation stays a fact the invoker supplies at merge
  time.

## Alternatives considered

**The driver in the core.** Refused: the core executes nothing and
holds no live state —
[ADR-0012](ADR-0012-what-the-tool-does-and-what-it-supplies.md)'s
boundary. A driver that launches implementers and reviewers and waits on
them would put the loop's live state into the one component that must
not hold it. The policy is what belongs in the tool, and it arrives as
`next`; the loop that calls it is the supplied reference driver an
adopter owns.

**Documenting the table only.** Refused: the table was already written
down — once per adopter, inside every driver — and
[proposal 041](../proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md)'s
measurements are of exactly that table misread. Eleven interacting rules
are tested once in the command or re-implemented diverging per adopter;
the finding the proposal reports is the divergence itself.

**The plan in the journal.** Refused: the queue's order changes
mid-step and is not a durable fact about a task —
[proposal 041](../proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md)'s
disposition settled this when it placed the plan in the local state
[ADR-0014](ADR-0014-where-things-live.md) defines. A `hold` or
`not_before` edit would otherwise pay a journal transaction — a merge
through CI — for each pause of a task. The plan is `plan.toml`, local
and re-read each step; the journal is untouched.
