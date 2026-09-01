# 004 — Provider CI integration has slots but no contract

- **Reporter:** Adopter A (Python web service on Linux) · **Observed on:** 0.1.0 · **Disposition:** deferred

## Finding

`agentmarshal init` scaffolds `.agentmarshal/integrations/{ci,git,provider}` and
`.agentmarshal/plugins/`. All four are empty, and nothing documents what belongs
in them — the adopter has to guess whether the slot expects a contract, code, or
nothing at all.

The report argues that "the operator supplies the transport" works for review,
where the operator already provides a reviewer command, but not for CI: pipeline
attestation is a gate input, so every adopter re-implements provider polling
with no interface to write against. Adopter A wrote a working provider CI
integration and offers it as evidence that a transport contract is achievable —
explicitly as a question, not a patch.

The same report notes that the gate judges the working tree rather than the
revision, which is the documented trusted-checkout model but surprises a reader
who expects the candidate SHA to be authoritative.

## Proposed

Either document the slots as intentionally free-form, or define a minimal
transport contract for CI attestation that adopters can implement.

## Disposition — deferred

The gap is real: empty undocumented directories are an invitation to guess, and
we created them. Documenting them costs nothing and should happen soon.

A CI transport contract is a larger commitment — it fixes an interface across
providers we do not yet have enough adopters to generalise from, and a premature
interface is harder to remove than to add. Deferred until we have integrations
from more than one provider family to compare.

### Re-read 2026-09-01 — remains deferred, and half the finding dissolved

Measured while re-reading: the empty `integrations/{ci,git,provider}` and
`plugins/` directories are **v1 leftovers**. The published v2 `init` — checked
against an installed 0.1.0 and against current source — creates none of them.
The guessing invitation was real, but the fix is deletion, not documentation of
slots that no longer exist; the migration document now says so.

The CI transport contract stays deferred for the original reason, unweakened:
the provider families available to generalise from are still the two we operate
ourselves, and no adopter integration beyond the original report has arrived. A
premature interface is still harder to remove than to add.
