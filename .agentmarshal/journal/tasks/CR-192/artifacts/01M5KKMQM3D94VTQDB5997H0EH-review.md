review-reread-can-switch-advisory-set: `complete.py` rereads `reviews[-1]` after the gate returns, so a newly appended review can replace the review the gate actually passed on; contrary to `design.md:82-85`, a newer review with no advisories can weaken the check and allow completion without dispositions for the earlier review. This concurrency case is advisory under the stated threat model.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"48bcc39f371befe1f00c7d99be159e278fd77e5e","verdict":"approved","findings":[],"advisory_findings":["review-reread-can-switch-advisory-set"],"classes":{"review-reread-can-switch-advisory-set":"correctness"}}
AGENTMARSHAL_VERDICT_END
