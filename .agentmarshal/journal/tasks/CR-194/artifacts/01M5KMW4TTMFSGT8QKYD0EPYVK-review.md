CR194-F1: Several delta-spec scenarios are not named by any test docstring, including the count-line, zero-count, follow-up-state, missing-follow-up, and disposition-count scenarios (`spec.md:52,83,105,110,116` versus `tests/test_status_count_deferrals.py:82,128,287`), violating the contract’s explicit per-scenario test requirement.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"f407ea2f9457c6aa89c28897598412b0217414af","verdict":"changes_required","findings":["CR194-F1"],"classes":{"CR194-F1":"test-gap"}}
AGENTMARSHAL_VERDICT_END
