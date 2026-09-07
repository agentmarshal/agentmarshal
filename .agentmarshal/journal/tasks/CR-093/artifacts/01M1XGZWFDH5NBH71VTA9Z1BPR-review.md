CR-093-F1 (blocking): `tests/test_gate.py:275`’s no-rename transcript test still passes with the old `git diff --name-only` implementation, violating the contract’s regression-proof requirement.

CR-093-F2 (advisory): `src/agentmarshal/journal/open_task.py:90` still documents scope checking as using `git diff --name-only`, which is now stale.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"079a9cda0b6e931bb9c98fde2e841e1087abc9fc","verdict":"changes_required","findings":["CR-093-F1"],"advisory_findings":["CR-093-F2"]}
AGENTMARSHAL_VERDICT_END
