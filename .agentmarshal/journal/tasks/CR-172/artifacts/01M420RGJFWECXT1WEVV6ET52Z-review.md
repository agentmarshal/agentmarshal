CR172-001: `docs/threat-model.md:284-290` wrongly says every candidate-added record is checked by every current rule; ADR-0015 requires read-time validation under the record’s own schema, so lowered-schema records evade later rules, as the document itself immediately acknowledges.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"f60dda580fb6dd589814c451fea9b2d39b803100","verdict":"changes_required","findings":["CR172-001"]}
AGENTMARSHAL_VERDICT_END
