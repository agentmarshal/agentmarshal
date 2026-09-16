CR-094-HASH-001: All ten source entries contain only 16 hex characters, not a complete SHA-256 hash, in each digest’s source line.
CR-094-PRIVACY-002: “GitHub” appears in every digest and the Adopter D index profile, violating the host-name sanitization requirement.
CR-094-DISPOSITION-003: Proposal 016 says the fix ships in the “next release” but does not name 0.4.0 in its disposition at docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:47-48.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"9a459a0d64e875952361a58c1cd06a6427c858f3","verdict":"changes_required","findings":["CR-094-HASH-001","CR-094-PRIVACY-002","CR-094-DISPOSITION-003"]}
AGENTMARSHAL_VERDICT_END
