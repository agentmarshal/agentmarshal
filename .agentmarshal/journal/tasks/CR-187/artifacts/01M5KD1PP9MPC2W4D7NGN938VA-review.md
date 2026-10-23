CR187-001: `src/agentmarshal/acknowledge.py:233-247` accepts `--reason` without leak-checking it, so supplying the matched private marker or secret as the reason writes that text into the acknowledgement record, contradicting the specified scenario that the written record carries neither matched text nor a marker value.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"e9eda55b8f1aa1c46902e8c1f467ada99c33aeac","verdict":"changes_required","findings":["CR187-001"],"classes":{"CR187-001":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
