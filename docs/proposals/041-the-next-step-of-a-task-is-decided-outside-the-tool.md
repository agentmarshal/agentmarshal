# 041 — The next step of a task is decided outside the tool: every adopter writes a driver that misreads why a step failed

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:4a5302df05bd8e5d051595955293555367038bf24d9402f8b21077965905b64a` · **Disposition:** accepted *(the command and the failure classes in the tool; the plan a supplied file, the driver the adopter kit)*

## Finding

The tool's journal records what happened to a task — sessions, reviews
with their verdicts, completion — and `gate` says whether a candidate may
merge, writing nothing itself. Nothing answers the question an unattended
loop asks after every step: **what is the next step for this task, and
should it be taken now?** So every adopter writes a driver. The reporter's
is about 60 lines of shell over the project's wrappers: for each task in a
queue, up to four attempts — integrate the base if the candidate conflicts,
complete if the newest review approves this head, otherwise run a fix
round; after the fourth attempt, stop the queue and wait for a person.

The decision part — conflict? approved *this* head? attempts left? — is a
pure function of the journal and git, the inputs the tool already has. It is
also the part the driver got wrong, because it could not tell *why* the
previous step failed:

1. **A provider usage limit consumed the attempt budget.** Each retry after
   the limit started, failed within seconds with the same "usage limit, try
   again later" message, and counted as an attempt — the queue spent its
   remaining attempts in about a minute and stopped; the right action was
   to pause the task until the reset time and run the next one.
2. **A finished run was treated as an unfinished one.** An implementer run
   ended exactly at the wrapper's hard time limit, after finishing the work
   and writing its report. The timeout's exit code made it a failed round:
   no review, and a redundant fix round on top of a complete candidate.
3. **An output-length truncation looked like any other failure.** A model
   failure that calls for continuing once, then escalating to a stronger
   model, was retried on the same model like an environment error.
4. **The queue could not be changed while it ran.** The order lived in the
   driving process's arguments; inserting an urgent task, removing one or
   pausing one until a quota reset each meant freezing the queue process,
   waiting out the current step, and starting a new one.

Measurements, as reported — two days, one project, one coordinating agent:

- **12 tasks completed** through the queue; **20 queue launches** (14 starts
  of the queue script, 2 "requeue after the current step" watchers, 4 side
  chains for tasks taken out of order). Every launch beyond the first was a
  manual change of the plan that a data-driven queue would have absorbed as
  an edit.
- **5 queue stops** that needed the coordinator: 1 provider usage limit
  (attempt budget exhausted in ~1 min, two attempts of ~10 s each), 2
  attempt budgets exhausted by repeated scope refusals that needed a
  contract amendment, 1 gate refusal because the amended contract had not
  been merged into the task branch, 1 attempt budget exhausted by hard time
  limits on a task whose runs were still working.
- **Cost of misclassified failures on one task:** 6 implementer rounds — 2
  ended at the time limit (one of them with finished work, followed by a
  redundant round instead of a review), 2 ended in output truncation and
  were retried on the same model, 1 was reviewed and returned, 1 produced
  the approved candidate.
- The **"approved this head"** rule (`reviewed_commit == HEAD`) caught every
  case where a fix round, a base merge or a work-in-progress commit had
  moved the head after an approval: no candidate was completed on a stale
  approval.
- Conflict detection with `git merge-tree --write-tree` before each attempt:
  1 conflict found and resolved by a merge-and-fix round, 0 completions
  stuck waiting for checks on an unmergeable pull request — the reporter's
  own figure for the previous two days, without it, is 3 such stalls of
  30–45 min. Proposal 040, from the same reporter, counted one such stall —
  a completion waiting on a check that could not start on an unmergeable
  pull request — among the six stalls it reports; the figures differ, and
  this digest does not reconcile them.

## Proposed

1. **The tool answers "what next" for a task** — a read-only command over
   the journal and git, `agentmarshal next <task> [--json]`, returning one
   of: `implement`, `fix` (with the findings to address — proposal 039),
   `integrate` (the base moved and conflicts, or the contract was amended
   and the branch does not have it), `review` (the head has no review),
   `complete` (the newest review approves this head and the gate would
   pass), `wait` (with a reason and, where known, a time), `stop` (with a
   reason a person must act on). Drivers then only execute; the policy is
   shared and tested once.
2. **Failure classes that the next step depends on** — session outcomes
   distinguishing at least: the model failed the task (next: a fix round, or
   escalation after N); the model was cut off by an output limit (next:
   continue once, then escalate); the provider refused — a usage limit, with
   a reset time when the provider gives one (next: `wait`, the attempt is
   not consumed); the environment failed before the model started (next:
   retry, not a round); the run hit the wrapper's time limit **with a
   finished report** (next: `review`, not `fix`). The reporter notes this
   extends proposals 024 (quota stops), 034 (limits as outcome values) and
   [proposal 036](../proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md)
   (an unfinished run must not be reviewed) to the decision they should
   drive.
3. **A plan as data** — the order of tasks, the implementer per task, pauses
   ("not before a time") and holds, living in the journal or a plan file the
   driver re-reads before each step, so inserting, pausing or skipping a
   task is an edit, not a process restart.
4. **A reference driver in the docs** — the loop above, about twenty lines
   over `next`, so adopters stop writing the policy themselves and only plug
   in how they run the implementer and the reviewer.

## Disposition — accepted; `next` and the failure classes in the tool, the plan a supplied file, the driver in the adopter kit

The selection rule is
[ADR-0012](../adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md)'s: a
durable fact about the task, checkable against the records with no live
process, is met by the tool; the rest is met by what the project supplies.

**`agentmarshal next <task> [--json]`** is accepted, in the tool: the
decision every adopter's driver re-implements is a pure function of the
journal and git — whether this head is approved, whether the branch
conflicts with the base, whether an amended contract reached the branch,
what the sessions' outcomes were — and the command executes nothing itself.
A new decision record, or a section of an existing one, will carry it.
Accepted; not shipped yet.

**The failure classes** are accepted: they are outcome vocabulary, which is
the accounting rework's ground — `provider-limit` is already a documented
outcome since 0.4.1, and the output-limit value is accepted with proposal
034 — plus a flag on the session that its report was finished, which is what
tells a run killed after completing its work from one killed before. The
flag is a different fact from the one
[proposal 036](../proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md)'s
refusal rests on: that refusal reads the session's `commit` against the
reviewed commit and an outcome other than `implemented`, while the flag
marks that the run wrote its report. `next` reads these classes.
Accepted; not shipped yet.

**The plan as data** is accepted, met by what the project supplies rather
than by the journal: a queue's live state is not a durable fact about a
task — it changes mid-step, and a journal transaction costs about seven
minutes in the reporter's setup — so the plan is a file in the local state
the decision on where local state lives defines (`.git/agentmarshal/`),
with a documented format: order, implementer, `not-before`, hold. `next`
reads `wait` and holds from it. Accepted; not shipped yet.

**The reference driver** is accepted: the loop over `next`, about twenty
lines, becomes part of the adopter kit the project supplies — the same place
proposal 038's layer templates live. Accepted; not shipped yet.

## Where

Nothing here is shipped yet. `agentmarshal next` and the session failure
classes — the new outcome values and the "report finished" flag — are
accepted into the tool, the classes with the accounting rework; the plan
is accepted as a supplied file in local state with a documented format; the
reference driver goes into the adopter kit.

## Corrections

- 2026-10-03: the failure-classes paragraph called the "report finished"
  flag the same fact
  [proposal 036](../proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md)'s
  refusal rests on;
  [proposal 036](../proposals/036-review-accepts-a-candidate-the-implementer-did-not-finish.md)
  rests on the session's `commit` and an outcome other than
  `implemented`, and the paragraph now says so.
