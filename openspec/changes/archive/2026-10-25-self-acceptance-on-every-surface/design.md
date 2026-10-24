## Context

`status` already derives the self-acceptance mark: an acceptance record
line appends ` self-accepted`, and its summary line carries
` (self-accepted: accepting party is a declared author or committer)`,
both derived on display by comparing `accepted_by` — stripped and
case-folded — against the accepted commit's declared author and
committer names and emails (`_declared_commit_writers` +
`_is_self_accepted` in `status_view.py`). The gate's acceptance line and
`report`'s task line do not mark it, although ADR-0007 decision 4 makes
the mark mandatory on every surface that reports the task
(AUD-gate-journal-5).

Separately, `report` derives `accepted-over-findings` from the existence
of any findings-carrying acceptance in the task — so a task whose
completed commit closed on an approving review still reports
`accepted-over-findings` whenever an earlier commit was accepted over
findings (AUD-gate-journal-4). ADR-0007 decision 5 wants the two told
apart.

## Goals

- The gate's acceptance line and `report`'s task line mark a
  self-acceptance in the terms `status` uses.
- `report`'s decision says how the completed commit actually closed:
  approval on the completed commit, or acceptance over its findings.
- A journal without a self-acceptance or an earlier-commit acceptance
  prints byte-for-byte what it prints today.

## Non-Goals

- Changing who may accept, or the gate's admission rules.
- `status` — it already marks.
- The findings lane's acceptance line: an `accepted_finding` binding has
  no candidate whose writers could be compared, and `status` carries no
  mark on one either.

## Decisions

- **The gate compares `accepted_by` against the writer emails it already
  reads.** The reviewer-independence check builds the candidate range's
  declared author and committer emails, stripped and case-folded; the
  acceptance line derives the mark from that same set, hoisted ahead of
  the verdict block so both read it once. The qualification names what
  the set is: `accepting party is a declared writer of the candidate`.
- **`report` derives the mark the way `status` does — by calling it.**
  `_self_accepted` in `report.py` delegates to
  `status_view._is_self_accepted`, imported where it runs rather than
  copied: `status_view.py` imports `report`, so a module-level import
  back would cycle. The comparison runs against the accepted commit's
  declared author and committer names and emails, in the repository
  the accepted commit lives in — the placement's host root, resolved
  the way `status` resolves it.
- **An unanswerable check is said on `report`, not hidden.** A commit
  git cannot read, or a journal outside a readable project, marks the
  task line `self-acceptance-unchecked` — the tri-state `status` uses —
  rather than a line indistinguishable from "not self-accepted". The
  findings lane still prints no mark: an `accepted_finding` binding has
  no commit whose writers could be compared.
- **The decision binds to the completed record.** For a completed task
  the latest review of the `completed_commit` (or `completed_finding`)
  decides: `approved` wins, else a latest findings-carrying acceptance
  bound to it yields `accepted-over-findings` — and that acceptance is
  the one the mark derives from. A task with no `completed` record keeps
  today's rule: any findings-carrying acceptance reports
  `accepted-over-findings`, marked when its latest such acceptance is
  a self-acceptance.
