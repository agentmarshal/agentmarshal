## Why

ADR-0016 decision 1 binds the dispositions to "the review the gate
passed on", and CR-192's review deferred the gap as an advisory
finding: `complete` re-reads the latest review after the gate
returns, so a review appended concurrently — by a process of the
same user — could replace the one the gate passed on, and a newer
review with no advisory findings could let a completion skip the
dispositions of the review that was actually judged.

## What Changes

- `GateReport` carries `resolved_review`: the id of the review the
  gate's verdict check passed on — the approving latest review of the
  resolved commit, or the non-approving one an acceptance covered —
  set by the same code that decides the verdict, and none when the
  gate passed on no review.
- `complete` reads the advisory findings needing a disposition from
  the review record carrying that id, among the records the gate
  evaluated: a review appended after the gate ran names a different
  id and cannot change which are owed. A `--disposition` or
  `--follow-up` naming an advisory finding only a later review
  raised is refused, naming the id.
- A caller that cannot name the review — the sidecar `complete`,
  whose call predates the field — derives it as the verdict check
  does: the latest review of the resolved commit.
- Nothing the gate checks or prints changes: the id lives on the
  report object, the printed transcript stays byte for byte what the
  pinned fixtures demonstrate, and `complete --findings` is
  untouched.

## Capabilities

- modified: `finding-lifecycle`

## Impact

Only `gate.py` and `complete.py` change. The gate's transcript and
every fixture stay identical — the new field is on the report
object, not a printed line — and no other command changes.
