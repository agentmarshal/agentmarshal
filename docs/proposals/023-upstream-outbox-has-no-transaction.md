# 023 — The upstream outbox has a convention but no transaction, and it sits where journal tooling sweeps it

- **Reporter:** Adopter D (greenfield project on Linux, GitHub, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:bc65a3ee95507aea` · **Disposition:** accepted

## Finding

`init` creates the outbox and a README that states the convention well: one file
per finding, sanitized at source, sent as a batch. Then nothing. No command
stages, commits or batches it, and nothing says how findings are supposed to
reach a commit in a repository whose journal is written by tooling rather than
by hand.

That gap has a specific consequence, because the outbox lives inside the journal
root. Any wrapper that commits a journal transaction the obvious way — stage the
journal directory, commit, open a pull request — sweeps whatever findings happen
to be unstaged at that moment into a commit about something else. The adopter
does not choose this; it is what the layout produces.

The mixing runs both ways. A findings commit drags in task evidence that
happened to be pending, and a task's completion commit drags in half-written
findings. Neither history is then readable on its own.

Measurements, as reported, from the reporter's first five governed tasks:

- Findings written: **9**. Committed at the time of the report: **8**.
- Commits those 8 landed in: **3**, none of them about findings — **6** in a
  contract amendment for one task, **1** in the opening of another, **1** in the
  completion of a third.
- Findings that reached a commit whose message mentions findings: **0 of 8**.
- Cost of the workaround: the reporter moves a pending finding out of the
  repository before every task completion and moves it back afterwards.

## Proposed

Any one of three, listed cheapest first: state in the outbox README that the
outbox is not journal evidence and should be excluded from journal staging, with
the pathspec that does it; ship a command that stages only the outbox, runs the
same leak scan the merge boundary runs and produces one batch commit; or make
the separation between the outbox and the journal explicit in the layout
documentation so tooling authors treat them as different things.

The underlying point is general: the outbox is the one directory under the
project directory that is not evidence about the adopter's own work, and nothing
says so. Everything else there is append-only, task-scoped and gated. Findings
are none of those.

## Disposition — accepted

Correct, and it applies to us: the driver that lands this repository's own
completion transactions stages the whole project directory, and would have swept
our outbox in exactly the way described if anything had been pending in it.

All three options are accepted, in the order given, because they are not
alternatives so much as stages. The README sentence and the pathspec ship first,
because they cost one line and would have prevented all eight of the reported
cases. The layout documentation follows in the same change, stating that the
outbox is not evidence — which is the sentence that makes the other two
obvious.

The command comes after, and slightly larger than proposed. Batching findings is
half of a delivery channel; the other half is what the reporter cannot do today
at all, which is learn what happened to a finding after sending it. So the
command will both produce the batch and report the disposition of what was sent
before, matching by the source hash this batch introduces. That is a release
later than the documentation, and it is the first product feature this outbox
convention has earned.
