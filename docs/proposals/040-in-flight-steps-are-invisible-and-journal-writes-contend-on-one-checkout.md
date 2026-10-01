# 040 — In-flight steps are invisible to the journal, and journal writes contend on one checkout

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:4121e437dc67e47481e9bd1347a06844accc3306fed1a011f71da2b490287dd8` · **Disposition:** accepted *(in part; the stuck-step visibility is met by a supplied watcher template, not a record type)*

## Finding

Two properties of the journal make a stuck step invisible, and make one stuck
step stop the others, when tasks run in parallel as background chains.

1. **The journal records only finished steps.** A session record is written
   when the implementer's or reviewer's run has ended; a review record when
   the verdict exists; nothing marks that a step has *started*. While a step
   runs — or hangs — the journal has no trace of it: `status` cannot say a
   review of this task started 45 minutes ago and has not finished, and
   `doctor` cannot list overdue steps. Everything the tool could know about
   liveness, it learns only after the fact.
2. **Journal writes need the shared working tree.** Records are files in the
   repository, so every transaction — open, amend, review records,
   completion — switches branches in the one checkout where the journal
   lives, commits, waits for the required check of the transaction's pull
   request, and switches back. With several tasks in flight, all of them
   queue on that checkout; adopters add a lock around it, and a lock held
   for the whole wait of a check turns one slow or stuck transaction into a
   convoy.

Measurements, as reported — two days, about 15 tasks in parallel chains, one
project:

- **6 stalls of 30–45 minutes each**, every one detected by a person or the
  coordinating agent polling — none by the tool:
  - a completion waited for a required check on a pull request that had
    become unmergeable after another task merged; the provider does not
    start checks for a conflicting pull request, so the wait could never
    end, and it held the checkout lock meanwhile (45 min);
  - a batch transaction waited more than 30 minutes for the checkout lock
    held by that completion and was killed by its own time limit without
    doing anything;
  - two review steps did not run because a provider quota was exhausted, and
    the chains went on to fix rounds without a review (proposals 024, 036);
  - a deployment after merge failed on a server precondition and was
    noticed only incidentally;
  - a calendar-driven required check — the end-of-life of a pinned tool —
    turned every code pull request red at once.
- Median duration of a journal transaction's required check: **6.7 min**;
  with the checkout lock held for the whole wait, two completions finishing
  together serialise for 15–40 minutes.

## Proposed

1. **Leases for in-flight steps.** A step — implementation, review,
   completion, a journal transaction — opens with a lease record (task,
   step, actor, started at, deadline) that its normal record closes, or that
   a failure or abandonment closes with an outcome; `status` shows open
   leases with their age, and `doctor` lists leases past their deadline. A
   wrapper that is killed leaves an expired lease, which is exactly the
   signal that something is stuck — not how long a step took (proposal 032)
   or where it stopped (proposal 024), but that a step is running *now* and
   is overdue.
2. **Journal writes without the shared checkout** — a way to create and
   commit journal records without switching the user's working tree, via
   git plumbing to a journal branch or a tool-managed dedicated worktree, so
   parallel tasks do not contend on one checkout and a lock, if any, is held
   for seconds rather than the duration of a provider check. The reporter
   continues proposals 019 and 035 here.
3. **Guidance for wrappers that wait on provider checks** — a documented
   fail-fast rule: before waiting on a required check of a pull request,
   verify that the pull request is mergeable and that a check has been
   created within a short window; fail fast otherwise. The tool does not
   wait for checks itself, but the recommended workflow makes every adopter
   write such a wait.

## Disposition — the fail-fast rule and the checkout-free write accepted; the visibility need met by a supplied template

**The fail-fast rule** for waits on provider checks is accepted as
documentation: the workflow this project publishes is what makes every
adopter write such a wait, and the reporter's first stall is the failure
mode the rule exists for — a pull request that can never start its check was
waited on for 45 minutes. Accepted; to be written.

**The visibility of stuck steps** — the need is accepted, and it is met by a
watcher template the project supplies rather than by a record type in the
journal. The reason is the workflow the project recommends for a protected
base branch — the pattern of proposal 019 — not the journal's mechanics:
the tool writes records into the working tree and leaves committing to the
adopter, but under that workflow every journal write is a transaction
through a pull request and its required check, so a record saying "this
step is running" could only appear once that transaction had cleared —
minutes late, queued behind the very convoy it is meant to expose. A
step's liveness lives where the step does — the run, the lock, the
provider's API — so the project supplies a watcher for those places as a
template, checked against its own cycle the same way the adopter layer of
proposal 038 is supplied. Not shipped yet.

**Journal writes without the working tree** are accepted, into the
journal-transactions work of proposals 019 and 035: the helper that stages
and carries a task's records already has to answer how it touches the
checkout, and a write that never switches the user's tree is the same
question answered further. Accepted; not shipped yet.

## Where

Nothing here is shipped yet. The fail-fast rule for waits on provider checks
is accepted as documentation, to be written; the stuck-step watcher is
accepted as a template the project supplies, not a record type; the
checkout-free journal write goes with the transaction helper of proposals
019 and 035.
