# 009 — No lifecycle extension points for evidence storage

- **Reporter:** Adopter C (business-application project on Windows) · **Observed on:** 0.1.0 · **Disposition:** deferred

## Finding

A project often needs something to happen at a lifecycle boundary — before
`complete`, an artifact must be stored somewhere the project defines. There is
no extension point, so the step lives in a wrapper script and is enforced only
by discipline.

The reporter frames a second, narrower case as an instance of the first: where a
project's evidence artifacts should be stored is a local policy, and the tool
should provide the hook without owning the policy. Both are explicitly marked as
proposals, not descriptions of current behaviour.

## Proposed

Defined lifecycle hooks (a `post-open` / `pre-complete` boundary), with storage
policy left to the project.

## Disposition — deferred

The need is real — we run exactly such wrappers ourselves, and a rule that is
not a step in the loop does not get executed (proposal 005 makes the same
point).

Deferred because hooks are an interface that is easy to add and hard to remove,
and because they interact with the trust boundary: a hook that runs during a
governed transaction becomes part of what the gate implicitly trusts. Doing this
before record provenance exists would widen the trust surface at the moment we
are trying to narrow it. The narrower storage case may land earlier than the
general mechanism.

### Re-read 2026-09-01 — remains deferred; the narrower case is moving first, as predicted

The provenance precondition is met (`recorded_by`, ADR-0006). And the
disposition's closing guess — "the narrower storage case may land earlier than
the general mechanism" — is the path events are taking, stated precisely:
hash-pinned artifact references are **in the record schema and validated**
(ADR-0005 Decision 4), though no command writes one yet; and ADR-0008 has
**decided** where such evidence lives (journal placements), though the sidecar
placement is not yet implemented. Neither piece requires a hook running inside
a governed transaction — which is the point.

The general mechanism stays deferred for the original reason, which time has
not touched: a hook interface is easy to add and hard to remove, and a hook
that runs during a governed transaction becomes part of what the gate
implicitly trusts.
