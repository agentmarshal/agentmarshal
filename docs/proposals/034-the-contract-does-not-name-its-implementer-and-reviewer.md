# 034 — The contract does not name its implementer and reviewer, so the assignment lives in the wrapper

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:ab8c047da4d9d621125d69e88cab29deeb07bd79b1a5c4e8f3a034270dd69502` · **Disposition:** accepted

## Finding

Who implements a task and who reviews it are decisions the reporter's
coordinating agent makes per task: a default implementer, an escalation
to a stronger one after failed rounds or for a larger task, and — as of
the report — a reviewer chosen so that it never shares a vendor with the
implementer. None of that is in the contract: its header carries `scope`
and `acceptance` and no assignment, so the decision is expressed only as
environment variables of the reporter's launch wrappers, set by hand at
launch time.

What the tool records afterwards is only what ran: `record-session`
stores the `actor`, and `review` stores the reviewer's declared identity.
`gate` checks one thing about identity — that the reviewer's declared
email differs from the candidate's commit authors. It cannot check that
the reviewer was the one intended, that it is independent of the
implementer by vendor or model, or that an escalation was deliberate
rather than a misconfigured launch.

Measurements, as reported — from 69 consecutive tasks on 0.4.0:

- **145 implementer sessions** from two vendors; **6 tasks switched
  implementer mid-task** — after an output-limit truncation, after two
  failed rounds, or because the first implementer's weekly quota ran out.
  Each switch was a relaunch with different environment variables, and
  the contract of those tasks is identical to the ones that did not
  switch.
- **150 reviewer sessions**, all from one reviewer so far. The reviewer
  shares a subscription with the coordinating agent; when that
  subscription hit its session limit, reviews failed and the whole loop
  stopped for about an hour and a half. Moving one implementer's reviews
  to a reviewer of another vendor is the remedy — and again the only
  place to express "for this task, reviewer X" is an environment
  variable.
- In the same period the coordinator wrote the implementer choice into
  contract prose by hand **three times**, because otherwise a reader of
  the journal could not tell why the session log changes vendor halfway.

## Proposed

Declare the assignment in the contract header, next to `scope` and
`acceptance`:

- `implementer` — the primary actor and an ordered fallback list, each
  fallback with the condition that permits it: provider limit or quota
  exhausted, output truncated, N failed rounds;
- `reviewer` — the primary reviewer and its fallback list, with the same
  kind of conditions;
- an independence rule — for example that reviewer and implementer must
  differ by vendor, or by vendor and model — applying to the fallbacks
  too: a reviewer fallback that would share a vendor with the
  implementer of the candidate is not permitted, and the next one in the
  list is taken.

A switch to a fallback would be recorded by the tool rather than
inferred: `record-session` with an outcome naming the limit the failed
run hit, and the next session naming which fallback condition it used.
Limits are the most common reason for a switch in a multi-agent setup,
the reporter's measurements say. On the release the reporter observed
the tool had no outcome value for them; proposal 024 asked for the
provider stop to be recorded, and its `provider-limit` has been a
documented outcome since 0.4.1 — a stop on the output limit still has
none.

And for `gate` to check the recorded sessions and review against the
declared assignment: the review that makes the candidate mergeable must
come from a permitted reviewer and satisfy the independence rule against
the implementers whose commits are in the candidate. Changing the
assignment would be an amendment with a reason, like any other change to
the agreement — which the reporter notes is exactly the trace missing
today. `status` would show the declared assignment next to what actually
ran.

## Disposition — accepted

**The outcome values** — for a session that ended on a provider limit and
for one that ended on an output-limit truncation: the first is already
shipped, because `provider-limit` has been the documented outcome for a
session the provider refused to continue since 0.4.1 — the vocabulary
proposal 024 established — so an adopter can write it today. The second
is accepted on the same grounds: why a run stopped is the same kind of
fact as that refusal, and the journal should say it in words journals
share. Accepted; not shipped yet.

**The header fields, the gate checks and the `status` display** — the
declared assignment next to what actually ran is the read side of the same
declaration — are accepted together. Where the assignment lives is a
decision on the tool's boundary that is not yet made: the reporter's
header schema is on the table, and so are shapes that leave the contract
unchanged and declare the assignment elsewhere the gate can read. It is
the same contract-governance question the agreement record of proposal 031
waits on — what the contract should declare about who does and who checks
the work is one question with whether the agreement is recorded at all,
and it should be settled once. Accepted; not shipped yet.

## Where

`provider-limit` is already shipped, a documented outcome since 0.4.1;
the outcome value for an output-limit truncation is accepted, not shipped
yet. The header fields, the gate checks and the `status` display of the
declared assignment next to what ran are accepted, not shipped yet —
they go with the decision on the tool's boundary, and where the
assignment will live is undecided.
