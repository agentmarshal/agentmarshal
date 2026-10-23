CR184-UNDECLARED-SOURCE: In `status_view.py:113`, `_is_declared_recorder` treats every `project-actor` record as currently declared without consulting the actors table; if that actor was removed or the project file is unreadable, status omits the required “not a declared actor” marker, violating the contract and ADR-0022 section 3.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"b795e2ff6b4f62f945795b016e8ba76e1d4f1535","verdict":"blocked","findings":["CR184-UNDECLARED-SOURCE"],"classes":{"CR184-UNDECLARED-SOURCE":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
