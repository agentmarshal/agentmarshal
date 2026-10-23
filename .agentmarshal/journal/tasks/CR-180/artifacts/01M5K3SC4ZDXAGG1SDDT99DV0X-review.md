CR180-001: In `src/agentmarshal/agree.py:156`, `--contract` mismatch is checked before drift, so a drifted contract with an old pinned hash reports only the explicit/current mismatch and omits the required pinned/current short hashes and `amend` instruction, contradicting the acceptance criterion and `design.md`’s “Drift outranks `--contract`” decision.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"68fb171291ac0f3e862c0feedb2b1452b1e549c9","verdict":"changes_required","findings":["CR180-001"]}
AGENTMARSHAL_VERDICT_END
