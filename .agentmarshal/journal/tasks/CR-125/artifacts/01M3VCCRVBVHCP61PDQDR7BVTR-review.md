I reviewed the diff against the contract, the surrounding published digests, and the code the digests make claims about. Notes on verification: the reporter's source files 022-025 and the coordinator's dispositions document are not in the snapshot, so verbatim quotation of measurements and the exact dispositions could not be checked against their sources — everything below is internal consistency plus claims checkable against this repository. I could not execute the CI sequence (sandbox approval), but the change is docs-only and nothing in `validate`/pytest/ruff/mypy reads these files — the only test that mentions `docs/proposals` (`tests/test_project.py:26`) asserts strings in the generated outbox README, which is untouched.

What is right: all four digests follow the 032-036 form (header frame → Finding with verbatim measurements → Proposed → Disposition → Where), carry distinct lowercase 64-hex source hashes, name 0.4.0 as observed-on, and carry no reporter-side identifier. 032's corrected journal-only-lane paragraph is accurate — `src/agentmarshal/journal/gate.py:650` computes `journal_only` and `:740` emits exactly the quoted transcript line, skipping the scope and review checks. 037's root-cause claim checks out on both sides (`review.py:206` decodes strictly and `_run_git` catches only `OSError`; `gate.py:254` raises `GateError`, degraded to `WARN: leak-scan skipped` at `gate.py:1148`). 035's index row now lists all three accepted parts, 034's Where no longer names an unpublished document, 024/026 are consistent across header, Disposition, Where and index row, and the batch introduction and map are complete for fourteen files.

Findings:

**039's disposition misstates what `status` does today.** `docs/proposals/039-review-findings-do-not-feed-back-into-the-next-round.md:103` says "`status` today projects only the lifecycle state — a task is open, done or abandoned — and prints no verdict counts at all". `agentmarshal status <task>` prints the full record trail, and each review record line carries `verdict=`, `findings=N` and `advisory=N` (`src/agentmarshal/cli.py:536-552`); the project's own quickstart says so at `docs/quickstart.md:475`. The accepted part (a *count* of `changes_required` verdicts) is still unshipped, but the sentence as written tells a reader `status` shows nothing about verdicts. This is the same error class CR-124 flagged in 032, which this task was carried here to fix.

**033 now carries a disposition the index does not define.** `docs/proposals/033-contract-review-before-implementation-does-not-pay-off.md:3` and the index row at `docs/proposals/README.md:99` were changed from "accepted" to "recorded", which does make the header agree with the body — but the index's own Disposition section (`docs/proposals/README.md:30-38`) states that every proposal carries one of **accepted**, **deferred** or **declined**, and the diff did not extend that vocabulary. `docs/proposals/README.md` is in scope, so the index now contradicts itself about a value it publishes as a reporter-facing guarantee.

**039 describes `brief` as reading the contract only.** At `docs/proposals/039-...md:73`, "`brief` builds the implementer briefing, from the contract only" — `build_brief` also appends the task's amendment history from its records and inlines the decisions and documents the contract names (`src/agentmarshal/journal/brief.py:341-344`). The contrast being drawn (no findings feed in) holds; the characterization does not.

**040 attributes an adopter pattern to the journal's mechanics.** `docs/proposals/040-...md:81-84` grounds the decision to meet stuck-step visibility with a template rather than a record type in "the journal's own mechanics: a journal write is a transaction through a pull request and its required check". The tool writes records into the working tree and leaves committing to the adopter — 035, published in this same batch, says so explicitly — and the transaction-through-a-pull-request is the protected-base pattern of proposal 019. The conclusion is defensible for the recommended workflow; the stated reason is not a property of the journal.

**039's seventh proposed item gets no disposition in the index's vocabulary.** The plugin interface for lifecycle steps (`docs/proposals/039-...md:88-91`) is answered with "the base is deferred, not declined, so the fallback is not taken up" (`:117-119`) rather than accepted, deferred or declined.

**038 uses a space as a thousands separator.** `docs/proposals/038-...md:35-37` and `:95` write "2 700", "3 800", "1 000"; no other file under `docs/` uses that style in English prose.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "08c548805b8178f5c10257b0d55b46beba429ae1",
  "verdict": "changes_required",
  "findings": [
    "039-status-verdict-counts-overstated",
    "033-disposition-outside-index-vocabulary"
  ],
  "advisory_findings": [
    "039-brief-described-as-contract-only",
    "040-adopter-pattern-called-journal-mechanics",
    "039-plugin-interface-has-no-disposition",
    "038-space-thousands-separator"
  ]
}
AGENTMARSHAL_VERDICT_END
