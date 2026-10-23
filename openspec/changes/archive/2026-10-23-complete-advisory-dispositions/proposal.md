## Why

ADR-0016 decision 1: for the review the gate passed on — an approving
review, or the non-approving one an acceptance covered — `complete`
takes a disposition for each of that review's advisory findings and
refuses before writing `completed` when any lacks one. CR-175 landed
the field: `create_completed_record` accepts `advisory_dispositions`
and the record stamps schema 7 through the minimum-schema derivation.
Until now the coordinator has written these choices into commit
messages, because the command had no way to take them.

## What Changes

- `agentmarshal complete` takes repeatable `--disposition
  <id>=fixed`, `--disposition <id>=deferred:<reason>` and
  `--disposition <id>=rejected:<reason>` — the reason is everything
  after the first colon, so it may contain colons — and repeatable
  `--follow-up <id>=<task>` for a deferred finding; the answers land
  in the `completed` record's `advisory_dispositions` through
  `create_completed_record`'s existing parameter, on both commit lanes
  — the embedded `complete_task` and the sidecar's.
- For the review the gate passed on — the latest review of the
  resolved commit, the same one the gate's verdict check consults —
  `complete` refuses before writing `completed` when any of its
  advisory findings has no disposition, naming every unanswered id.
- It also refuses, writing nothing — a disposition or follow-up naming
  an id that is no advisory finding of that review (naming the id), a
  `deferred` or `rejected` without a reason, a follow-up on a
  disposition other than `deferred`, a malformed or repeated flag, and
  a value the record rules refuse, repeated naming the flag it came
  through.
- `complete --findings` takes no dispositions: the flags are refused
  there, and the lane gains no refusal for want of one (ADR-0016
  decision 1).
- A review carrying no advisory findings completes exactly as before
  with no flag and no field; `docs/quickstart.md` documents the flags.

## Capabilities

- modified: `finding-lifecycle`

## Impact

Only `complete` changes; no other command changes, and the gate's
fixtures and every documented transcript a test pins are unchanged —
a passing completion prints what it printed before. `status` and
`report` showing open deferrals are later tasks.
