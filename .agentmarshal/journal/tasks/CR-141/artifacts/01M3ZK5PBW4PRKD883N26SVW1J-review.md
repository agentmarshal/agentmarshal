I verified every factual claim in the ADR against the files it rests on. Here's what I checked and what I found.

**Verified as accurate:** the `leak-scan` arguments (`--base`/`--commit`, both required, `cli.py:342-347`), what it scans (`merge-base..commit` added lines via `leak_scan_diff`, `cli.py:1260-1287`), exit 1 on a hit / 0 on none (`cli.py:1310-1321`), the per-hit shape `path: identification` (`capture.py:349`), the identifications (built-in signature name, `private-marker #N` one-based, `capture.py:663`), the `<private marker #N>` path masking (`capture.py:328`), the declaring-file suppression as the only suppression (`capture.py:651-657`, and `leak_scan` config carries only `private_markers`), the artefact refusal naming categories and no file (`capture.py:396-403`), the gate's `WARN: possible leak in candidate additions (advisory, not blocking):` line adding no violation (`gate.py:1179-1183`), `NOT EXAMINED: advisory leak scan (findings lane has no diff)` (`gate.py:239`), `project.json` as the config file, and every claim attributed to ADR-0005/0006/0007/0013/0014/0015 and to the two specs. All nine links resolve. The form matches ADR-0012..0019 (Context, Decision, Left open, Consequences, Alternatives considered). The record model is left to a later unnumbered decision. No adopter, client, release number or unpublished ADR number appears. The diff is one new markdown file, so the CI sequence is unaffected — I could not execute it (`uv` is absent from this snapshot), but nothing in `tests/` enumerates `docs/adr/` or `docs/README.md`.

Findings:

The second Consequences bullet (line 200-202) says an acknowledgement "changes the command's exit code, never what either surface shows" — which is the opposite of what the ADR decides. Decision 3 says the hit "gains the mark", "What this revises" (line 170-174) says the run "prints the mark that transcript does not have", and the fifth Consequences bullet says "only a candidate whose scan reports an acknowledged hit changes the transcript". On a literal reading this bullet denies the very revision acceptance criterion 3 requires the ADR to state, and an implementer could cite it as "do not change the transcript".

Decision 4 (line 131) asserts "`status` shows who acknowledged", committing a third surface the approved decision does not name — the contract's enumeration and the ADR's own Consequences speak of the gate and the command as "both surfaces". Today `_print_task_detail` (`cli.py:510-607`) has a dedicated line for `acceptance` and a generic `id / type / created_at` fallback for anything else, so an acknowledgement record would not show who acknowledged without a further change this decision does not otherwise mention.

The Context's closing sentence (line 66-68) says "the deferral was lifted because the path stays what it was judged to be — a new kind of record". Proposal 020's 2026-10-03 disposition says the opposite causally: the deferral was lifted "for the reason the whole intake moved", and remaining a new kind of record is why it "arrives through a decision record rather than as a flag". Being a new record type is what deferred it and what dictates its form, not what lifted the deferral.

Decision 3 and Consequences state unqualified that the gate prints an acknowledged hit and that "acknowledged by whom and why is printed wherever the hit is", but the gate's line is bounded at 20 hits with "and N more not shown" (`gate.py:70`, `capture.py:348-353`), a bound the leak-scan spec explicitly permits. With more than twenty hits the mark can fall outside what the transcript shows, so the "nothing is hidden" guarantee is weaker on the gate's surface than stated.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "355f89a9f569b13b90c333829310044e20885a70",
  "verdict": "changes_required",
  "findings": [
    "consequences-bullet-contradicts-the-transcript-change-it-revises"
  ],
  "advisory_findings": [
    "status-surface-added-beyond-the-approved-decision",
    "deferral-reason-inverts-proposal-020",
    "unqualified-print-guarantee-ignores-the-bounded-gate-line"
  ]
}
AGENTMARSHAL_VERDICT_END
