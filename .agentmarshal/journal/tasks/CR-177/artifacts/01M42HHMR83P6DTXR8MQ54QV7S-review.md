CR177-001: `tests/test_agreement.py:162-183` never constructs a candidate or calls `run_gate`; it tests content validation and the writer-side status guard separately, so it does not demonstrate the required scenario that the gate admits a candidate adding an agreement record.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"1248874d451bde879f11ee30a79e9d191358f3ce","verdict":"changes_required","findings":["CR177-001"]}
AGENTMARSHAL_VERDICT_END
