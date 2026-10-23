RC-UTF8-05 is fixed: full-content UTF-8 decoding with `errors="replace"` preserves replacement characters for the reported invalid sequence.

RC-MASK-05 is still present in `src/agentmarshal/record_check.py:328-340,380-384`: the post-mask rescan result is discarded. For an AWS-key excerpt with private marker `aws`, masking creates `[masked: aws-access-key-id]`; the rescan finds `private-marker`, but the withheld message names only the original `aws-access-key-id` category. The required secondary category is therefore omitted, and the regression test does not cover this because its marker already matches the original input.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"8d819936bc03c8d021f83a5315c0999ef1e37882","verdict":"changes_required","findings":["RC-MASK-05"],"classes":{"RC-MASK-05":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
