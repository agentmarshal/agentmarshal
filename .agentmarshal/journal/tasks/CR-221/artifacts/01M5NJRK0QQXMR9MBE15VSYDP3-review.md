F-ROOT-READONLY: In `src/agentmarshal/isolation.py:93`, an invocation running as UID 0 maps namespace UID 0 to UID 0 and never drops capabilities before exec; Linux therefore preserves the stage’s namespace `CAP_SYS_ADMIN`, allowing it to remount or unmount the supposedly read-only bind created at `src/agentmarshal/isolation.py:219` and modify the candidate. This breaks acceptance criteria 3 and 5, while `test_an_isolated_stage_cannot_reach_the_network_or_write_the_candidate` only attempts an ordinary write and does not expose the bypass.

Acceptance criterion 1 is met structurally: the archived proposal, design, delta specification, tasks, and synchronized main specification are present; a static scan found all 26 delta scenario titles verbatim in test docstrings across `test_stages.py` and `test_isolation.py`.

Acceptance criterion 2 is met for ordinary non-root operation by `test_a_stage_without_declared_network_runs_in_new_user_and_net_namespaces`, `test_a_stage_declaring_network_true_runs_without_the_network_namespace`, and the end-to-end isolation test.

Acceptance criterion 4 is met by the four provider-secret scenario tests covering fixed names, suffixes, post-gate behavior, and a single note.

Acceptance criterion 6 is demonstrated by the forced-probe branch tests, the conditional end-to-end test, and existing switched-off/not-run/changed-after-approval tests. The coordinator reports the full CI sequence passed at the reviewed commit; I found no contrary tool failure.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "df6fb68f4690ca7e548f3e013bafa5d24e89f0fb",
  "verdict": "changes_required",
  "findings": [
    "F-ROOT-READONLY"
  ],
  "classes": {
    "F-ROOT-READONLY": "security"
  },
  "verification": {
    "executed": [
      {
        "what": "Static comparison of archived delta scenario titles against test docstrings",
        "result": "All 26 scenarios were found verbatim."
      },
      {
        "what": "Read local Linux user_namespaces(7) and capabilities(7) documentation",
        "result": "unshare(CLONE_NEWUSER) grants all capabilities in the new namespace; exec preserves them when namespace UID is 0."
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
      "openspec/changes/archive/2026-10-24-stage-isolation/",
      "openspec/specs/extension-stages/spec.md"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "uv is unavailable in the read-only review environment; the coordinator supplied the passing result for the exact reviewed commit."
      },
      {
        "what": "Runtime reproduction as UID 0 with usable user and mount namespaces",
        "why": "The review environment runs as UID 1000 and forbids creating temporary files."
      }
    ]
  },
  "evidence": {
    "F-ROOT-READONLY": "src/agentmarshal/isolation.py:93 identity-maps UID 0 to UID 0; src/agentmarshal/isolation.py:181 creates the user/mount namespaces; src/agentmarshal/isolation.py:219 installs the bind without subsequently dropping capabilities. Local user_namespaces(7) states that namespace capabilities survive exec when UID is 0."
  }
}
AGENTMARSHAL_VERDICT_END
