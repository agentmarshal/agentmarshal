## Context

`complete` runs the gate itself and writes `completed` only on a
pass (`complete.py`). CR-192 made the command take a disposition for
each advisory finding of "the review the gate passed on" — but it
computes that review twice: once inside `run_gate`'s verdict check
(`reviews[-1]` of the resolved commit), and again inside
`record_commit_completion`, which re-reads the journal and takes
`reviews[-1]` a second time. Between the two reads a concurrent
process of the same user can append another review of the same
commit — records are append-only, so appending is always lawful —
and the second read then judges a different review. A newer review
with no advisory findings would let the completion write
`completed` while owing none of the dispositions of the review the
gate actually passed on — the advisory finding CR-192's own review
left, deferred with this task as its follow-up.

## Goals

- The review whose advisory findings need dispositions is the review
  the gate judged, by construction: `GateReport` carries its id, set
  by the same code that decides the verdict check — never recomputed
  — and `complete` reads that record's advisory findings among the
  records the gate evaluated.
- A review appended after the gate ran cannot change which advisory
  findings are owed; one naming a finding only the appended review
  raised is refused as unknown.
- Nothing the gate checks or prints changes — the id lives on the
  report object, so the pinned transcript and the fixtures stay byte
  for byte — and `complete --findings` is untouched.

## Non-Goals

- Locking the journal against concurrent writers — the fix removes
  the consequence, not the possibility, of an append between gate
  and write.
- Any change to what the gate checks or prints.
- Protection beyond the published decisions (docs/threat-model.md).

## Decisions

- **The report carries the id, set where the verdict is decided.**
  `run_gate` already knows which review it judged — `latest`, the
  same variable the verdict check consults on both pass paths
  (approving verdict, or an acceptance covering exactly its blocking
  findings). `resolved_review` is set there, not recomputed later:
  `latest["id"]` when the check passes on it, `None` when the gate
  passed on no review — the journal-only lane and the
  asked-to-judge-without-one mode — and on the findings lane, which
  judges no commit's review.
- **The record is found by id, among the records the gate evaluated.**
  `read_records` stamps each record with the id its filename carries,
  so `record_commit_completion` takes a `resolved_review` parameter
  and looks the record up by it. An appended review sorts later and
  carries a different id, so it can neither replace the judged review
  nor lend it advisory findings; a `--disposition` or `--follow-up`
  naming an id only a later review raised fails the existing
  unknown-id refusal. A missing pinned record — impossible under
  append-only, so only through tampering — refuses rather than
  silently owing nothing.
- **`resolved_review=None` is the gate's own "no review judged".**
  Every caller passes the report's field — `complete_task` in
  `complete.py`, and the sidecar `complete` in `cli.py` — so no path
  re-selects the latest review after the gate. `None` is what the
  verdict check left on the paths that judge no review — the
  journal-only lane, a run asked to judge without one — and owes no
  advisory dispositions; it is never re-derived into the latest
  review of the resolved commit, which is itself a selection a
  post-gate append could swap.
- *Correction 2026-10-23:* the bullet above first read
  "`resolved_review=None` keeps the pre-field derivation" — the
  sidecar `complete` called `record_commit_completion` from `cli.py`
  with no report field, a call this task's scope could not then
  change, so the latest review of the resolved commit was derived
  again and the sidecar lane kept the concurrent-append window.
  The contract amendment of the same date admitted `cli.py` to the
  scope; the sidecar call now passes `report.resolved_review` and
  the derivation is removed, not kept.

## Alternatives considered

**Carry the advisory findings on the report.** The criterion asks
for the id, and the record — not a copied list — is what the
disposition check should read: the id names evidence, the list
would be a snapshot of it.

**Re-derive "the review the gate passed on" in `complete` without the
id.** Any derivation that does not know which records existed at gate
time cannot tell the judged review from a later append — that is the
defect being fixed.

**Change `cli.py` to thread the report through.** Outside this
task's original scope, so it was first named as a follow-up — then
taken in this change after all: the 2026-10-23 contract amendment
admitted `cli.py`, and the alternative stopped being an
alternative.
