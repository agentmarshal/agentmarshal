F-SETUP-CLOEXEC — [isolation.py:297](/tmp/agentmarshal-review-5i9340il/snapshot/src/agentmarshal/isolation.py:297) calls `os.set_inheritable()` outside the setup’s exception handler; if a sandbox refuses that operation, the exception escapes `preexec_fn`, and [stages.py:619](/tmp/agentmarshal-review-5i9340il/snapshot/src/agentmarshal/stages.py:619) converts it to `not run` instead of running the stage and naming both guarantees as not enforced. This breaks acceptance criterion 5 and the published “setup step fails” scenario; the existing `test_a_setup_step_that_fails_in_the_stage_s_own_child_is_named` only substitutes a setup that successfully marks the descriptor before reporting a simulated mount failure.

Acceptance coverage:

- AC1: proposal, design, delta, completed tasks, archived change, and synchronized main specification are present. All 28 delta scenarios have matching `Scenario:` test docstrings.
- AC2: network namespace behavior is demonstrated by `test_a_stage_without_declared_network_runs_in_new_user_and_net_namespaces`, `test_a_stage_declaring_network_true_runs_without_the_network_namespace`, and the refusal test.
- AC3: read-only mounting and writes reporting are demonstrated by the pre-gate mount, refused-mount, post-gate, declared-writes, and end-to-end isolation tests.
- AC4: fixed-name and suffix withholding, post-gate preservation, and single-note behavior each have dedicated provider-secret tests.
- AC5: namespace, mount, capability-drop, and missing-report branches are tested, but the descriptor-marking failure above violates the criterion.
- AC6: forced probe verdicts, the conditional end-to-end test, and switched-off/not-run/changed-after-approval regression tests are present. The coordinator reports the complete CI sequence passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "db074827d22b4230551860d36f1ff2904c96a171",
  "verdict": "changes_required",
  "findings": [
    "F-SETUP-CLOEXEC"
  ],
  "classes": {
    "F-SETUP-CLOEXEC": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Scenario-to-docstring inventory over the archived delta and tests using Python AST",
        "result": "28 scenarios; 0 without a matching Scenario docstring"
      },
      {
        "what": "Call stage_setup with os.set_inheritable forced to raise PermissionError",
        "result": "PermissionError escaped from the setup closure"
      },
      {
        "what": "Run subprocess.Popen with a preexec_fn that raises PermissionError",
        "result": "SubprocessError: Exception occurred in preexec_fn"
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-221/contract.md",
      "docs/adr/ADR-0001-governance-plane.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/threat-model.md",
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
        "what": "Full CI sequence",
        "why": "The coordinator supplied a successful result for the exact reviewed commit; this materialized snapshot also lacks the uv executable."
      },
      {
        "what": "Git commit/history verification",
        "why": "The supplied snapshot contains no discoverable Git metadata."
      }
    ]
  },
  "evidence": {
    "F-SETUP-CLOEXEC": "src/agentmarshal/isolation.py:297-303 and src/agentmarshal/stages.py:619-630; forced os.set_inheritable failure produced PermissionError, and Popen converts an escaping preexec_fn exception to SubprocessError."
  }
}
AGENTMARSHAL_VERDICT_END
