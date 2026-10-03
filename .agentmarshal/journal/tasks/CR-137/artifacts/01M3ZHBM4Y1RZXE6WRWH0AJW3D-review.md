I verified the ADR against the contract point by point, against the sibling ADRs for form, and against the source files each present-tense claim rests on.

**What I executed** (read-only, in `/tmp/agentmarshal-review-7izs3itq/snapshot`):

- `grep`/`sed` over `src/agentmarshal/journal/status.py` — `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL = frozenset({"session", "reopened"})` with `reopened` gated on `terminal_state == "done"`: the ADR's "today `session` is admitted after either terminal state and `reopened` after completion only" is exact.
- `src/agentmarshal/cli.py:247-253` and `docs/quickstart.md:112-122`, `gate.py:1035-1046` — `commit` is the default mode and requires `pipeline_sha` to equal the candidate commit; `ci-required` delegates to the provider's required checks. Matches the Context bullet.
- `complete.py:3-4,49,57` — "runs the gate itself and records completion only when the gate passes". Matches.
- `review.py:692-714` (`git archive` into stdlib tar, no `.git`, plain tree) and `records.py:152` (`approved`, `changes_required`, `blocked`, `rejected`) plus `_VERDICT_OPTIONAL = {"advisory_findings"}`. Matches.
- `attestation.py:24-32` — nine record types, none of them a check; `report.py:29-30,64,70` — `review_cycles` and `tokens`, so "next to rounds and cost" is accurate; `gate.py:776` holds the real transcript line "measurements-only append to a task closed at base (session records accrue post-terminal)" the ADR says will name `check`.
- `ADR-0005` Decision 3 ("measurements are not lifecycle… may be appended to a task in any state, including terminal") — this grounds the ADR's "after any terminal record — completed or abandoned", so the widening past the contract's shorthand "after completion" is the session rule itself, not an added point.
- `ADR-0013` Decision A.3 (a hook before a transition may only pause; new stages at an adopter's request) — the "Left open" reasoning for the snapshot-preparation command is correct.
- `ls` on every link target: all ten relative links resolve (`../proposals/026|028|030`, `../../openspec/specs/record-lifecycle|gate-lanes`, ADR-0004/0005/0013/0014/0015).
- Section headings of ADR-0012/0013/0014/0015 — the shape (title, Status/Date, "Builds on"/"partly revises", the not-implemented-by-this-document paragraph, Context "How it works today", numbered Decision, Left open, Consequences, Alternatives considered) is ADR-0012/0013's own, including the position of "Left open".
- Dispositions of proposals 026 (finding 1: "stated as unconfirmed and lands as advisory", `evidence` into the review-evidentiality decision), 028 (`check` record, `brief`, `report`) and 030 (executed-versus-read field; the snapshot preparation command as the optional part) — each decision clause maps onto one of them, including `skipped` as an outcome, and nothing from the enumerated acceptance list is missing or extra.
- Checked the prohibitions: no adopter, client, private document or release version is named anywhere in the file; proposals are all "proposal NNN" and linked; the record model is referred to as a later decision with no number.

**What I checked by reading only:** that the "partly revises" claim is the right pair of specifications — `record-lifecycle` plainly covers projection, writer and gate post-terminal admission, and `gate-lanes` only through its "A default run is unchanged / the pinned transcript still matches" requirement, which the reworded transcript line touches. The contract prescribes naming exactly these two, so I did not treat the indirect gate-lanes link as a defect.

**What I could not run:** the full CI sequence. `uv` is not installed in this review snapshot and this sandbox refuses to execute `python3 -m pytest` / `agentmarshal validate`, so criterion 5 is unconfirmed by execution. Read-only evidence that it is unaffected: the diff adds one Markdown file and no code; `grep -rn "docs/adr" tests/` finds only synthetic fixture paths (`ADR-0042-*`, `ADR-9999-*`) under `tests/test_brief.py` and `test_journal.py`, the only repo document any test reads is `docs/quickstart.md` (`tests/test_quickstart.py:18`), and `agentmarshal validate` reads journal records, not `docs/`. I state that as unconfirmed rather than as a pass.

No blocking or advisory findings.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ecbd902688af9398f6dfb7008d64597676a022e4", "verdict": "approved", "findings": []}
AGENTMARSHAL_VERDICT_END
