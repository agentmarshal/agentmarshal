## Why

[ADR-0016](../../../../docs/adr/ADR-0016-the-lifecycle-of-review-findings.md)
decision 4: `status` shows the task's count of `changes_required` verdicts,
and the gate's output gains a line carrying the same count, flagged when it
reaches the project's threshold (default 3). It blocks nothing — it is the
signal to stop and revisit the contract that a person today has to notice
unaided. This change is the gate line; the `status` count is a separate
task.

## What Changes

- On the implementation lane — in the embedded placement and in a sidecar —
  a gate run prints one line carrying the task's count of
  `changes_required` review verdicts over the whole task (every review
  record of the task's candidates, whatever commit it names; a review
  bound to a research finding, ADR-0009, is not counted) and the project's
  `review.changes_required_threshold` (default 3), read through the
  project settings module. When the count has reached the threshold the
  line is marked.
- The line reports; it decides nothing. It adds no violation, changes no
  exit status and refuses no merge. A threshold setting that cannot be
  read is named on the line and does not fail the run.
- The journal-only lane's transcript carries no count line.
- The gate-lanes spec gains a requirement for the line. Its
  default-run requirement already pins the transcript by committed
  fixtures and already provides for a deliberate change, so its text
  stands; this task regenerates the implementation-lane fixtures through
  the test's explicit update path, and the fixture diff — exactly the new
  line — is part of this reviewed change (CR-146).

## Capabilities

- modified: `gate-lanes`

## Impact

- `src/agentmarshal/journal/gate.py`: `run_gate` counts the task's
  `changes_required` review records and says the line on the
  implementation lane.
- `tests/test_gate.py`: a test per scenario of the new requirement.
- `tests/fixtures/gate/`: the two implementation-lane fixture transcripts
  (embedded and sidecar) and the sidecar journal-only refusal gain the
  line; the embedded journal-only fixture is unchanged.
- `openspec/specs/gate-lanes/spec.md` on archive.
