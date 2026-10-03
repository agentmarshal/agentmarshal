Previous finding CR171-002 is fixed: escaped keys are now explicitly refused by the amended contract, before journal paths are created.

CR171-003: `src/agentmarshal/journal/open_task.py:75-79` mishandles valid one-line triple-quoted values ending in quote characters; for example, `id = """CR-099""""` parses as `CR-099"` but the regex consumes the first three closing quotes, causing `open --contract-file` to refuse a supported top-level, one-line `id` declaration.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"a54aaa7acf557e9ecf45d42e349f514b969453f5","verdict":"changes_required","findings":["CR171-003"]}
AGENTMARSHAL_VERDICT_END
