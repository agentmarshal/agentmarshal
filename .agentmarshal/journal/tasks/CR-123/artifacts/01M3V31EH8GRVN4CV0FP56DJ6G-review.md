F-029-OUTBOX-SCAFFOLD: `docs/proposals/029-advisory...` lines 7–14 incorrectly says nothing creates the outbox directory; `init` already scaffolded it in 0.3.0 and 0.4.0, as proposal 023 and the release documentation confirm.
F-028-REPORTER-PATH: `docs/proposals/028-check-outcomes-are-not-evidence.md` lines 31–32 publishes the reporter’s internal API path `/api/resources`, violating the contract’s prohibition on repository paths and identifiers.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"aa76965d94779ddde9fe3fd0bf8f013373e2bc12","verdict":"changes_required","findings":["F-029-OUTBOX-SCAFFOLD","F-028-REPORTER-PATH"]}
AGENTMARSHAL_VERDICT_END
