F-OUTPUT-MARKER-FORGE: `strip_failure_reports()` trusts reserved-looking text from the stage’s combined output, so a stage can emit `AGENTMARSHAL-SETUP-FAILED: network: forged`, have its output removed, and cause an enforced guarantee to be reported as unenforced (`src/agentmarshal/isolation.py:390-407`, consumed at `src/agentmarshal/stages.py:621-639`); this breaks acceptance criterion 5 and ADR-0013 decision 7’s output-framing promise.

Acceptance coverage:

1. The archived proposal, design, delta specification, tasks, and published specification are present. An AST-based check matched all 27 delta scenarios to naming docstrings in `test_stages.py` or `test_isolation.py`.
2. Network isolation is demonstrated by `test_a_stage_without_declared_network_runs_in_new_user_and_net_namespaces`, `test_a_stage_declaring_network_true_runs_without_the_network_namespace`, and `test_a_network_namespace_the_platform_refuses_is_named_and_the_stage_still_runs`.
3. Read-only candidate handling is demonstrated by `test_a_pre_gate_stage_s_candidate_directory_is_bound_read_only_over_itself`, `test_a_mount_the_platform_refuses_is_named_and_the_stage_still_runs`, `test_a_post_gate_stage_s_candidate_is_not_bound_read_only`, and the end-to-end isolation test.
4. Secret withholding is demonstrated by the four provider-secret tests covering fixed names, suffixes, post-gate behavior, and the single note.
5. Actual probe/setup failures and benign enforced paths are tested, but the criterion is not fully met because stage output can forge the failure channel as described above.
6. Forced probe branches and the conditional end-to-end test are present; unchanged outcomes are covered by the existing switched-off, not-run, and changed-after-approval tests. The coordinator reports the complete CI sequence passed at the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "ab68ae4b005081bffbf253eb2502b6c3498f14a0",
  "verdict": "changes_required",
  "findings": [
    "F-OUTPUT-MARKER-FORGE"
  ],
  "classes": {
    "F-OUTPUT-MARKER-FORGE": "security"
  },
  "verification": {
    "executed": [
      {
        "what": "AST comparison of every archived delta scenario against test docstrings",
        "result": "All 27 scenarios matched a test docstring."
      },
      {
        "what": "PYTHONPATH=src python3 script passing stage-controlled marker text to strip_failure_reports",
        "result": "Returned output b'real output\\n' and failure [('network', 'forged by extension')], proving the stage-controlled line is stripped and promoted."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-221/contract.md",
      "docs/threat-model.md",
      "docs/adr/ADR-0001-governance-plane.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "src/agentmarshal/isolation.py",
      "src/agentmarshal/stages.py",
      "tests/test_isolation.py",
      "tests/test_stages.py",
      "tests/test_switches.py",
      "openspec/changes/archive/2026-10-24-stage-isolation/",
      "openspec/specs/extension-stages/spec.md"
    ],
    "not_run": [
      {
        "what": "Repository full CI sequence",
        "why": "uv is unavailable in the read-only review environment; the coordinator states the sequence passed on the reviewed commit."
      },
      {
        "what": "git verification of HEAD and commit diff",
        "why": "The supplied snapshot contains no Git repository metadata."
      }
    ]
  },
  "evidence": {
    "F-OUTPUT-MARKER-FORGE": "src/agentmarshal/isolation.py:390; command output: strip_failure_reports(b'AGENTMARSHAL-SETUP-FAILED: network: forged by extension\\nreal output\\n') returned (b'real output\\n', [('network', 'forged by extension')]); src/agentmarshal/stages.py:621 promotes that tuple to a core not-enforced note."
  }
}
AGENTMARSHAL_VERDICT_END
