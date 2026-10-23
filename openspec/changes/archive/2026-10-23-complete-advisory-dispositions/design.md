## Context

`complete` runs the gate itself and writes the `completed` record only
on a pass (`complete.py`); the sidecar placement repeats the same two
steps inline in the CLI. The gate's verdict check consults the latest
review of the resolved commit — `reviews[-1]` — passing on an
`approved` verdict or on an acceptance covering that review's blocking
findings (ADR-0007). CR-175 gave the `completed` record the
`advisory_dispositions` field and `create_completed_record` its
parameter; nothing supplied it until now, so the coordinator's
dispositions have been going into commit messages, outside the
evidence.

## Goals

- Every advisory finding of the review the gate passed on ends in a
  recorded choice — `fixed`; `deferred`, with a reason and optionally
  a follow-up task; `rejected`, with a reason — written into the
  `completed` record's `advisory_dispositions`.
- The check and every refusal sit in `complete` itself, at write time
  — the point where the coordinator can still supply the answers — and
  each writes nothing.
- A review carrying no advisory findings completes exactly as before;
  the findings lane is untouched.

## Non-Goals

- `status` and `report` showing open deferrals — later tasks.
- A review-by date on a deferral — pending an operator decision.
- Changing what the gate checks — the gate's fixtures and every pinned
  transcript are unchanged; the new check lives in `complete`, after
  the gate passes.
- Displaying or verifying dispositions beyond writing the field.

## Decisions

- **The review the gate passed on is the gate's own `latest`.** The
  advisory set is read from `reviews[-1]` of the resolved commit — the
  same record the gate's verdict check consults, approving or covered
  by an acceptance — never re-derived a different way, so the two can
  never disagree about which review's advisories are owed.
- **One writer for both commit lanes.** `record_commit_completion`
  resolves the advisory ids from the journal, checks the flags against
  them, then builds and writes the record through
  `create_completed_record`'s `advisory_dispositions` parameter;
  `complete_task` calls it after `run_gate` passes, and the sidecar's
  inline lane calls it the same way — the embedded and sidecar
  placements cannot drift on the rule.
- **The flags are parsed into the field's own shape.** `--disposition
  <id>=<word>[:<reason>]` splits on the first `=` and then the first
  `:`, so a reason may contain colons; `fixed:<reason>` is admitted
  because the field admits a `reason` on `fixed`. `--follow-up
  <id>=<task>` lands as `follow_up` on its finding's entry. A value
  with no `=`, an empty id, an empty task or an id given twice is a
  malformed-flag refusal naming the flag; everything else goes to the
  record unchanged.
- **Record-rule refusals are repeated flag-named.** The entries reach
  `create_completed_record` and `write_record` as given; a
  `JournalRecordError` they raise — a word outside the vocabulary, a
  `deferred`/`rejected` without a `reason`, a `follow_up` on a
  non-`deferred`, a `follow_up` that is not a task id, a string that
  could forge a line — is re-raised naming the flag it came through
  (`--follow-up` where the message names `follow_up`, else
  `--disposition`), the record's own message still naming the finding
  id and the key at fault. The refusal lands at validation, before the
  write — nothing is written.
- **Unknown before missing.** A `--disposition` or `--follow-up` id
  that is not an advisory finding of that review is refused first,
  naming each such id — a stray id is usually a mistyped one and its
  correction also answers the missing check, which follows by naming
  every advisory finding left unanswered.
- **No flag, no field.** When the review carries no advisory findings
  the field is omitted — an empty object is a record refusal, not a
  spelling of "none" — and the record is byte-for-byte today's.
- **`--findings` refuses the flags.** The findings lane takes no
  dispositions (ADR-0016 decision 1): a `--disposition` or
  `--follow-up` there is a usage error, and the lane gains no refusal
  for want of one.

## Risks

- [The advisory set and the gate's verdict drift apart] → both read
  `reviews[-1]` of the resolved commit from the same journal, so they
  cannot disagree — a review landing between the gate run and the
  write would make the disposition check stricter, never weaker.
- [A flag echo forges a line on stderr] → every user value a refusal
  interpolates goes through `escape_for_display`, the record's own
  messages having `repr`ed the id already.
- [A disposition answered for a review the gate did not pass on] → the
  check runs only after `report.passed`, against the commit the gate
  resolved — a refusal before that is the gate's own.
