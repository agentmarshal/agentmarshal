CR171-001: `_retarget_contract_id` in `src/agentmarshal/journal/open_task.py:125` preserves `\n` and `\r\n` but drops lone `\r`; a valid contract accepted by `parse_contract_text` is corrupted during ID replacement and refused instead of being opened and pinned.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"4a4d2f358a8f7c98baeb628c75e2609e5d618251","verdict":"changes_required","findings":["CR171-001"]}
AGENTMARSHAL_VERDICT_END
