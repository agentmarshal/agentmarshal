CR171-004 is fixed: declaration probing now uses a TOML-safe ASCII probe, and non-BMP IDs are covered by a regression test.

CR171-005: `tests/test_pin_contract_hash.py:233` claims to test an unreadable contract file, but its cases cover only missing and invalid files; no case simulates a read failure, so the contract’s explicit unreadable-file scenario is not demonstrated.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"574277b93311a0989e8db44b1174898d867cd125","verdict":"changes_required","findings":["CR171-005"]}
AGENTMARSHAL_VERDICT_END
