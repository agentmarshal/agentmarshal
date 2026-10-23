quickstart-gate-severity: [docs/quickstart.md:587](/tmp/agentmarshal-review-zdrredl3/snapshot/docs/quickstart.md:587) says the gate reports the count on an `INFO` line, but `gate.py` emits `WARN` when the threshold is reached or unreadable; this violates the contract’s accuracy criterion.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"096c7daa2ded0789038b099ead1e81d0be6ca9db","verdict":"changes_required","findings":["quickstart-gate-severity"],"classes":{"quickstart-gate-severity":"claim-accuracy"}}
AGENTMARSHAL_VERDICT_END
