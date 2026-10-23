Acceptance criterion 1 is met: the archived change contains proposal, design, tasks, and an ADDED contract-governance delta; all scenario names correspond to test docstrings in `test_gate_requires_agreement.py` and existing agreement tests.

Acceptance criterion 2 is met: the gate reads the setting from the project settings source, hashes the trusted contract, and emits one hash-bearing PASS/FAIL line. This is demonstrated by `test_a_recorded_agreement_at_the_judged_hash_passes`, `test_no_recorded_agreement_refuses_the_candidate`, the trusted-hash test, and the sidecar test.

Acceptance criterion 3 is met: stale agreements fail with both hashes, the latest stale hash is reported, matching older records still satisfy the existential check, and recorder identity is unrestricted. The corresponding stale/latest/any-agreement/any-recorder tests demonstrate these cases.

Acceptance criterion 4 is met: absent or false settings preserve the pinned transcript byte-for-byte, malformed settings emit WARN, and the deterministic lane emits no agreement line. The three corresponding scenario tests demonstrate this.

Acceptance criterion 5 is met: the supplied diff changes only the scoped gate logic, tests, and archived specification artifacts. The coordinator reports the entire prescribed CI sequence passed on the reviewed commit. I could not independently rerun pytest because this snapshot environment lacks `uv`; this is unverified locally, not a test failure.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4a36e64a7755b2f5d2a9ea145893dbf20633f963",
  "verdict": "approved",
  "findings": [],
  "verification": {
    "executed": [
      {
        "what": "Read-only Python AST comparison of archived delta scenario headings against test docstrings",
        "result": "All scenarios were located; two docstrings wrap their scenario names across lines and were confirmed by direct inspection."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-202/contract.md",
      "docs/threat-model.md",
      "docs/adr/ADR-0018-governing-the-contract.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/settings.py",
      "src/agentmarshal/journal/contracts.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/status.py",
      "tests/test_gate_requires_agreement.py",
      "tests/test_agreement.py",
      "openspec/changes/archive/2026-10-23-gate-requires-agreement/",
      "openspec/specs/contract-governance/spec.md"
    ],
    "not_run": [
      {
        "what": "Focused pytest and full CI sequence",
        "why": "The review environment has no uv executable; the coordinator states the full sequence passed on the reviewed commit."
      },
      {
        "what": "Git-history verification of the reviewed SHA",
        "why": "The supplied snapshot contains no Git metadata."
      }
    ]
  }
}
AGENTMARSHAL_VERDICT_END
