# 035 — A journal transaction carries the records of every task in flight, so a task can be opened by another task's transaction

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:3b8c00b1156da2c6776fcbb6a17b80fd642b7f819e248edef8d4ee897f4c398f` · **Disposition:** accepted

## Finding

Commands write records into the working tree of the checkout: `open`
writes the contract and the `opened` record, `review` writes the review
record and its prose, `record-session` writes a session. Committing them
is left to the adopter. With a protected base branch that means a journal
transaction per event — the pattern of proposal 019 — and the staging
recipe is the one the tool itself prints in the outbox README `init`
writes: stage `.agentmarshal/journal`, or `.agentmarshal` minus the
outbox. With several tasks in flight, that stages whatever is uncommitted
at that moment, for every task: review and session records of one task,
written a minute earlier, ride in the `complete` transaction of another.
Mostly that is bookkeeping noise. The same happens to a contract written
by `open` but not yet published by its own transaction: it is published
by whichever transaction of another task runs first.

The reporter hit the second case in a way that cost a round: the
coordinating agent created a contract, a transaction of another task
published it before its own `open` transaction ran, the coordinator's
check for "not yet published" missed it, and the implementer launch
refused because the contract was not yet on the base branch — it arrived
there a few minutes later inside a pull request titled for a different
task.

Nothing in the tool notices. `validate` accepts the records, because they
are valid wherever they come from; `gate` on a journal-only branch named
for one task checks that task — its records and the paths of its own
journal subtree — and does not look at records of other tasks in the same
diff.

Measurements, as reported — counted with a small read-only script over
the reporter's git history: every commit whose subject is a journal
transaction naming its task or tasks, and the files it touched under
other tasks' journal directories:

- Before the reporter's own fix — the whole history of their project, on
  0.3.0 and 0.4.0 alike: **252 journal transactions; 70 (28%) carried
  files of other tasks** — session records, review records and artifacts —
  and also **23 contracts and 20 `opened` records** of tasks other than
  the one the transaction names. Those tasks were opened or amended by
  someone else's transaction and have no transaction of their own in the
  history.
- After changing their wrapper to stage only the named task's journal
  directory and to list, not take, anything else: **26 journal
  transactions over the next day** with three to five tasks in flight —
  one of them a deliberate joint opening of five tasks named explicitly —
  and **0** carried files of other tasks.

So the fix is cheap and complete on the adopter side — which is the
reporter's argument for putting it into the helper proposal 019
describes, before every adopter writes the sweeping version first.

## Proposed

The agreement events — `open` and `amend` — should arrive on the base
branch in a transaction that names their task, and the tool should be
able to tell when they do not:

- The transaction helper proposal 019 asks for — accepted, not yet
  shipped — should stage only the journal directory of the task it is
  given, and list uncommitted records of other tasks instead of taking
  them. As 019 is written — "stages only the journal" — the helper would
  reproduce this defect for every adopter who runs tasks in parallel.
- `gate` (or `validate` against a base ref) on a branch that names a task
  should at least warn, and preferably refuse, when the diff adds
  `opened` or amendment records of a different task; review and session
  records of other tasks could stay a warning.
- `status` could show, per task, records present in the working tree but
  not on the base branch, so a coordinator does not need its own check
  for "is this contract published yet".

## Disposition — accepted, together with proposal 019

The finding is measured on both sides of the fix — more than a quarter of
the reporter's journal transactions carried other tasks' records until
their wrapper stopped taking them, and none did after. The sweeping
recipe is also the one our own `init` writes into the outbox README, so
the defect is ours to remove from the published pattern rather than every
adopter's to rediscover.

The transaction helper proposal 019 promised takes only its own task's
journal directory — anything else uncommitted it lists rather than takes
— and that constraint is now part of the accepted work, before the helper
ships in the sweeping form. With it, the gate: when a transaction adds
`opened` or `amendment` records of a task it does not name, the gate
warns — the reporter's lesser option; the record stays valid evidence,
what was wrong is which transaction carried it. The `status` listing of
records present in the working tree but not on the base branch goes with
the same work. Accepted; not shipped yet.

## Where

Nothing here is shipped yet. The per-task staging rides on proposal 019's
transaction helper; the gate warning about another task's `opened` or
`amendment` records, and the `status` listing of unpublished records,
come with the same work.
