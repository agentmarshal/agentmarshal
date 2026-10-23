## Context

`run_gate` in `src/agentmarshal/journal/gate.py` reads the contract from
the trusted side — the merge-base tree in the embedded placement, the
sidecar working tree in the other — and reads project settings from the
journal repository's `project.json`: the `changes_required` threshold
(CR-168) comes through `agentmarshal.settings`, a working-tree reader
whose unreadable value the gate already reports on a WARN line.
`agentmarshal.settings.require_agreement` reads `contract.require_agreement`
(default false, ADR-0022 section 6); `contract_sha256` (CR-163) is the
one way a contract is hashed; CR-177 and CR-180 landed the `agreement`
record and the `agree` command that pins the contract's current hash.

## Goals

- A project that turns `contract.require_agreement` on gets the
  agreement enforced at the merge boundary, bound to the exact contract
  text the gate judges against.
- The line and the refusal are honest: a FAIL names the judged hash and
  how agreement is recorded; an agreement at another hash is named for
  what it is; an unreadable setting is reported, never silently skipped.
- With the setting off — the default — nothing changes: the pinned
  default transcript stays byte for byte.

## Non-Goals

- Roles or any rule about who may agree (ADR-0018 decision 2).
- Membership in the contract's `reviewers` list — a later task, after an
  operator decision.
- The deterministic (journal-only) lane and the findings lane: no
  contract is judged there, so no agreement line prints — and requiring
  an agreement on the lane that lands the agreement transaction itself
  would be circular.
- Reading the setting from the merge-base tree. The settings module is
  a working-tree reader; making a trusted-tree variant of it is not
  this task's (see Decisions).

## Decisions

- **One check line on the implementation lane, after the scope line.**
  The contract the gate judges against is loaded there, so the line
  stands at the first place the judged hash is meaningful — before the
  review checks that consume different evidence. The deterministic lane
  judges no contract and prints nothing new.

- **The judged hash is the trusted side's, computed the one way.** In
  the embedded placement it is `contract_sha256` over the same
  merge-base `contract_text` `parse_contract_text` just parsed for the
  scope check — a candidate's own contract edit moves nothing. In a
  sidecar the journal repository's `tasks/<id>/contract.md` is hashed —
  the copy `task.contract` was parsed from, the one `amend` pins and
  `agree` reads; a file that cannot be read or hashed is a `GateError`,
  the same refusal an unreadable base-tree contract gets. In the
  embedded case the text decoded as UTF-8 on the way in, so re-encoding
  it is exact, and `contract_sha256` normalizes CRLF the way text
  reading does.

- **Existential satisfaction, latest named on failure.** The check is
  whether the task's records — the ones `load_task_status` projected
  from the journal repository's working tree, the same records `agree`
  appends to — hold an `agreement` whose `contract` equals the hash:
  any one carrying it satisfies, wherever it stands and whoever
  recorded it (ADR-0018 decision 2: any declared actor may agree, and a
  recorder that is not a declared actor is accepted — `recorded_by` is
  shown, never judged). When none carries it the FAIL line names the
  *latest* `agreement` record's hash — the same record `status`
  compares for its earlier-text line.

- **The setting's read mirrors the threshold's.**
  `require_agreement(journal_root.parents[1])` — the journal
  repository's `project.json`, the working tree in either placement. A
  candidate that edits `project.json` to switch the requirement off
  makes that edit inside its reviewed diff, not in secret — the
  threshold's reasoning, restated for a boolean. An unreadable setting
  prints `WARN: agreement with the contract not examined
  (contract.require_agreement unreadable: <error>)` — the line's own
  counterpart to `(threshold unreadable: <error>)` — and adds no
  violation.

- **Not review-bound.** `review_required` governs the review checks;
  the agreement check binds the contract and runs however the run was
  asked — a provider CI run on a head no review can name still gets the
  requirement enforced.

- **Line wording.** `PASS: agreement recorded for contract <hash7>`;
  `FAIL: no agreement recorded for contract <hash7>; record agreement
  with 'agentmarshal agree'`; `FAIL: an agreement exists for another
  hash (<other7>), not for the judged contract <hash7>; record
  agreement with 'agentmarshal agree'`. The short hash is the field's
  own seven-character form, as `status` renders it. Every value the
  line interpolates is hex or the tool's own text; `say` escapes
  regardless.

## Risks

- [The check reads records, not intentions — a task could hold a stale
  agreement and still look agreed] → the hash comparison makes "agreed"
  mean "agreed with this text"; an agreement at another hash is named
  as such on the FAIL line rather than read as agreement.
- [A project turns the setting on and every merge fails until an
  agreement exists] → the FAIL says `agentmarshal agree` records it;
  the record is written to the same journal working tree the gate
  reads, so it precedes the merge the way a review does.
