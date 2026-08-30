# 008 — Session and token accounting is not in the core

- **Reporters:** Adopter B, Adopter C (business-application project on Windows) · **Observed on:** 0.1.0 · **Disposition:** accepted

## Finding

Raised independently by two adopters in four separate documents — the strongest
convergence in this batch.

The `session` record type exists and `record-session` can write one, but nothing
in the loop produces it: a task's actual cost is not captured unless the adopter
builds the plumbing. Both reporters did, in different ways, and both concluded
the mechanism belongs in the core rather than in each project's hooks.

Adopter B, working with an external executor, reports that usage has to be
reconstructed afterwards from provider logs — a per-project procedure that is
lossy and cannot be verified later. Adopter C asks for it to be part of the
standard journal contract and, separately, for the quickstart to show token
accounting so an adopter learns it at the start rather than after months.

Both note the schema question that follows: what belongs in a session record for
a run executed by a provider that reports usage in its own format.

## Proposed

Session/token accounting as a core capability with a defined record shape, and
its place in the documented loop.

## Disposition — accepted

Two adopters converging independently, in four separate documents, is the
clearest signal this project has received — and it matches our own practice: we
account for cost per task, and we do it with local scripts because the tool does
not.

The economics claim is one of the project's stated purposes, so leaving capture
to each adopter is a gap in the product, not an integration detail. Accepted for
the core. The provider-format question is real and is where the design effort
goes: the record must be provider-neutral while remaining reconstructable, which
argues for storing normalised counts plus a provenance marker rather than raw
vendor payloads.
