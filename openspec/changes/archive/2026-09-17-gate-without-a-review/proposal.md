## Why

The shipped provider template runs the gate on a pull-request head that cannot
carry its own review record: a review is recorded against a commit after that
commit exists, and lands at completion. The gate therefore refuses every
implementation pull request, the job is marked tolerated, and the check-run is
red on every one of them
([proposal 017](../../../../docs/proposals/017-provider-template-gate-check-structurally-red.md)).

A check that is red by construction teaches an operator that red is normal. The
previous attempt to fix this in the template alone was refused in review: the
only thing a template can do is skip the gate entirely, which drops the scope,
append-only, base-state and lifecycle checks the run does enforce.

## What Changes

- The gate accepts being asked to evaluate everything that does not depend on a
  review. In that mode, a candidate with **no** review record has its two
  review-bound checks reported as not examined instead of refused.
- A candidate that **has** a review record is judged exactly as before, in every
  mode. The mode cannot turn a refusal into a pass.
- The shipped template uses the mode, and stops tolerating a failure it was
  causing itself.

## Impact

- `src/agentmarshal/journal/gate.py`, `src/agentmarshal/cli.py`.
- `templates/github/agentmarshal-governance.yml`.
- `docs/github-enforcement.md`, which describes the arrangement being replaced.
- The transcript of a default gate run is unchanged.
