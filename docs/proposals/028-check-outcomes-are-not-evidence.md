# 028 — Check outcomes are not evidence: a candidate can fail CI repeatedly and leave no trace

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:32dacfd47249e16b2ac1f76656f4ef7f585019a8f405d5bcbe58542920dd9bf7` · **Disposition:** accepted *(as a piece of work; deferred — it is a new record type)*

## Finding

The reporter's journal, forty governed tasks in, contains five record types
— `opened`, `amendment`, `session`, `review`, `completed` — of the nine the
vocabulary defines; the four that never appear (`acceptance`, `finding`,
`abandoned`, `reopened`) carry no check outcome either. None of the nine
describes what the code *does*: each records what someone *said* or *did*.
The required check is the one party in the loop that answers that question,
and the one the journal does not hear from. `gate` accepts
`--attestation commit`, under which the invoker attests a green pipeline on
the way to `completed`; a failing run leaves nothing — no record, no reason,
no count — and under `ci-required` the gate delegates the attestation to the
provider's required checks and records neither outcome. Run the same
candidate through CI three times, fail three times, and the journal is
byte-identical to a candidate that was never submitted.

Two consequences follow, and the reporter hit both in one task. The
implementer is not told why its work was rejected: `brief` assembles the
prompt from the contract, and on a re-run the reporter's wrapper adds the
reviewer's prose — because a review is a record and can be read back — but
there is no check record to read and no field in the brief to carry it, so
the implementer is handed an opinion and no facts. And nobody can later tell
that it happened: the cost of a rejected candidate is invisible in `report`.

Measurements, as reported — from the reporter's journal, 40 governed tasks:
record types present are exactly `opened`, `amendment`, `review`, `session`,
`completed`; no record type carries a check result. The task that made this
concrete (importing research data into the CMS):

- The candidate passed the reviewer twice and passed `gate` twice.
- Both times the required check failed in CI on the same assertion on one
  API endpoint, which returned 500.
- Both times the implementer's next round was driven by the reviewer's prose
  only. It fixed six advisory findings across the two rounds and never
  touched the defect, because it did not know the defect existed.
- The loop was broken by a human writing the CI error text into the contract
  by hand, as an acceptance criterion. The third round fixed it immediately.
- Cost of the gap: two implementation rounds, two reviews, two CI runs,
  roughly an hour.

The local mirror of the check has the same blind spot in the other
direction: the failing assertion needed a database, and the local run skips
it silently when there is none. So the implementer's own `checks: ok` was
true and useless — and nothing in the journal recorded that a check had been
skipped either.

## Proposed

Make a check outcome a record, and let `brief` read it:

- A `check` record, written by whatever runs the checks: task, commit,
  verdict, the step that failed, a truncated excerpt of its output, and
  whether any checks were skipped. Append-only, like everything else.
- `gate` already distinguishes attestations; the failing case should produce
  a record rather than nothing at all.
- `brief` gains the ability to include the latest failing `check` for the
  task, so a re-run prompt carries facts as well as opinion — truncation and
  secret-scanning belong in the tool, not in every adopter's wrapper.
- `report` counts rejected candidates alongside rounds and cost, so "how
  much did CI rejection cost us" becomes answerable.

## Disposition — accepted as a piece of work, deferred

Real, measured, and an asymmetry the journal should not carry: a pass can be
attested on the way to `completed`; a fail cannot be recorded anywhere — not
a record, not a count, not a line in `report`. A gate that can be told the
pipeline passed, in a journal that cannot show the pipeline ever ran and
refused, is not neutral about failure; it is silent about it.

It is also a new record type, and this project decides record types in an
architecture decision before it builds them. This one goes into
the review-evidentiality decision — where the `evidence` field
deferred in proposal 026 and the executed-versus-read field of proposal 030
already wait: what a record should say about how a claim was checked is one
question, and it should be answered once. Accepted; not shipped yet.
