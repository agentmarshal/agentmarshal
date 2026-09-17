CR096-001: `review.py:395-402` and `brief.py:243-300` never load or render amendment records, violating ADR-0011 Decision 1.

CR096-002: `records.py:37-50,144,890-943` excludes `reviewed_contract`, supports no new schema, and stamps review records as schema 3/4; `submit_review.py:36-67` never records the contract hash, violating ADR-0011 Decision 4.

CR096-003: `openspec/changes/render-amendment-history/` and `openspec/specs/contract-history/` are absent, so the required design, completed checklist, delta scenarios, and scenario-named tests were not delivered.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"dc499ae9e65df6eacfacfd1cba18cff3017d285c","verdict":"changes_required","findings":["CR096-001","CR096-002","CR096-003"]}
AGENTMARSHAL_VERDICT_END
