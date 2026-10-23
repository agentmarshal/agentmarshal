Previous findings: RC-UTF8-01 fixed; RC-MASK-02 fixed; RC-OUTPUT-03 fixed; RC-TEST-04 fixed.

RC-UTF8-05: `src/agentmarshal/record_check.py:186-193` treats structurally shaped but invalid UTF-8 sequences crossing the 4 KiB boundary as valid characters and silently drops their continuation bytes; for example, `F4 90 80 80` produces no replacement character, contrary to the undecodable-bytes acceptance criterion.

RC-MASK-05: `src/agentmarshal/record_check.py:337-343,383-390` handles a private marker contained in the mandated mask label by omitting the excerpt and withholding the matched category, contradicting the requirements that the record carry the masked excerpt and stderr name its category.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"1c9e90f3e6ad1498fd7fd8e69ef0215f55f6b7d7","verdict":"changes_required","findings":["RC-UTF8-05","RC-MASK-05"],"classes":{"RC-UTF8-05":"correctness","RC-MASK-05":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
