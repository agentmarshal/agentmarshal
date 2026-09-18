## Context

`_launch_review_tail` in `review.py` passes `prose=raw_output` to
`submit_review` for every verdict it records; `submit_review` writes the bytes
to `.agentmarshal/journal/tasks/<task>/artifacts/<record-id>-review.md` and
pins them on the record. `submit-review --prose FILE` reaches the same writer.
`capture.py` has `capture_policy_from_project`, which returns the `attested`
preset when the project file has no `capture` section, and
`CapturePolicy.level_for(CaptureClass.REVIEWS)`; no command calls either.
Rejected-verdict output and successful-run stderr are kept in local temporary
files by `_preserve_output` and `_preserve_reviewer_diagnostics`.

## Goals

- The capture policy decides what happens to a review's prose, on both paths.
- The default does not publish it.
- `commit` is exactly today's behaviour.

## Non-Goals

- The private store, and a hash-pinned reference into it.
- The economics and sessions classes.
- Changing rejected-verdict output or diagnostics handling.
- Touching prose already committed.

## Decisions

- **The policy is the existing one.** The level comes from
  `capture_policy_from_project(...).level_for(CaptureClass.REVIEWS)`, applied
  to the project file of the journal being written — in a sidecar placement,
  the sidecar's. A second key for the same decision would be the field
  designed twice.
- **`commit`: unchanged.** The artifact is written and pinned as before, and
  `agentmarshal review` prints the same `reviewer prose pinned: <ref>` line.
- **`hash` without a private store: out of the journal, kept locally.** ADR-0005
  defines `hash` as a hash-pinned reference into a private store, and the store
  does not exist. Pinning a hash on the record would make `validate` refuse the
  journal for an artifact it cannot find, and a new record field would be a
  schema change for a stopgap. So in this release `hash` does the part it can:
  the prose stays out of the journal. `agentmarshal review` writes the output
  to a local temporary file, as it already does for a rejected verdict, and
  names the file on stderr; the record carries no artifacts. The reference
  arrives with the store.
- **`off`: nothing kept.** No artifact, no temporary copy; stderr says the
  prose was not kept and why.
- **The human path refuses rather than drops.** `submit-review --prose` under
  `hash` or `off` is refused before anything is written, naming the level and
  `capture.overrides.reviews = "commit"` as the setting that permits it. An
  operator who passed a file asked for it to be kept; silently dropping it
  would be the surprise this change removes.
- **A malformed capture section fails closed, early.** `agentmarshal review`
  resolves the level before it launches the reviewer, so a bad section costs
  no reviewer run. `submit-review` resolves it only when `--prose` is given:
  without prose there is nothing for the policy to decide.
- **This repository opts in.** Its project file sets
  `capture.overrides.reviews` to `commit`: the repository is public with its
  review prose on purpose, and its tooling reads the pinned line.

## Risks

- [A 0.4.0 review in a project without a capture section keeps its prose only
  in a temporary file] → that is the decided default. The documents say how to
  choose `commit`, and the stderr line names where the file went.
- [The `minimal` and `full` presets now change review prose but not economics
  or sessions] → stated in the documents; the other classes are not read.
