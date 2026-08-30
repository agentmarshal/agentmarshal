+++
schema = 1
id = "CR-054"
title = "Keep the reviewer's reasoning when the verdict names a finding"
scope = ["src/agentmarshal/journal/review.py", "src/agentmarshal/journal/submit_review.py", "src/agentmarshal/cli.py", "tests/test_review_launcher.py"]
acceptance = [
  "a recorded verdict that is not `approved` leaves the reviewer's raw output in a file, and `agentmarshal review` names that file on stderr",
  "a recorded `approved` verdict carrying advisory findings does the same",
  "a recorded `approved` verdict with no findings at all leaves no file and prints nothing extra",
  "the record path remains the only line `agentmarshal review` writes to stdout",
  "failure to keep the output does not fail the run: the review is still recorded",
]
+++

# CR-054: Keep the reviewer's reasoning when the verdict names a finding

## Context

A review record carries finding **ids** — `["CR-053-F001"]` — and nothing else.
The reasoning behind them lives only in the reviewer's stdout, which
`launch_review` discards as soon as the verdict parses.

The launcher already knows this matters: a verdict that *fails* validation has
its raw output preserved (`_preserve_output`), because "a rejected verdict
should not cost you the analysis". But a verdict that is **accepted and
blocking** is the ordinary case, and there the analysis is dropped — leaving the
operator an id and no way to learn what it meant.

Found on ourselves during CR-053: the reviewer returned `changes_required` with
`CR-053-F1`, and reading the claim required wrapping `AGENTMARSHAL_REVIEWER_CMD`
in a `tee` script and asking again. Under a non-deterministic reviewer that
re-runs is not merely inconvenient — the second run may not raise the finding at
all, so the reasoning can be lost for good.

## Objective

Keep the reviewer's raw output whenever the recorded verdict names a finding,
blocking or advisory, and tell the caller where it is.

## Acceptance Criteria

- A recorded verdict other than `approved` preserves the reviewer's raw output;
  `agentmarshal review` names the file on **stderr**.
- An `approved` verdict carrying `advisory_findings` does the same — an advisory
  finding is still a claim with reasoning behind it.
- An `approved` verdict with no findings preserves nothing and prints nothing
  beyond the record path.
- The record path stays the only thing written to **stdout**, so existing
  callers that read it are unaffected.
- Preservation is best-effort: if the file cannot be written, the review is
  still recorded and the run still succeeds.

## Non-Goals

- Storing the reviewer's prose **in the record**. What is retained, where, and
  for how long is the capture policy's question (ADR-0005), which is roadmap;
  this task keeps a local file and says where it is.
- Changing the verdict protocol, the record schema, or what the gate reads.
- Cleaning up preserved files. As with rejected verdicts, removal is the
  caller's decision.
