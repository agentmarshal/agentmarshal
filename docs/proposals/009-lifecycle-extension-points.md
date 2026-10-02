# 009 — No lifecycle extension points for evidence storage

- **Reporter:** Adopter C (business-application project on Windows) · **Observed on:** 0.1.0 · **Disposition:** accepted *(2026-10-03 — [ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md); deferred at intake)*

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

> Superseded 2026-10-03: **accepted**, answered by
> [ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md).
> The deferral's reasoning and the 2026-09-01 re-read stand below as
> history; the decision and what of the ask it covers are in the dated
> section at the end.

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

## Disposition — accepted (decision 2026-10-03)

[ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
answers the ask. It gives an extension a declared stage — `pre-gate` (in CI
and at the merge step, before the gate) and `post-gate` (after `complete`),
with the stage, its mode and its isolation declared in the extension's
manifest. An extension is a separate step before the gate, not part of it:
at `pre-gate-stop` it can pause the process, and that is all it can do to
it — the merge happens when the gate has passed and no pause stands, and
the gate reads neither an extension's output nor its flags. The rule for
future stages: a hook before a transition may only pause; a hook after a
transition may only notify and write to the log; new stages are added at an
adopter's request, and "after open" is already a named candidate.

Covered: the project-defined step enforced at a lifecycle point — it is
declared in a manifest and invoked by the tool, instead of living in a
wrapper script kept by discipline, and at `pre-gate-stop` it is enforced,
because the merge waits while its pause stands. Not covered: the two
boundaries the report names are not among the two stages — "after open"
waits on an adopter's request, and there is no `pre-complete`; the
artifact-storage example lands on `post-gate`, or on a `pre-gate` extension
inside `complete`, not on a hook at that exact boundary. And no extension
code runs inside the gate or a governed transaction: the trust-boundary
reason behind both deferrals is answered by construction — the gate takes
nothing from an extension's run — rather than by trusting the hook.

Decided; not shipped yet — the ADR's stages follow in their own tasks.
