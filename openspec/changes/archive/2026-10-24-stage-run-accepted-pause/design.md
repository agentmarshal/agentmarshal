## Context

ADR-0013 decision 5: an extension's stop is a pause of the process
before the gate; sorting it out — a fix in a new round, or operator
acceptance — does not touch the gate; the merge happens when the gate
has passed and no pause stands. The acceptance is the first of two
extensions of ADR-0007: a pause raises no review finding, so the
acceptance stands over the pause itself. CR-215's
`accept --task --commit --pause <extension>` writes it —
`accepted_pause: {extension}` bound by `accepted_commit` (ADR-0022
section 2). CR-211's `stage run` pauses — exit 3 — on a failed,
unfinished or not-run `pre-gate-stop` stage and reads no acceptance.

The pieces the run composes all exist: `read_records` (records.py) is
the journal's own reader — the records come back schema-validated, so
an acceptance's `accepted_pause`, `accepted_commit`, `accepted_by` and
`reason` arrive in their guaranteed shapes, and a journal that cannot
be read raises rather than misreads; `placement.journal_root` names the
journal in the embedded placement (a sidecar never reaches this point —
it is refused before any stage is planned); and `_run_stages`' pause
bookkeeping already knows the decision every pause stands on.

## Goals

- A `pre-gate-stop` stage that failed, did not finish or did not run
  stands down its pause when an `acceptance` record carries
  `accepted_pause` for the stage's extension bound by `accepted_commit`
  to the commit the run resolved; the result line keeps its outcome and
  names who accepted and why.
- The stage's `extension-event` keeps its decision and its reason names
  the acceptance record.
- A journal that cannot be read is named once and every pause stands —
  no fallback lifts one.
- The gate, `accept` and every other command are untouched.

## Non-Goals

- The gate reading pause acceptances — the merge still wants the gate
  passed and no pause standing; what stands down is the pause, nothing
  else.
- `post-gate` results consulting acceptances — a notification mode has
  no pause to stand down.
- Any relaxation of the pause for a stage the acceptance does not name.

## Decisions

- **The read is lazy and goes through `read_records`.** The acceptance
  records are needed only when a `pre-gate-stop` stage's decision is
  `failed`, `did-not-finish` or `not-run`, so the journal is opened at
  the first such stage and never by a run that pauses nothing —
  `post-gate` and all-checking runs open nothing new. `read_records`
  is the loader the task names: the records arrive validated (a
  malformed record raises before it can masquerade as an acceptance),
  and the alternative `load_task_status` would add a contract read and
  an opened-record requirement the pause does not need — a task with no
  records directory is simply a task holding no acceptance. The result
  is cached for the run the way the isolation probe is.
- **A journal that cannot be read answers "no acceptance".** The read
  is tried once; a refusal — `JournalRecordError`, an `OSError`, any
  `ValueError` the validation layer can raise — is named on one stderr
  line naming the journal and is not retried. The stage's result line
  is still owed and still printed; the pause bookkeeping then sees no
  acceptance, so every pause stands. A fallback that lifted a pause on
  an unreadable journal would be the one silent weakening this feature
  must not have.
- **The match is the record's own fields.** `record_type` is
  `acceptance`, `accepted_pause.extension` equals the stage's
  extension, `accepted_commit` equals the resolved candidate — the same
  string `AGENTMARSHAL_COMMIT` carries. A findings or operational
  acceptance carries no `accepted_pause` and cannot match; an
  acceptance for another extension or another commit cannot either.
  Journal order is path order, so the latest match is the last — the
  operator's most recent word is the one named.
- **The result line keeps its outcome and adds the suffix.** `,
  pause accepted by <party> (<reason>)` after `failed (exit 2)` /
  `did not finish (timeout)` / `not run (<reason>)` — the pause line
  itself (`the process is paused before the gate — <entry>`) is not
  printed for the stage. `accepted_by` and `reason` pass through
  `escape_for_display` the way `status_view` renders them.
- **The event keeps its decision and names the record.** The
  `extension-event` decision is what it is today (`failed`,
  `did-not-finish`, `not-run`); the reason appends
  `; pause accepted by acceptance record <id>` — the record's id as
  `read_records` yields it — so a reader of the log can trace the
  lift to the evidence. The outcome's own reason stays ahead of the
  clause; an empty reason would leave the clause alone.
- **Nothing else consults it.** `checked` and `switched-off` stages
  never pause and never look; `pre-gate-warn` warns and `post-gate`
  notifies exactly as before; the operational lane still returns before
  any stage is planned; a workstation's unreadable trust file still
  ends the command at 1 without a stage consulted.

## Risks

- [An acceptance for a near-miss lifting a pause] → the match is on the
  resolved full 40-hex commit and the extension's exact name, both
  validated by the record layer before they reach the comparison.
- [A silent lift on an unreadable journal] → the fallback returns no
  acceptance and the pause stands; the refusal is named once on stderr.
- [The pause output arriving where the acceptance line is owed] → the
  suffix is computed before the result line prints and the `paused`
  entry is skipped only for the matched stage, so every owed line is
  still emitted.
- [A second parser drifting from the record rules] → the read is
  `read_records` itself; validation is the journal's own.
