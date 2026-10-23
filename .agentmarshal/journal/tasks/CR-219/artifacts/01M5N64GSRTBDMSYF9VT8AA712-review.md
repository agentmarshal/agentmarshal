CR219-REMOVAL-TASK — CR-219 requires every removed switch entry to name the current task (`contract.md:15`), but `gate.py:1310-1325` ignores removed entries and reports them allowed; `test_gate_operational.py:301-333` confirms that removing CR-214’s entry under CR-001 passes, while the archived specification incorrectly codifies the same behavior at `openspec/specs/gate-lanes/spec.md:244-277`.

Acceptance coverage:

- Criterion 1 is met structurally: proposal, design, ADDED delta requirements, archived change, synchronized main spec, and all 14 scenarios have matching docstrings in `tests/test_gate_operational.py`.
- Criterion 2 is not met because of CR219-REMOVAL-TASK. Its other lane-selection, contract-source, parser, transcript, and non-review behavior is demonstrated by the operational tests at lines 56–159 and 496–613.
- Criterion 3 is met by `test_an_extra_path_in_the_diff_takes_the_lane_it_takes_today`, `test_in_a_sidecar_the_operational_lane_is_not_offered`, and the malformed, undeclared-extension, and wrong-task tests.
- Criterion 4 is met by `test_pre_gate_stages_do_not_run_on_an_operational_change` and `test_other_phases_and_other_candidates_behave_as_today`.
- Criterion 5 is met by the existing committed-transcript fixture test, the operational escaping test, and the coordinator-confirmed full CI sequence.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "ef196fa7cdd1061b761e3c24e64ea11d8b7507e3",
  "verdict": "changes_required",
  "findings": [
    "CR219-REMOVAL-TASK"
  ],
  "classes": {
    "CR219-REMOVAL-TASK": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Compared archived delta-spec scenario headings with test names and docstrings using rg and source inspection",
        "result": "All 14 archived scenarios have corresponding named tests; the removal scenario deliberately asserts behavior contrary to CR-219."
      },
      {
        "what": "Inspected operational_candidate, run_gate operational-lane checks, stage-run integration, and pinned transcript fixtures",
        "result": "The implementation satisfies the reviewed lane behavior except that removed entries are never checked for the current task."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-219/contract.md",
      "docs/adr/ADR-0010-process-extensions.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/stages.py",
      "tests/test_gate_operational.py",
      "tests/test_gate.py",
      "tests/test_findings.py",
      "openspec/changes/archive/2026-10-24-gate-operational-lane/",
      "openspec/specs/gate-lanes/spec.md"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The coordinator established that the complete sequence passed on the reviewed commit; the supplied read-only snapshot also contains no Git metadata."
      }
    ]
  },
  "evidence": {
    "CR219-REMOVAL-TASK": ".agentmarshal/journal/tasks/CR-219/contract.md:15 requires removed entries to name this task; src/agentmarshal/journal/gate.py:1310-1325 checks only candidate-present added/changed entries and explicitly allows removals; tests/test_gate_operational.py:301-333 asserts that removing an entry naming CR-214 under CR-001 passes."
  }
}
AGENTMARSHAL_VERDICT_END
