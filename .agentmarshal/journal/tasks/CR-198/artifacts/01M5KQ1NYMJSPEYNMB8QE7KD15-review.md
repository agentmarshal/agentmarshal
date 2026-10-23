adr-clarification-cites-wrong-cr145-finding — `docs/adr/ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md:124` cites `gate-rules-unreachable-on-read`, but the CR-145 finding that demonstrated the gate admitting a forged lowered-schema record is `gate-admits-forged-low-schema-record`; this fails the contract’s requirement to name the finding that exposed the issue.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"519527682ae46b9ac59a07755d03b5c3faead2ce","verdict":"changes_required","findings":["adr-clarification-cites-wrong-cr145-finding"],"classes":{"adr-clarification-cites-wrong-cr145-finding":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
