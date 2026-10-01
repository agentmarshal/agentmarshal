# 036 — Review accepts a candidate the implementer did not finish, and gate accepts its approval

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 and 0.4.0 · **Source:** `sha256:49f2af2b806086043d0495fcc7c3a3a4559d3a7df5c1eed92ee5ddca21a253be` · **Disposition:** accepted

## Finding

An implementer run can end before the work is done: the provider's usage
limit, an output-token limit, a crash, a timeout. Whatever it wrote by
then is still a commit, and nothing in the tool distinguishes it from a
finished candidate. `review` takes any commit, and the reviewer judges a
half-written change against the full contract. `gate` checks that the
latest review is `approved` and that the reviewer differs from the
commit's authors; it does not check how the implementation session that
produced the candidate ended.

`record-session` takes a free-text outcome, so the journal can say that a
run failed. But the session record carries no commit — it stores role,
actor, activity, outcome and token counts — so neither `review` nor
`gate` can connect the failed session to the candidate under review.

Measurements, as reported — from 300 reviews over 117 tasks, **7**
reviewed a commit the reporter's wrapper had explicitly marked as
unfinished in the commit subject, written when the implementer exited
with an error:

- **4** came back `changes_required`, with findings that amounted to
  "this is not finished" — a paid review round spent on stating the
  obvious;
- **3** came back `approved` — an unfinished candidate accepted as
  meeting the contract. In those cases the work happened to be complete
  enough, but the tool gave no signal that it was an interrupted run.

The reporter's wrapper was later changed to skip review after a failed
run. The same defect came back through a second path: a benchmarking
script of theirs that reused the review step reviewed a candidate whose
implementer had stopped on a provider usage limit mid-edit — the
candidate did not compile, and the reviewer again reported the missing
work as defects. Every new launcher has to reimplement the rule, because
the tool does not hold it.

## Proposed

Whether a candidate is finished is a fact about how its implementation
session ended, and the journal already records sessions:

- `record-session` for the implementer accepts the commit the session
  produced — a `commit` field on the record — and outcome values that
  name why a run stopped early: `failed`, a provider-limit outcome of the
  kind proposal 024's vocabulary names, and one for an output-token
  truncation;
- `review` refuses — or requires an explicit override with a reason —
  when the latest implementer session recorded for the reviewed commit
  did not end as `implemented`;
- `gate` refuses an `approved` review of a commit whose producing session
  is recorded as not finished, unless the operator records an acceptance
  for it, as `accept` does for findings today;
- `status` shows, for the candidate head, which session produced it and
  how that session ended.

The reporter relates it to proposal 024, where the same limit has no
outcome value, and to proposal 034, where the same stop is what a
fallback switch is made of.

## Disposition — accepted

The chain the reporter describes is real at each link: the session record
cannot name its commit, so no later step can know the run was
interrupted; the reviewer then prices "this is not finished" at a full
round; and the gate's approval check never asked. All three follow the
records.

The `commit` field on the implementer's session record is accepted — it
is the link the rest needs, and it turns a wrapper's commit-subject
convention into evidence. With it, `review` and the gate refuse a
candidate whose producing session did not end `implemented`; the shape of
the operator's way through — the explicit override or the recorded
acceptance the reporter proposed — is part of that work. When no session
names the commit, behaviour is as today: a candidate produced by a runner
that wrote no session is judged as it is now. Accepted; not shipped yet.

## Where

Nothing here is shipped yet. The `commit` field on the implementer's
session record and the refusal in `review` and `gate` are accepted; the
release that carries them will say so in its changelog.
