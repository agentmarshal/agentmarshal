## Context

[ADR-0016](../../../../docs/adr/ADR-0016-the-lifecycle-of-review-findings.md)
decision 4: the gate's output gains a line carrying the task's count of
`changes_required` verdicts — over the whole task, unlike `next`'s count
since the latest amendment ([ADR-0023](../../../../docs/adr/ADR-0023-next-the-next-step-of-a-task.md)
decision B) — flagged when the count reaches the project's threshold. The
threshold is `review.changes_required_threshold` (default 3), which CR-151
made readable through `agentmarshal.settings`
(`changes_required_threshold(project_root)`). The line lands inside the
transcript that gate-lanes' "A default run is unchanged" pins by fixtures
(CR-146): this task is the deliberate output change that requirement
already provides for, and the fixture diff it produces — exactly the new
line — is the naming that requirement asks for.

## Goals

- Whoever reads the gate's output sees how many times the task was
  returned, and sees it marked when the count has reached the threshold.
- The line is a report, never a verdict: no violation, no exit-status
  change, no refused merge — in either placement.
- The pinned transcript stays exact: only the implementation-lane
  fixtures change, through `AGENTMARSHAL_UPDATE_GATE_FIXTURES` and
  `test_regenerate_the_committed_fixtures`, and their diff is the one new
  line.

## Non-Goals

- The count in `status` — a separate task under the same decision.
- Counting since the latest contract amendment — `next`'s count
  (ADR-0023); the gate and `status` count over the whole task.
- The findings lane (`run_findings_gate`) — the line is the
  implementation lane's.
- Reading the threshold from the merge-base tree. The settings module is
  a working-tree reader; making a trusted-tree variant of it is not this
  task's (see Decisions).

## Decisions

- **The line and its position.** `run_gate` ends the implementation
  lane's transcript with one `say` line, the last transcript line before
  the verdict line, so a marked count is the final thing read. The
  wording is:

  - below the threshold:
    `INFO: changes_required verdicts for <task>: <count> (threshold <n>)`
  - the count has reached the threshold:
    `WARN: changes_required verdicts for <task>: <count> (threshold <n>
    reached — stop and revisit the contract)`
  - the threshold cannot be read:
    `WARN: changes_required verdicts for <task>: <count> (threshold
    unreadable: <error>)`

  `INFO` is a new status word for the transcript — the line is a
  measurement, not a check, and must not read as `PASS`. `WARN` is the
  transcript's existing advisory marker: at the threshold the flag is
  the prefix, and a threshold that cannot be read is the same kind of
  advisory anomaly as a skipped leak-scan. Every interpolated value is
  an integer, the task id, or a caught error's text — the line is the
  tool's own text, and `say` escapes what it is handed regardless.

- **The count is over the task, not the commit.** It counts every record
  of the task whose `record_type` is `review` and whose `verdict` is
  `changes_required`, whatever `reviewed_commit` it names — the record
  set `load_task_status` already validated into `task.records`, so the
  line adds no read of its own. A review of an older commit counts; a
  review's other verdicts do not.

- **The threshold is read through the settings module.**
  `changes_required_threshold(journal_root.parents[1])` — the journal
  repository's `project.json`, which is `project_root` in the embedded
  placement and the sidecar's root in a sidecar, the same resolution
  `markers_from_config` uses there. Unlike the contract or the
  leak-scan markers the read is from the working tree, not the
  merge-base tree: CR-151's reader is a working-tree reader, and the
  line is advisory — a candidate that edits `project.json` to raise its
  own threshold makes that edit inside its reviewed diff, not in secret.

- **An unreadable threshold is reported on the line.** The settings read
  is wrapped in `(OSError, ValueError)` — `ProjectSettingsError` is a
  `ValueError` — so a malformed key, a malformed section or an
  unparseable `project.json` lands on the line as `threshold unreadable`
  with the error's message, and the count still prints. The line never
  reaches `check`: it cannot add a violation.

- **The journal-only lane prints no line.** The deterministic lane
  carries no work to review, so no count. The guard is the lane
  decision itself (`journal_only`), not a new flag — in a sidecar the
  lane does not exist and every run is the implementation lane.

- **"A default run is unchanged" is not reworded.** The requirement pins
  the run's transcript to the committed fixtures and already says a task
  that changes the output on purpose regenerates them and names the
  change in its diff — which is what this task does. Its text stays
  true; this change is an ADDED requirement alongside it, not a
  MODIFIED one.

## Risks

- [The new `INFO` prefix reads as a new kind of transcript line] →
  intentional: the line is a measurement, and a status word the check
  vocabulary does not have keeps it from reading as a pass or a
  refusal.
- [A candidate could raise its own threshold and hide the mark] → the
  line is advisory and decides nothing; the `project.json` edit is in
  the reviewed diff, and the count it would have hidden still prints.
- [A run-dependent value in the line breaks the fixture pin] → the line
  carries only the task id, two integers and (on failure) an error the
  settings module worded; nothing in it varies between runs.
