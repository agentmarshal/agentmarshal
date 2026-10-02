I verified every present-behaviour claim in the ADR against the files it cites, checked the proposal and ADR cross-references, compared the form against ADR-0012..0015, and worked through the contract's content checklist item by item.

**What checks out**

- `records.py` holds `findings` and `advisory_findings` as reviewer-invented id lists (`records.py:373-392`); `gate.py` and `acceptance.py` read only the blocking list (`acceptance.py:63-90`) — "neither path reads the advisory list" is correct.
- `status`' review line is literally `verdict=… findings=N advisory=N` (`cli.py:552-553`); `report` counts reviews and aggregates no findings (`report.py:64`, `report.py:144`); nothing links reviews and nothing counts `changes_required` (no such field or counter anywhere in `src/`).
- `complete` runs the gate itself and records completion only on a pass (`complete.py:49-66`) — so "the new check sits in `complete` itself, refusing before writing `completed`" rests on real behaviour.
- ADR-0007 does say in terms that advisory findings are "neither required nor permitted" at an acceptance and that "nothing is being overridden by shipping past an advisory" (`ADR-0007:84-85`), and gate-lanes' third requirement does pin the default transcript "byte for byte" (`gate-lanes/spec.md:47-49`) — both named revisions are accurate.
- ADR-0010 D3 is indeed "Named documents and decisions reach implementer and reviewer" (`ADR-0010:117-125`), so the "Left open" claim about delivery already existing is right.
- Form matches ADR-0012/0013 exactly (Context / Decision / Left open / Consequences / Alternatives considered); every ADR and proposal link resolves; the record model is referred to as a later decision with no number; no adopter, private document, in-house experiment or unpublished release is named. Scope is the single file, and the docs-map line is correctly absent per the non-goal.

**CI**: I could not execute `uv run …` here — the sandbox denied it, so I did not run the five-step sequence. Statically the change is documentation-only: no Python is touched (ruff/format/mypy unaffected), `agentmarshal validate` reads only the journal, no test enumerates `docs/adr/` or the documentation map, and `project.json` declares no leak-scan private markers. I found nothing that would turn CI red, but I am reporting this as unexecuted rather than as verified green.

**Advisory findings**

Proposal 039's fifth ask — whole-set mechanical checks in place of sampling, which that proposal's disposition accepts as documentation in the very same paragraph as the principle criterion ("the same kind of contract guidance, a pattern to document rather than a mechanism to build") and repeats in its "Where" section — appears nowhere in ADR-0016: Decision 5 answers only the third ask, and "Left open" lists items 2, 6 and 7, so the ADR's claim to answer proposal 039 has one accepted item unaccounted for.

The Context sentence "A review record carries two finding lists" is slightly stronger than the record model it cites: `advisory_findings` is optional and omitted when empty (`records.py:983`, `records.py:1018`; `review.py:67` treats it as `_VERDICT_OPTIONAL`), so a review record carries one required list and an optional second one — a wording the contract singles out for checking.

"The findings lane — the task lane of [ADR-0009] — is untouched" reads two ways: findings-lane tasks do get reviews that can carry advisory findings (`findings-review/spec.md`, `complete_findings_task` in `complete.py:70`), so taken literally the sentence exempts their completions from Decision 1, while the intended reading is only that ADR-0009's research-`finding` lifecycle is a different thing from a review finding.

None of these contradict the contract's blocking criteria.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "5ecb5d72d73b98ca841cef5287b73995fec25a28", "verdict": "approved", "findings": [], "advisory_findings": ["proposal-039-item-5-whole-set-check-unanswered", "review-record-advisory-list-is-optional", "findings-lane-untouched-is-ambiguous"]}
AGENTMARSHAL_VERDICT_END
