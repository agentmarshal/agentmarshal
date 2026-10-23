The previous finding CR185-CLASS-COMPLETENESS is fixed: omitted reported IDs now record as `other` with warnings and have regression coverage.

CR185-DOC-PROMPT-OVERCLAIM: `docs/quickstart.md:108` says the generated prompt explains all class-handling behavior, but `src/agentmarshal/journal/review.py:242` omits the documented handling of missing IDs, extra IDs, malformed objects, and associated warnings.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"37608f73ebf5560299124b4b8fb2499cb3c27e3f","verdict":"approved","findings":[],"advisory_findings":["CR185-DOC-PROMPT-OVERCLAIM"],"classes":{"CR185-DOC-PROMPT-OVERCLAIM":"claim-accuracy"}}
AGENTMARSHAL_VERDICT_END
