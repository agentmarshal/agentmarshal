ADV-001-stale-adr-status-notes: ADR-0005 and ADR-0004 still document accepted finding reviews as retaining a temporary copy (`docs/adr/...`).

ADV-002-design-overstates-the-preflight: `design.md:28` says preflight avoids filesystem access, but `validate_record_for_write` reads journal/project state.

ADV-003-unreachable-except-clause: `submit_review.py:88` redundantly re-raises an exception the following handler cannot catch.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"1ec3e82cf67f13c9de3f1861f168b2e5825241bf","verdict":"approved","findings":[],"advisory_findings":["ADV-001-stale-adr-status-notes","ADV-002-design-overstates-the-preflight","ADV-003-unreachable-except-clause"]}
AGENTMARSHAL_VERDICT_END
