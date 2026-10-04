CR172-F1: `docs/threat-model.md:91` overstates forgeable-text protection as applying to values generally carried by records or contract headers; the cited specification limits write-time refusal to enumerated fields, while fields such as contract `scope`/`acceptance` and amendment reasons are not covered universally.

CR172-F2: `docs/threat-model.md:436` cites its own preamble for the “decided, not yet implemented” classification instead of an allowed ADR, specification, README, or SECURITY source; SECURITY.md does not itself establish the full roadmap-versus-defect rule stated there.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"97d92e93cd06976f4d1afd6f1ed843b506b0828d","verdict":"changes_required","findings":["CR172-F1","CR172-F2"]}
AGENTMARSHAL_VERDICT_END
