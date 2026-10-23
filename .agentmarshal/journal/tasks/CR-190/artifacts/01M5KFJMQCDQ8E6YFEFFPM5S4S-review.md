CR190-001: `src/agentmarshal/cli.py:1344` prints `recorded_by` without leak masking; a valid `AGENTMARSHAL_ACTOR` equal to the detected secret is recorded and then emitted verbatim, violating the acceptance criterion that matched text never appears in output.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"a6519ee330eadb76e933a94032fabded02f8db5b","verdict":"changes_required","findings":["CR190-001"],"classes":{"CR190-001":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
