CR184-TEST-001: `tests/test_status_schema_7_lines.py` does not provide scenario-named tests for every added delta-spec scenario—most clearly the unreadable/unhashable-contract scenario; the failed-step and marker scenarios are only folded into tests whose docstrings name different scenarios—violating CR-184’s explicit acceptance criterion.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"aaf1877e4f33fc702c37691a7e3d3baca2abc38c","verdict":"changes_required","findings":["CR184-TEST-001"],"classes":{"CR184-TEST-001":"test-gap"}}
AGENTMARSHAL_VERDICT_END
