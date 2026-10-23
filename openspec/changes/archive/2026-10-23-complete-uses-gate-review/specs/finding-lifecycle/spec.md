## MODIFIED Requirements

### Requirement: `complete` takes a disposition for each advisory finding of the review the gate passed on
`agentmarshal complete` SHALL take a repeatable `--disposition
<finding id>=<disposition>` — `<disposition>` one of `fixed`,
`deferred:<reason>` and `rejected:<reason>`, the reason everything
after the first colon, so it may contain colons — and a repeatable
`--follow-up <finding id>=<task>` naming a follow-up task for a
`deferred` finding. The review the gate passed on is the one its
verdict check judged — the approving latest review of the resolved
commit, or the non-approving one an acceptance covered — and the
gate's report SHALL carry its id: the same code that decides the
verdict check sets it, never recomputed, and the report carries none
when the gate passed on no review. `complete` SHALL take the advisory
findings that need a disposition from the review record carrying that
id, read from the records the gate evaluated — a review appended
after the gate ran carries a different id, so it cannot change which
advisory findings are owed — and SHALL write the answers into the
`completed` record's `advisory_dispositions` through
`create_completed_record`'s parameter: each reason landing as
`reason`, each `--follow-up` landing as `follow_up` on its finding's
entry. When the review carries no advisory findings the command SHALL
complete exactly as before: no flag needed, no field written.

#### Scenario: a completion answers each advisory finding of the approving review
- **WHEN** the approving latest review of the candidate carries
  advisory findings and `complete` is given a `--disposition` for each
- **THEN** the `completed` record's `advisory_dispositions` carries
  each finding's entry and the record is written

#### Scenario: a deferred disposition may name a follow-up task
- **WHEN** `complete` is given `--disposition F-1=deferred:<reason>`
  and `--follow-up F-1=<task>` for a deferred advisory finding
- **THEN** the finding's entry carries `follow_up` with that task

#### Scenario: a reason is everything after the first colon
- **WHEN** a `--disposition` reason itself contains colons
- **THEN** the recorded `reason` is everything after the value's first
  colon

#### Scenario: a fixed disposition may carry a reason
- **WHEN** `complete` is given `--disposition F-1=fixed:<reason>`
- **THEN** the finding's entry carries the reason, as the field admits
  a `reason` on `fixed`

#### Scenario: the review the gate passed on may be a non-approving review an acceptance covered
- **WHEN** the latest review of the candidate does not approve, an
  acceptance covers its blocking findings, and the review carries
  advisory findings
- **THEN** `complete` takes a disposition for each of that review's
  advisory findings, written into the `completed` record

#### Scenario: a review with no advisory findings completes as before
- **WHEN** the review the gate passed on carries no advisory findings
- **THEN** `complete` with no flags writes the `completed` record
  exactly as before, carrying no `advisory_dispositions`

#### Scenario: the gate's report carries the id of the approving review it passed on
- **WHEN** the gate's verdict check passes on the approving latest
  review of the resolved commit
- **THEN** the report carries that review's id, set by the same code
  that decided the verdict check

#### Scenario: the gate's report carries the id of the review an acceptance covered
- **WHEN** the gate passes on an acceptance covering the non-approving
  latest review of the resolved commit
- **THEN** the report carries that review's id

#### Scenario: the gate's report carries no review id when it passed on no review
- **WHEN** the gate passes having judged no review — a journal-only
  candidate, or a run asked to judge without one
- **THEN** the report carries no review id

#### Scenario: a review appended after the gate ran cannot change which advisory findings are owed
- **WHEN** a review of the candidate is appended after the gate ran —
  carrying no advisory findings, or different ones
- **THEN** `complete` still requires a disposition for each advisory
  finding of the review the gate passed on, refusing before it writes

#### Scenario: an advisory id raised only by a review appended after the gate refuses, naming the id
- **WHEN** a `--disposition` or `--follow-up` names an advisory
  finding only a review appended after the gate ran raised
- **THEN** `complete` refuses naming the id and writes nothing

#### Scenario: a completion after an appended review writes the passed-on review's dispositions
- **WHEN** a newer review is appended after the gate ran and each
  advisory finding of the review the gate passed on gets a
  `--disposition`
- **THEN** the `completed` record's `advisory_dispositions` carries
  that review's entries and the record is written
