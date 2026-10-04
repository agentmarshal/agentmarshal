CR171-001 is fixed: `_retarget_contract_id` now preserves lone `\r`, with a byte-for-byte regression test covering LF, CRLF, and lone-CR endings.

CR171-002: `src/agentmarshal/journal/open_task.py:72-149` recognizes fewer TOML forms than `parse_contract_text`; for example, a valid quoted key `"i\u0064"` parses as `id` but cannot be retargeted, so `open --contract-file` rejects a valid contract instead of opening and pinning it.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"341863b360cc156c785385ca01661cdfae9a678c","verdict":"changes_required","findings":["CR171-002"]}
AGENTMARSHAL_VERDICT_END
