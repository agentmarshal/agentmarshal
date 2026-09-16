I read the full diff and verified every checkable claim against this repository's own code and journal.

**What I verified**

- All ten digests (014–023) carry `Observed on: 0.3.0`, a `Source: sha256:…` line (each 64 lowercase hex chars, all distinct), a verbatim measurements block, a "Proposed" section and a reasoned disposition.
- No repository name, hostname, filesystem path, task identifier (`CR-NNN`) or code excerpt from the reporter appears in any new digest or index row; the Adopter D profile names a setup only.
- The index carries the `Where` column, filled for all ten rows, and 016 — the one already fixed on the default branch — says so in its disposition and names 0.4.0.
- CONTRIBUTING states the three tracking handles (source hash, disposition, where-it-went) and points at `docs/proposals/README.md`.
- Factual claims about this project check out: `doctor` has exactly four checks (`src/agentmarshal/doctor.py:119-124`); the session activity vocabulary is `implementation, review, other` (`src/agentmarshal/journal/records.py:151`); reviewer stderr is consumed only on a non-zero exit (`src/agentmarshal/journal/review.py:202-211`); the placeholder error names no token (`review.py:172-174`); the review prompt carries contract + diff and no amendments (`review.py:100-136`); prose is pinned for every parsed verdict on the default branch (`review.py:420-432`); `leak-scan` prints categories only (`src/agentmarshal/cli.py:1147-1151`); the shipped template is `continue-on-error: true` and greps `CR-[0-9]+` out of the head ref (`templates/github/agentmarshal-governance.yml:56,74`); the project declares no markers.
- The self-incriminating counts in 022 are exact: 22 amendment records exist, one of them in the still-open CR-095, leaving **21 records across 18 of 91 completed tasks**. CR-075 is a concrete instance of the described scenario — amendment after the second review (a `changes_required` about a criterion's wording, "raised in both runs"), rounds three and four judged against the amended text.

Two non-blocking issues follow.

`index-partial-count-inconsistent`: in `docs/proposals/README.md:77` the batch summary says "all accepted — two of them in part", and line 37 cites "as 018 and 020 do" as the pattern for a partial disposition, but three digests carry an in-part qualifier — 016's header reads `accepted *(in part; the third request is met in another shape)*` and its index row repeats it. The sentence is defensible if "in part" is read as "with a deferred half", but a reader counting headers gets three, and this directory has already had one task spent on correcting its own summary counts.

`wrap-width-inconsistent`: `docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:61` runs to 99 columns where every other body line in the directory is hard-wrapped at 80, and `docs/proposals/023-upstream-outbox-has-no-transaction.md:16-18` wraps raggedly mid-sentence ("sweeps / whatever findings happen / to be unstaged"), which reads as an unreflowed edit.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "404ddd9175bb0cbcf1b7f349804e9049e3d1c368", "verdict": "approved", "findings": [], "advisory_findings": ["index-partial-count-inconsistent", "wrap-width-inconsistent"]}
AGENTMARSHAL_VERDICT_END
