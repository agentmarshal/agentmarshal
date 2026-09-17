## Why

A research task lands through findings, not diffs (ADR-0009). The record type,
the review binding, the acceptance binding and the gate's findings lane all
shipped. One piece did not: the automated reviewer cannot be pointed at a
finding. `agentmarshal review --reviewed-finding` refuses with "not supported in
this release; use the human path", so the only way to review a conclusion is for
a person to record the verdict by hand.

That leaves the lane closed for the tasks it was built for. This project's own
research journal holds three such tasks; the first of them reached a recorded,
hash-pinned conclusion and the gate answered with one line — no review record
for the latest finding — because the only reviewer that could produce one is a
human, and on a single-operator project the human's git identity is the same
identity the finding's recorder resolves to, so the independence check refuses
it. A lane that can only be closed by a reviewer who is never independent is
not a lane.

The reviewer machinery already runs against a commit: it builds a metadata-free
snapshot, hands the reviewer a contract and a diff, demands a machine-verdict
block, and records the verdict with the reviewer's prose pinned as an artifact.
A finding has a contract and artifacts pinned by hash instead of a diff — the
same shape with a different subject.

## What Changes

`agentmarshal review --task T --reviewed-finding <id>` runs the configured
reviewer against a finding. The launcher verifies every artifact that resolves
locally against the hash the finding recorded, gives the reviewer the verified
bytes rather than the working tree, demands a verdict naming that finding, and
records it through the same writer the commit path uses.

It refuses, rather than reviews, when the pinned content is not the content on
disk: drift refuses the launch the way a new commit invalidates a verdict, and
a finding with nothing verifiable to review is refused too.

The commit path does not change — including the bytes of its prompt.

## Capabilities

- new: `findings-review`

## Impact

The findings lane becomes closable by the deciding reviewer channel, which is
independent of the recorder by construction. The three research tasks waiting on
it can complete. Nothing in the diff lane, the record schemas or the gate
changes.
