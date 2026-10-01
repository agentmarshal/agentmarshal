# 030 — A verdict does not say what the reviewer executed and what it only read

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 for the mechanism and 0.3.0 for the historical measurements · **Source:** `sha256:100633253ea653cd4523320fb9c4ff5cf096ea20cbe1d402ad0574855b15aed3` · **Disposition:** deferred

## Finding

`review` runs the reviewer command against a snapshot of the candidate tree
made with `git archive`. The snapshot is not a git repository and carries no
installed dependencies — for a typical application project that means no
compiler, no linter and no test runner. Acceptance criteria routinely end
with a line of the form "the type check, the linter and the test suite
pass", so the reviewer is asked to confirm a claim it has no way to execute,
and does what a careful reader can: it reasons from the code and from the
language's rules.

The verdict it then records does not distinguish the two kinds of
confirmation. A criterion verified by running the suite and a criterion
verified by reading the source produce the same word; `gate` reads that word
and `report` counts rounds and cost, and neither can tell that the strongest
claim in the review was never executed by anyone. Reviewers are usually
honest about it in prose — but prose is not a record, so the distinction
survives only as long as a human happens to read that paragraph.

Measurements, as reported — 114 review artifacts from the reporter's
journal:

- In **12** the reviewer states, in its own words, that it could not run the
  checks: "could not execute", "verified by reading", "I could not run the
  suite", "the conclusion is static". This is a lower bound — a review that
  silently skipped execution would not say so.
- **Two blocking findings, in two different tasks four days apart, both
  asserted that the project's type check would fail. Both were reasoned from
  the compiler's rules because the snapshot had no installed dependencies.
  Both were false: the type checker passed when actually run**, on the exact
  code the review described.
  - The first cost a full round. The verdict was `changes_required`, the
    implementer changed working code to satisfy a defect that did not exist,
    and a second review followed.
  - The second cost nothing, but only because the coordinator ran the type
    checker by hand before acting on the verdict — strict mode, exit 0 —
    and then had to argue with a recorded blocking finding on the strength
    of a measurement the journal has no place for.
- Several of the same reviews resolve the gap by saying the criterion "rests
  on the CI run" — handing the claim to the one party the journal does not
  hear from either, which is the subject of proposal 028.

The failure is not rare, not random, and not the reviewer's carelessness: it
is structural. The tool builds an environment in which a whole class of
criteria cannot be checked, and then records the result as if it had been.

## Proposed

- A field on the review record for what was confirmed by execution and what
  by reading — the reviewer states it in prose today; moving it into the
  verdict protocol costs one line.
- `gate` need not refuse on it; it is enough that `status` and `report` can
  answer "were this candidate's check-related criteria ever executed by
  anyone" — together with a record for check outcomes, one side says what
  was run and the other what was only read.
- Optionally, an adopter-declared preparation command for the snapshot, so
  execution becomes possible where the adopter wants it and pays for it.

## Disposition — accepted as a piece of work, deferred

Two false blocking findings in a hundred-odd reviews is not carelessness; it
is the environment doing exactly what it was built to do, and the record
being unable to say so. Both are legitimate work — but only one is evidence
about behaviour, and a merge gate that cannot tell them apart is weaker than
it looks.

The field is accepted, into the review-evidentiality decision — the same
decision the `evidence` field deferred in proposal 026 and the `check`
record of proposal 028 wait on. What a record should say about how a claim
was checked is one question, and it should be answered once rather than one
field at a time. Accepted; not shipped yet.

## Where

Deferred, and nothing here is shipped yet. The executed-versus-read field
waits on the review-evidentiality decision — with the `evidence` field of
proposal 026 and the `check` record of proposal 028.
