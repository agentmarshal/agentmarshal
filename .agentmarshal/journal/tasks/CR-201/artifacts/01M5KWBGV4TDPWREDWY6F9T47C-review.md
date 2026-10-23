ADV-001 — The archived [proposal.md](/tmp/agentmarshal-review-06cy7kbp/snapshot/openspec/changes/archive/2026-10-23-complete-uses-gate-review/proposal.md:24) and [tasks.md](/tmp/agentmarshal-review-06cy7kbp/snapshot/openspec/changes/archive/2026-10-23-complete-uses-gate-review/tasks.md:9) incorrectly claim the sidecar may re-derive the latest review and that only `gate.py`/`complete.py` change; the implementation correctly requires `resolved_review` and changes `cli.py`.

Acceptance coverage:

- AC1 is met: the proposal, design, modified delta, archive, and synchronized main spec exist. A static comparison found all 12 delta scenarios named by docstrings in `tests/test_complete_dispositions.py`, demonstrated by the six existing disposition tests and six new `test_the_gate_report_*`, `test_an_appended_review_*`, and `test_a_completion_after_an_appended_review_*` tests.
- AC2 is met by `test_the_gate_report_carries_the_id_of_the_approving_review_it_passed_on`, `test_the_gate_report_carries_the_id_of_the_review_an_acceptance_covered`, and `test_the_gate_report_carries_no_review_id_when_it_passed_on_no_review`.
- AC3 is met by `test_an_appended_review_cannot_change_which_advisory_findings_are_owed`, its sidecar counterpart, `test_an_advisory_id_of_an_appended_review_refuses_naming_the_id`, and `test_a_completion_after_an_appended_review_writes_its_dispositions`.
- AC4 is met by `test_default_run_transcript_matches_the_committed_fixture`, `test_the_disposition_flags_are_refused_on_the_findings_lane`, and `test_a_findings_completion_without_flags_is_unchanged`; the transcript fixtures are unchanged in the supplied diff.
- AC5 is met: the source diff changes only the scoped completion paths, and the coordinator reports the complete CI sequence and suite passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "41a1aaa48c4c0b66e7493291f6415742c85521d7",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-001"
  ],
  "classes": {
    "ADV-001": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {
        "what": "Static AST comparison of archived delta scenario titles against test docstrings",
        "result": "All 12 scenarios matched at least one test docstring."
      },
      {
        "what": "uv run pytest -q tests/test_complete_dispositions.py",
        "result": "Could not start because uv is unavailable in the review environment."
      },
      {
        "what": "git rev-parse HEAD",
        "result": "Could not inspect repository metadata because the supplied snapshot contains no Git worktree metadata."
      }
    ],
    "read": [
      "Task CR-201 contract and amendment",
      "supplied diff",
      "docs/adr/ADR-0007-operator-acceptance.md",
      "docs/adr/ADR-0016-the-lifecycle-of-review-findings.md",
      "docs/threat-model.md",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/journal/complete.py",
      "src/agentmarshal/cli.py",
      "tests/test_complete_dispositions.py",
      "tests/test_gate.py",
      "archived OpenSpec proposal, design, tasks, and delta",
      "openspec/specs/finding-lifecycle/spec.md",
      "coordinator's CI result for the reviewed commit"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "uv is not installed in this read-only snapshot environment; the coordinator states the full sequence passed on the reviewed commit."
      }
    ]
  },
  "evidence": {
    "ADV-001": "openspec/changes/archive/2026-10-23-complete-uses-gate-review/proposal.md:24-26,38-40 and tasks.md:9-13 contradict src/agentmarshal/cli.py:937-942 and src/agentmarshal/journal/complete.py:80-86."
  }
}
AGENTMARSHAL_VERDICT_END
