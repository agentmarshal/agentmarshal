I reviewed each acceptance criterion against the files in the snapshot, verifying every corrected statement against the document it rests on.

**Verified as correct:**
- **ADR-0014 decision 9 / proposal 042 / index row** — all three carry a dated 2026-10-03 amendment with the earlier text kept visible; each states the step events (kind of work, process, start time, deadline; a step ended with its outcome) in the process log, `status`/`doctor` showing a step past its deadline, the watchdog and loop monitor as a supplied component the harness runs, no background process started by the core, and the step commands and event fields deferred to the record model named without a number. No decision is added or removed; ADR-0013 never declared a `step` stage, so nothing dangles there.
- **docs/README.md** — one line each for ADR-0016 through ADR-0021 in the existing `— understand …` style; I checked each summary against the ADR it points at (including ADR-0017's `check` record, verdict-execution section and external-facts decision) and all are accurate.
- **Advisories 1–9** — each is closed in the named file with a dated Corrections note at the end (043 by the dated note the advisory asked for instead). I confirmed against sources: ADR-0013's scope table names only the config directory's Windows form while `%LOCALAPPDATA%` is on ADR-0014's map (`ADR-0014:168`); `uv sync --locked` reads a `uv.lock`, and the example now matches the `npm ci`/`package-lock.json` sibling; proposal 039's fifth ask is accepted as documentation; proposal 033 compares cost only (max cycle $18.24 < $27.02); proposal 032's disposition sends the journal-only lane to proposals 019 and 035; `.agentmarshal/extensions/` is on ADR-0014's map; proposal 036's refusal rests on the session `commit` and an outcome other than `implemented`; the self-hosting workflow numbers merge 4 and complete 5 while allowing either side of the merge; and the leak-scan spec sentence "its exit status answers whether a hit was found" sits exactly in the undecodable-file requirement (`openspec/specs/leak-scan/spec.md:107`).
- Changes are confined to the twelve scope files, and `complete --findings` exists as cited.

The CI sequence could not be executed here — `uv run agentmarshal validate` and `uv run pytest` were refused by the sandbox. The change is Markdown-only, no test asserts on the edited prose, and no docs linter is in the pipeline, so the risk is low, but I could not confirm the run.

Four advisory points follow.

The fourth Consequences bullet of `docs/adr/ADR-0019-accounting-time-quota-resets-money.md:177` keeps the connective "documented and unenforced, **so** … read … the same way in every project": uniformity now reads as a consequence of the vocabulary being unenforced, which Decision 5 (`the tool neither checks nor counts it`) contradicts — the required content is there, but the causal link belongs to the vocabulary being shared, not to its being unenforced.

In `docs/proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md:187` the new dated disposition is placed after `## Where`, so the file no longer ends with its "Where" section; every other proposal, including proposal 039's own dated amendment section, keeps Finding → Proposed → Disposition(s) → Where.

In the same file at line 130 the activity-probe paragraph still reads "an extension at the `step` stage declares its probes", and the amendment above it says "The rest of this disposition stands" — leaving an accepted extension point hanging off a stage the same file declines.

In `docs/proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md:120` and `:149` the new text refers to proposal 036 without a link (and as bare "036" on the second mention), where the contract asks for "proposal NNN" and linked; the file's existing style carries no proposal links, which is why I treat this as advisory rather than blocking.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "b32c9f51a4dc626f2e2b7949f443413f3b3cf582", "verdict": "approved", "findings": [], "advisory_findings": ["adr-0019-unenforced-so-uniform-non-sequitur", "p042-dated-disposition-after-where", "p042-activity-probe-still-at-declined-stage", "p041-proposal-036-not-linked"]}
AGENTMARSHAL_VERDICT_END
