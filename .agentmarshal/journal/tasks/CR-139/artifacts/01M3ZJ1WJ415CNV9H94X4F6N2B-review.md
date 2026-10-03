I read the ADR against every file it rests on and against the five proposals it answers.

**What I verified**

- Present-behaviour claims (acceptance 3): a session record's fields and the `measured`/`reported` usage block (`src/agentmarshal/journal/records.py:947`, `src/agentmarshal/cli.py:294`); `outcome` checked only for non-emptiness and never aggregated (`records.py:548`, no `outcome` reference in `report.py`); `created_at` set to now in `create_session_record` (`records.py:942`); a session deliberately admitted in any task state, with ADR-0005 Decision 3 as its ground (`session.py:33`); `report` printing only `reviews=` and `tokens=` per task and in the summary (`report.py:144`, `report.py:163`); `provider-limit` documented since 0.4.1 (`docs/quickstart.md:449`, `CHANGELOG.md:41`). All accurate.
- Every measurement quoted from proposals 032, 024, 018, 034 and 026 matches the proposal text, including the 85-minute median over 24 tasks, the 2-of-2 dropped reset times, the hash-pinned sidecar cost file, the missing output-limit word, and the two idempotency failure modes.
- Form matches ADR-0012..0017 (Status/Date, "Builds on", the not-implemented-by-this-document note, Context / Decision / Left open / Consequences / Alternatives considered); every link target exists; proposals are cited as "proposal NNN"; the record model stays a later decision with no number; no private document, adopter, client or unpublished release is named (0.4.1 is the latest published release).
- All nine points in the acceptance list are present: explicit start/end with `created_at` untouched, lead time by phase with `unknown` for older sessions, the reset time, the optional cost summed per currency, the documented outcome values, `--if-missing`, journal summary vs. process-log exports, the journal-transaction sentence, and the economics/sessions capture classes left open.

I could not execute the CI sequence — `uv` is unavailable in this sandbox — but the change adds one Markdown file and touches no code, no journal record and no lint-covered path, and the repo has no docs-structure test.

**Advisory findings**

Decision 3 (line 96) scopes the reset time to "a session whose outcome is `provider-limit`", while Decision 5 (line 113) keeps `outcome` unchecked free text; the ADR never says whether the new field is conditionally validated against that word, which is the first question the implementing task will have to answer, and the two readings differ in behaviour.

Decision 8 (line 139) says proposal 032's "third ask lands as a documentation sentence", but that ask had two halves — the sentence and exposing the gate's journal-only lane to the required check — and 032's disposition routes the second into the journal-transactions work of proposals 019 and 035; the ADR does not say so, so a reader concludes the whole ask was settled here.

Decision 4 (line 102) answers proposal 018's cost field without touching the question that proposal's deferral named as the one the accounting rework must answer first — how a per-task figure is attributed when one agent session spans several tasks — and "Left open" (line 145) does not record it either, so an answered-in-full proposal leaves a visible hole.

The fourth Consequences bullet (line 172) reads "so a refusal, a crash and a truncation read differently across projects", where the point of a shared vocabulary is that the three read differently *from one another* and the same way *in every project*; as written the sentence can be read as the opposite of the decision's rationale.

None of these is a dropped or added decision point, a wrong statement about current behaviour, or a form break, so none blocks publication.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "224ef0d56aebb5e7ed452ab547abd05b69e92d55", "verdict": "approved", "findings": [], "advisory_findings": ["reset-time-field-coupled-to-unchecked-outcome", "proposal-032-third-ask-described-as-fully-answered", "cost-attribution-across-tasks-neither-decided-nor-left-open", "consequence-sentence-inverts-shared-vocabulary-point"]}
AGENTMARSHAL_VERDICT_END
