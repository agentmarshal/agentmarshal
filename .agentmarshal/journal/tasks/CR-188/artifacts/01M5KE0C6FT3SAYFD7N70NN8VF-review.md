A1: `record_session` does not validate `cost_source` before the `--if-missing` match in `src/agentmarshal/journal/session.py`; a direct caller can supply an invalid source and receive a successful no-op, contrary to the design’s stated validation ordering. The CLI remains protected by argparse choices.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"61a9f92dc08845a1775f0078d0e9dfef6e78d30c","verdict":"approved","findings":[],"advisory_findings":["A1"],"classes":{"A1":"correctness"}}
AGENTMARSHAL_VERDICT_END
