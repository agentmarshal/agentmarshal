CR192-001: [complete.py](/tmp/agentmarshal-review-ozb3a2gm/snapshot/src/agentmarshal/journal/complete.py:155) splits on the first `=`, making a valid advisory ID containing `=` impossible to disposition even though record validation permits such IDs.

CR192-002: [complete.py](/tmp/agentmarshal-review-ozb3a2gm/snapshot/src/agentmarshal/journal/complete.py:135) infers the originating flag by searching the whole error text; for a valid advisory ID such as `follow_up`, a rejected disposition value is incorrectly reported as a `--follow-up` error instead of naming `--disposition`.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"279cc6aaa44a7c885a2e1c239164b5b69afbc102","verdict":"changes_required","findings":["CR192-001","CR192-002"],"classes":{"CR192-001":"contract-mismatch","CR192-002":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
