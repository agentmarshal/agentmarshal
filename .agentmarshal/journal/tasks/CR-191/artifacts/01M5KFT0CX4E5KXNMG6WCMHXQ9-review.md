CR191-001: `src/agentmarshal/journal/status_view.py:373` strips and case-folds actor IDs before checking the declared role list, so `actor="devin"` is incorrectly treated as declared by `implementers=["Devin"]`; actor IDs are exact labels, and the contract requires actors not in the declared list to be marked. The shared helper affects both implementers and reviewers.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"7b60ea50ab36e83f29a696abacb16dcf1caaf225","verdict":"blocked","findings":["CR191-001"],"classes":{"CR191-001":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
