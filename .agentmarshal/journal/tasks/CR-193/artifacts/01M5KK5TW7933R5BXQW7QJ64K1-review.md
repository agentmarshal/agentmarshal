ADV-001: The archived design falsely claims the gate and `leak-scan` share `_acknowledgement_mark`; separate implementations remain in `capture.py:404` and `cli.py:1321`, so they can drift despite currently matching.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"fdb9467ef27afcda821c28cb807055c3c7b3e41b","verdict":"approved","findings":[],"advisory_findings":["ADV-001"],"classes":{"ADV-001":"claim-accuracy"}}
AGENTMARSHAL_VERDICT_END
