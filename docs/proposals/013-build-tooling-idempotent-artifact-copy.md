# 013 — A build script fails when the artifact is already at its target path

- **Reporter:** Adopter B (business-application project on Windows) · **Observed on:** 0.1.0 · **Disposition:** declined

## Finding

The adopter's own build-ledger script copies a supplied artifact into a standard
artifact location when completing a build record. In one build the artifact had
already been produced directly into that standard location, so the copy attempted
to overwrite the file with itself and the operation failed.

## Proposed

Normalise and compare source and destination before copying; when they are the
same file, skip the copy and continue computing provenance and hash. Keep the
operation idempotent when it is retried after a transient failure.

## Disposition — declined

The defect is in the adopter's own tooling, not in an `agentmarshal` command:
the script, its copy step and its build record are all theirs. Declining here is
a boundary statement, not a judgement on the report — we answer for the
behaviour of the tool we ship, and taking responsibility for adopters' build
scripts would make that boundary meaningless.

The underlying idea is sound and worth keeping in their tool. Idempotence after a
transient failure is exactly the property a completion step should have, and
"the artifact is already where it belongs" is a legitimate recipe rather than a
misuse. Nothing here needs upstream to change for that to work.

## Note on this file

This proposal was **dropped rather than declined** when the first batch landed —
the batch summary implied a coverage it did not have. `README.md` in this
directory states that a declined proposal keeps its file and its reason, so
omitting one contradicted the policy shipped alongside it. Recorded now, with
the correction, because a triage that discards what it does not act on is not a
record.
