# Self-hosting workflow

AgentMarshal governs its own development with its own v2 journal and
gate. This document describes the task lifecycle, the merge-authority
model, and which parts of the earlier v1 tooling remain in use versus
which are superseded.

## Lifecycle of a task

Every task travels the same path; each transition is recorded as
evidence in the journal (`.agentmarshal/journal/tasks/<id>/`).

1. **Open.** `agentmarshal open --title "<title>" --scope <path> [...]`
   creates the task's `contract.md` and an `opened` record. The opening
   is a journal-only change: it is committed on its own branch and merged
   first, so the contract is present in the base tree before any
   implementation. The gate recognises a journal-only transaction and
   does not require a review for it.

2. **Implement.** Branch from the updated default branch, make the change
   within the declared scope, and commit. No lifecycle field is flipped
   by hand — task state is projected from the records.

3. **Review.** An independent reviewer evaluates the exact candidate
   commit; the verdict is recorded with
   `agentmarshal submit-review --task <id> --commit <sha> --verdict
   approved --role <r> --vendor <v> --model <m> --email <reviewer>`.
   The reviewer's email must differ from the candidate's authors and
   committers — the gate enforces this independence.

4. **Merge.** The gate is the merge authority:
   `agentmarshal gate --task <id> --commit <sha> --base <target>`
   (context can be derived from the branch when the flags are omitted).
   It passes only when the task is not closed at the base, the diff is
   within the contract scope read from the base tree, the latest review
   of the exact commit is approved by an independent reviewer, the
   pipeline is attested for that commit, and the evidence records are
   append-only and consistent. A thin merge wrapper runs the gate and,
   on success, performs the provider's merge.

5. **Complete.** `agentmarshal complete --task <id> --commit <sha>
   --base <target>` re-runs the gate and, on pass, writes the
   `completed` record. That record is committed as a journal-only
   completion transaction and merged the same way (the gate's base-state
   check admits the open→done transition).

At any point `agentmarshal validate` checks the whole journal for
integrity (every contract parses, every record is valid, every task
projects to a consistent state, no record-id collisions); it is the
governance check run in CI.

## Merge-authority model

Authority lives in `agentmarshal gate`, which is provider-agnostic: it
reads git and the journal only. The actual merge call is delegated to
the hosting provider. In this repository a thin host-side wrapper runs
the gate and, on a pass, invokes the provider's existing merge API with
the legacy merge policy disabled — the v2 gate has already established
authority. This keeps the governance decision vendor-neutral while
reusing whatever merge transport the provider offers.

Pipeline attestation is explicit: the wrapper passes the green pipeline
SHA (`AGENTMARSHAL_PIPELINE_OK_SHA`) that the gate checks against the
candidate commit.

## Live vs superseded tooling

The self-hosting cut-over replaced the v1 governance authority but reuses
some v1 transport:

- **Still in use:** the provider merge-request API (fetch head/target and
  perform the merge) and the read-only review launcher that produces an
  independent reviewer verdict. These are transport and reviewer
  integration, not governance decisions.
- **Superseded:** the v1 merge policy, the v1 task-lifecycle/audit
  scripts, and the managed implementation cycle. Their roles are now held
  by `agentmarshal gate`, `agentmarshal complete`/`validate`, and the
  task lifecycle projected from records. CI governance runs
  `agentmarshal validate` rather than the v1 validator.

## Notes

- Openings and completions are journal-only and take the gate's
  deterministic lane (no model review required); implementation
  candidates take the full review-bound lane.
- The gate reads the contract and the base task state from the merge-base
  / base tree, never from the candidate, so a candidate cannot widen its
  own scope or hide that its task is already closed.
