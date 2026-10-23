## Context

`src/agentmarshal/journal/review.py` builds the reviewer prompt, runs the
reviewer command in a metadata-free snapshot, parses the verdict block it
prints and hands the record to `submit_review`. `submit_review`'s
parameters are the human path's contract — the task forbids growing them —
so the launcher's tail writes the record itself, mirroring
`submit_review`'s load-check-record-write sequence and carrying the two
fields only a launch supplies: `previous_review`, read from the task's
records before the reviewer runs, and `classes`, normalized from the
verdict against the project's vocabulary.

## Goals

- A launched review names the task's previous review in both bindings —
  commit and finding — and carries no link on a task's first review.
- The verdict protocol admits `classes`; the prompt lists the configured
  vocabulary and asks for one class per reported finding id.
- A class the vocabulary does not know records as `other` with a warning;
  markup the record could not hold is dropped with a warning; no class
  refuses a paid verdict.
- `submit-review`, the gate's fixtures and every other command stay as
  they are.

## Non-Goals

- Showing the reviewer the previous round's findings — a separate mode
  per ADR-0016 decision 2.
- `status`/`report` surfacing of `previous_review` or `classes`, and the
  gate's use of either — later tasks.
- New flags or fields on `submit-review`, or any change to what a human
  submits.

## Decisions

- **Read the link before the reviewer runs.** `launch_review` and
  `_launch_finding_review` already load the task's records ahead of the
  run — `previous_review` is the latest `record_type == "review"` record
  id in that snapshot. A writer landing mid-run produces a later record,
  never the one just launched, so no review can link to itself.
- **Parse `classes` raw; normalize after the subject check.**
  `_parse_verdict` keeps rejecting what the verdict contract rejects —
  unknown keys included — while `classes` becomes an optional key whose
  value passes through unvalidated. After the reviewed-subject check the
  launcher maps each entry — an id among `findings`/`advisory_findings`
  records its class, `other` with a warning when the vocabulary does not
  hold it — and then completes the mapping: an id the verdict reports
  but `classes` names no class for records `other` with a warning naming
  the id. The requirement is a `classes` entry for *each* reported id,
  so a partial mapping kept silently loses the omissions; `other` is the
  honest record of "no usable class given". An id the verdict does not
  carry drops with a warning. A `classes` that is not an object, is
  empty, or holds a value which is no usable class string drops whole
  with a warning: the class is reference markup that decides nothing,
  so the verdict stands.
- **The tail writes the launched record itself.** `submit_review` cannot
  take the two fields, so `_launch_review_tail` runs the same sequence —
  load the task, build the record, pin the prose before the write when
  the policy keeps it, validate, write — through
  `create_review_record(previous_review=..., classes=...)`. The record
  layer's own validation remains the last word.
- **One vocabulary read per launch.** `review.finding_classes` comes from
  the journal repository's project file — the same file the actor
  legibility check reads — so a sidecar journal prompts and normalizes
  against the sidecar's vocabulary; a malformed vocabulary refuses before
  the reviewer runs, the prompt being unbuildable without it.

## Risks

- A class string that could forge a rendered line would reach `report`
  unsanitized — an empty or forgeable value therefore drops the whole
  `classes` object before the record layer can refuse it.
- A verdict naming classes for ids it does not carry could confuse a
  reader — such entries are dropped, and the warning names the id and the
  class given.
