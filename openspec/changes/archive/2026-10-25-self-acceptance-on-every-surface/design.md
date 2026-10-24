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

- **One shared comparison, three surfaces.**
  `_accepting_party_is_declared_writer` in `report.py` is the comparison
  `status_view._is_self_accepted` makes — the accepting party, stripped
  and case-folded, against the declared author and committer names and
  emails. The gate applies it over the candidate's commit range
  (`_range_writer_identities` reads `%an%n%ae%n%cn%n%ce` over
  `merge-base..candidate`, the same fields
  `_declared_commit_writers` reads for one commit); `report` and
  `status` apply it to the accepted commit. The reviewer-independence
  check keeps the emails-only `_range_emails` set — a name in it could
  only collide with a reviewer identity declared as an address.
- **`report` applies the shared comparison over the accepted commit.**
  `_self_accepted` looks the commit's declared writers up the way
  `status` does — `status_view._declared_commit_writers`, imported
  where it runs rather than copied: `status_view.py` imports `report`,
  so a module-level import back would cycle — in the repository the
  accepted commit lives in, the placement's host root, resolved the
  way `status` resolves it.
- **`report` marks a confirmed self-acceptance only.** Where the
  accepted commit's writers cannot be read — an absent commit, a
  shallow clone, a journal outside a readable project — the line
  prints as for any other acceptance, and `status` alone says the
  check could not run. A `self-acceptance-unchecked` field would break
  the byte-for-byte promise the capability makes for a
  non-self-acceptance line. The findings lane still prints no mark: an
  `accepted_finding` binding has no commit whose writers could be
  compared.
- **The decision binds to the completed record.** For a completed task
  the latest review of the `completed_commit` (or `completed_finding`)
  decides: `approved` wins, else a latest findings-carrying acceptance
  bound to it yields `accepted-over-findings` — and that acceptance is
  the one the mark derives from. A task with no `completed` record keeps
  today's rule: any findings-carrying acceptance reports
  `accepted-over-findings`, marked when its latest such acceptance is
  a self-acceptance.
- **An approval after an acceptance on the same commit reports
  `approved`.** `review(X, changes_required) → acceptance(X) →
  review(X, approved) → completed(X)` is a legal journal — records are
  admitted until a terminal one — and the completed commit's *latest*
  review approved: the task reports `decision=approved` and no mark.
  `accepted-over-findings` is for a completion whose commit's latest
  review is non-approving and an acceptance covers it; an acceptance
  standing on the same commit does not shadow the approval that
  actually closed it.
