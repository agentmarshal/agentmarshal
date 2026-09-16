CR-094-HASH: All ten source lines in `docs/proposals/014-...` through `023-...` contain only 16 hex characters, not complete SHA-256 digests.
CR-094-PRIVACY: The digest metadata and index profile expose the named provider `GitHub` in `docs/proposals/014-...:3` through `023-...:3` and `docs/proposals/README.md:109`.
CR-094-016-RELEASE: Proposal 016’s disposition says only “next release”; the required release `0.4.0` appears only in the index at `docs/proposals/README.md:82`.
CR-094-018-WHERE: The accepted coordination activity in proposal 018 has no destination; `accounting rework` in `docs/proposals/README.md:84` applies to the deferred cost field.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"9a459a0d64e875952361a58c1cd06a6427c858f3","verdict":"changes_required","findings":["CR-094-HASH","CR-094-PRIVACY","CR-094-016-RELEASE","CR-094-018-WHERE"]}
AGENTMARSHAL_VERDICT_END
