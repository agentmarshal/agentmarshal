I read the ADR against every published text it cites — ADR-0007, 0008, 0011–0022, proposals 034, 036, 038, 041–043 — and against `gate_context.py`, `gate.py` and `docs/self-hosting-workflow.md`.

**What holds.** All sixteen links resolve. The present-behaviour bullets in Context are accurate: the branch policy and its two refusals, `origin/HEAD` with the `master` fallback and the refusal when neither resolves (`gate_context.py:21,80-102`); the empty-range refusal (`gate.py:648`), the merge-base contract read and its refusal (`gate.py:801-806`), the scope check from the base side, the review-or-acceptance check, the reviewer-vs-writers comparison over `merge-base..commit` (`gate.py:431-433`), and the attestation as the one check taken from the invoker (`gate.py:1041`); `complete --base` as an ancestor (`docs/self-hosting-workflow.md:44-51`). The three named revisions are correct: ADR-0019's decision 5 does declare the vocabulary unread, proposal 036's disposition does refuse any non-`implemented` producing session, and ADR-0014 D9 does name only `status` and `doctor`. The form matches ADR-0012..0022, the nine actions and eleven rules are all there with the three definitions, and nothing names a private document, an adopter or a client.

Findings follow.

**Rule 5 sends a reviewer's provider limit to an implementer.** `docs/adr/ADR-0023-next-the-next-step-of-a-task.md:173-176` scopes the rule to "an implementer's or a reviewer's" session, but its only non-`wait` branch is "a next implementer in the contract's list → `fix` by them with `fallback_reason: provider-limit`". So a reviewer run that stopped on a quota with no `resets_at` yields an implementer fix round on a candidate nobody has reviewed — and, because rule 5 precedes rules 8–11, it does so even when an approving review of the head already exists. That is the exact failure class proposal 041 is written against, and it ignores the ordered reviewer list ADR-0018 decision 3 and ADR-0022 §5 give the contract header, whose measured motivation in proposal 034 is precisely a reviewer's subscription hitting its limit.

**Decision 1 says the task is derived from the branch, while the task is a required argument.** `ADR-0023:113-116` gives the signature `next <task> [--branch …] [--base …] [--json]` and then says "The branch and the base derive the way `gate` derives them — the task from the branch, the base by default the default branch". `<task>` is positional and mandatory, and "Left open" at `ADR-0023:303-304` defers the no-task form past 0.5.0, so nothing in this command derives a task from a branch. What the sentence needs to say — how `--branch` defaults — it does not say.

**`provider-limit` is attributed to ADR-0022 as a marked non-round.** `ADR-0023:236-239` says "`environment-failure` and `provider-limit` are not rounds — the outcome vocabulary of ADR-0022 marks them so". ADR-0022 §4 marks only `environment-failure` ("not a round"); its `provider-limit` entry says "documented since 0.4.1; carries `resets_at`" and nothing about attempts. The substance rests on proposal 041's item 2 ("the attempt is not consumed"), not on ADR-0022's vocabulary.

**`allow_unfinished` is an output no rule produces.** It appears in the actions at `ADR-0023:152` and among the JSON keys at `ADR-0023:254`, but no branch of the table emits it, and decision A at `ADR-0023:268-271` explicitly refuses the one case that would have — `review` with `allow_unfinished` for a `time-limit` run with its report ready. The "no sessions at all" branch (`ADR-0023:219-222`) needs no override either, since proposal 036's disposition leaves that case as today.

**`fallback_reason` is named by rule 5 but absent from the JSON contract.** `ADR-0023:176` has the action carry `fallback_reason: provider-limit`, using ADR-0022's session field name, while the key list at `ADR-0023:252-254` omits it — leaving it unclear whether `next` prints the field or merely tells the driver what to record on the next session.

**The relaunch count overstates its source.** `ADR-0023:70-71` says "the queue took 20 manual relaunches in two days"; proposal 041 reports "**20 queue launches** (14 starts of the queue script, 2 … watchers, 4 side chains)" of which "Every launch beyond the first was a manual change of the plan" — nineteen relaunches, not twenty.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "172daa47bb1e2187ea08383970e38085f7070036",
  "verdict": "changes_required",
  "findings": [
    "rule-5-reviewer-provider-limit-falls-to-implementer-fix",
    "decision-1-derives-task-from-branch-though-task-is-required"
  ],
  "advisory_findings": [
    "provider-limit-not-marked-a-non-round-by-adr-0022",
    "allow-unfinished-output-produced-by-no-rule",
    "fallback-reason-absent-from-json-key-list",
    "proposal-041-queue-launches-restated-as-20-relaunches"
  ]
}
AGENTMARSHAL_VERDICT_END
