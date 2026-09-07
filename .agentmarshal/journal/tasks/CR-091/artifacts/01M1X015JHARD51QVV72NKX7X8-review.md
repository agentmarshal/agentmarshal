CR-091-F001: Accepted prose is always persisted without capture-policy control (`review.py:423`, `submit_review.py:72-99`), contradicting ADR-0005 Decision 2 and the updated overview.

CR-091-F002: Sidecar history filtering excludes Git type changes (`gate.py:378-381`), allowing an artifact-to-symlink replacement (`T`) to evade append-only enforcement.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"8daae5ee5d76c369b8ea2778d651dadfbddec17d","verdict":"changes_required","findings":["CR-091-F001","CR-091-F002"],"advisory_findings":[]}
AGENTMARSHAL_VERDICT_END
