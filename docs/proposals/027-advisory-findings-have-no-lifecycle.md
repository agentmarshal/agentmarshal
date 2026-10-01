# 027 — Advisory findings have no lifecycle, so `approved` quietly absorbs known defects

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:c911cbe77d187da24edf202d29df654d1dba19fceb4103dfdf5186e8a7d73043` · **Disposition:** accepted *(in part; the verdict rename is declined)*

## Finding

A review record carries two lists: `findings` and `advisory_findings`. The
gate reads the verdict — and, when it does not approve, whether the latest
acceptance record covers exactly the blocking list. Neither path reads the
second list. Nothing in the journal ever says what happened to an advisory
finding: no record of the decision, no reason attached to it, no way to find
the deferred ones later.

The verdict word makes this worse. `approved` reads as "this is fine"; what
it means is "the acceptance criteria are met". A review can approve a
candidate and, in the same record, describe a defect the criteria happen not
to cover. Both statements are true, and the tool treats only the first as
evidence — so a task can complete with a reviewer's written description of a
real defect in its own journal, indistinguishable from a task whose
advisories were all cosmetic.

The reporter is explicit that making advisories blocking is the wrong fix,
and reviewers are right to resist it: a finding is blocking when it violates
an acceptance criterion, and many genuine defects do not — they are outside
the contract's scope, or in code the task only touched incidentally, or
fixing them would widen the task. The advisory list exists precisely so the
reviewer can do neither; what is missing is somewhere for the answer to go.

Measurements, as reported, from the reporter's last ten governed tasks:

- Reviews recorded: **34**.
- Reviews with verdict `approved` that also carried advisory findings: **18**.
- Advisory findings on those approved reviews: **55**.
- Implementation rounds run *after* a verdict of `approved` had already been
  recorded, because a human-facing loop judged some advisory to be a real
  defect: **7**, in **5** of the ten tasks.

Three of those rounds, described in the reviewer's own words at the time:

- a migration snapshot whose link back to its predecessor held a zero UUID,
  breaking the snapshot chain for every later migration;
- a verification script that read only the response's status code and never
  consumed the body, so the process kept the socket alive and the command
  hung indefinitely — in the tool whose whole purpose is to be run during an
  incident;
- an editorial workflow where unpublishing a document promoted an
  unreviewed draft on the next publish, defeating the guarantee the task was
  written to establish.

Each of those landed in a journal whose machine-readable state said
`approved`, `gate: passed`; the only reason they were fixed is that a
human-facing loop re-read the prose.

## Proposed

Give an advisory finding a disposition, recorded once, at completion:
`complete` accepts a disposition for each advisory finding on the latest
review of the completed commit — `fixed`, `deferred` or `rejected`, each
with a short reason, `deferred` optionally carrying a follow-up task — and
the gate requires that every advisory finding on that review *has* a
disposition, without requiring any particular one; `status` and `report`
surface open deferrals. Deliberately the weakest rule that still works: it
does not make advisories blocking and does not let the gate judge severity —
it converts silence into a recorded choice.

A second, independent suggestion: the verdict vocabulary invites the
misreading, and `criteria_met` says what `approved` actually means. If
renaming is too disruptive, the documentation could at least state it,
because every adopter learns it the same way — by finding a defect under a
green verdict.

## Disposition — accepted for the lifecycle, declined for the rename

**The dispositions** are accepted, into the decision on the finding
lifecycle. They land in the same machinery as proposal 026's
converging-rounds half — the link between a task's review records and a
finding's `new`/`persisting`/`resolved` status — and as a further report in
this batch about findings not feeding back into the next round: a finding
that has a recorded answer and a finding that has a recorded history are one
question, and should be settled once. The reporter's minimalism is the right
shape — the gate checks that an answer exists, not which answer; accepting a
defect stays a cheap, legitimate decision, and silence stops being one.
Accepted; not shipped yet.

**The rename** is declined — by us, upstream: the reporter proposed it and
we are the ones refusing it. `approved` is a word in the record vocabulary,
written into every review record every journal holds and read by every
wrapper that consumes them; renaming it rewrites the meaning of evidence
already recorded. The reporter's fallback is taken instead: the
documentation will state that `approved` means "the acceptance criteria are
met", so the misreading stops costing each adopter a defect to learn.
Accepted for documentation; not shipped yet.

## Where

Nothing here is shipped yet. The advisory-finding dispositions wait on the
finding-lifecycle decision; the documentation stating what `approved` means
is accepted, to be written. The rename is declined by us.
