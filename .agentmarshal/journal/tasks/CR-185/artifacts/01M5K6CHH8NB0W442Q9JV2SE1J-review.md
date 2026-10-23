CR185-CLASS-COMPLETENESS: `src/agentmarshal/journal/review.py:913` silently records a partial `classes` mapping when the verdict omits classes for some reported findings, contradicting the requirement that every reported finding receive a class.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"85fc140c51b0685c450ed3b54a69ba5481599f55","verdict":"changes_required","findings":["CR185-CLASS-COMPLETENESS"],"classes":{"CR185-CLASS-COMPLETENESS":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
