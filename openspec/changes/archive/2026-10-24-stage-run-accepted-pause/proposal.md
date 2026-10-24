## Why

[ADR-0013](../../../../docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
decision 5: an extension's stop is a pause of the process before the
gate, and sorting it out — a fix in a new round, or operator acceptance —
does not touch the gate; the merge happens when the gate has passed and
no pause stands. CR-215 gave the operator the recording half —
`accept --task --commit --pause <extension>` writes an acceptance
carrying `accepted_pause: {extension}` bound by `accepted_commit`
([ADR-0022](../../../../docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md)
section 2). `stage run` still pauses (exit 3) on every failed,
unfinished or not-run `pre-gate-stop` stage and reads no acceptance, so
a pause the operator has already stood behind blocks the process again.

## What Changes

- `stage run --phase pre-gate` reads the task's records through the
  journal's record reader, from the journal the placement names. For a
  `pre-gate-stop` stage that failed, did not finish or did not run it
  looks for an `acceptance` record carrying `accepted_pause` naming
  that extension and `accepted_commit` equal to the commit the run
  resolved.
- With one, the stage's result line keeps its outcome and adds
  `pause accepted by <party> (<reason>)` — the record's `accepted_by`
  and `reason`, escaped for display — and the stage does not pause;
  when no other stage pauses the command exits 0. The stage's
  `extension-event` keeps its decision and its reason names the
  acceptance record.
- An acceptance bound to another commit, naming another extension or of
  another form (over findings, `operational`) does not count. A
  switched-off stage, a `pre-gate-warn` stage, a `post-gate` stage and
  a checked stage are unchanged — a checked stage never mentions an
  acceptance.
- A journal that cannot be read is named on one stderr line and every
  pause stands — the fallback never lifts one.

## Capabilities

- modified: `extension-stages`

## Impact

One function's run loop and one event writer: `stages.py`'s
`_run_stages` gains a lazy acceptance read through `read_records`, and
the pause bookkeeping honours it. The gate reads no acceptance of this
form and is untouched — ADR-0013 decision 5: sorting out a pause does
not touch the gate. `accept` and every other command are unchanged.
