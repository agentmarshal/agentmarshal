+++
schema = 1
id = "CR-034"
title = "advisory findings: approved reviews may carry non-blocking findings"
scope = ["src/agentmarshal/journal/records.py", "src/agentmarshal/journal/submit_review.py", "src/agentmarshal/cli.py", "tests/test_journal.py", "tests/test_gate.py"]
acceptance = []
+++

# CR-034: advisory findings

## Context

The v2 review model is binary: `approved` iff there are no findings. But
real code review — human and AI, as GitHub/GitLab model it — routinely
approves *with* non-blocking comments ("approve with nits", follow-up
suggestions). Forcing `approved` to carry zero findings makes reviewers
either drop that signal or falsely escalate to `changes_required`. It also
prevents faithfully recording a common attestation and makes richer,
audit-friendly evidence impossible (an engaged approval vs a rubber stamp).

This adds a distinct `advisory_findings` field: non-blocking findings that
may accompany any verdict, including `approved`, without affecting the
merge decision. Blocking findings keep their existing `findings` semantics.

## Objective

Let a review record carry optional non-blocking `advisory_findings`
alongside the existing blocking `findings`, so `approved` reviews can
record follow-up findings without weakening the gate's merge rule.

## Acceptance Criteria

- [ ] A review record may carry an optional `advisory_findings` list. It is
      validated exactly like `findings` (non-empty unique string ids) when
      present, is disjoint from `findings` (a finding is blocking or
      advisory, not both), and is omitted when empty (backward compatible:
      existing records without the field stay valid).
- [ ] The blocking rule is unchanged: `approved` still requires empty
      `findings`; a non-`approved` verdict still requires at least one
      `finding`. `advisory_findings` may be present or absent under any
      verdict.
- [ ] `create_review_record` gains an optional `advisory_findings`
      parameter (default none); `submit_review` and the `submit-review` CLI
      gain a repeatable `--advisory-finding`. The status view surfaces the
      advisory count.
- [ ] The merge gate is unaffected: an `approved` review carrying
      `advisory_findings` still passes the review check (advisory findings
      never block a merge).
- [ ] Tests: an approved review with advisory findings validates and round
      trips; advisory findings that are empty-string, duplicated, or
      overlapping with `findings` are rejected; approved-with-blocking still
      rejected; the gate passes an approved-with-advisory review.
- [ ] `uv run agentmarshal validate`, pytest, ruff, format, and mypy stay green.

## Non-Goals

- No change to the blocking `findings` semantics or the gate's merge rule.
- No per-finding severity model — a simple blocking/advisory split only.
- No migration change here (CR-035 will let `migrate --lenient` preserve a
  pre-v1 approved-with-findings review as advisory).
