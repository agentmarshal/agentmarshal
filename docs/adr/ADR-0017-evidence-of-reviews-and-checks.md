# ADR-0017: The evidence of reviews and checks

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0004](ADR-0004-journal-data-model.md) (append-only records
carry the evidence a gate decides from),
[ADR-0005](ADR-0005-evidence-capture-and-format.md) (measurements are not
lifecycle; the evidence-capture policy) and
[ADR-0014](ADR-0014-where-things-live.md) (the process log holds what the
journal must not). **It partly revises the
[record-lifecycle](../../openspec/specs/record-lifecycle/spec.md) and
[gate-lanes](../../openspec/specs/gate-lanes/spec.md) specifications**: a
check record is admitted after a terminal record — it joins the
measurements the projection, the writer and the gate admit post-terminal —
and the gate transcript's line for a measurements-only append on a task
closed at base names it. It answers
[proposal 028](../proposals/028-check-outcomes-are-not-evidence.md),
[proposal 030](../proposals/030-review-verdicts-do-not-say-what-was-executed.md)
and
[proposal 026](../proposals/026-reviewer-facts-round-convergence-and-two-gaps.md)'s
first finding.

This ADR records a decision. The record type, the command, the brief and
report lines, the protocol additions and the specification changes it
describes are **not implemented by this document**; they follow in their
own tasks. The present tense below is how a decision is written, not a
claim about shipped behaviour.

## Context

How it works today:

- no record stores whether the pipeline passed; indirectly, a `completed`
  record exists only because `complete` runs the gate itself and records
  completion when the gate passes (`complete.py`);
- what the pipeline-attestation check trusts depends on the mode: the
  default, `--attestation commit`, trusts the SHA the invoker reports —
  `pipeline_sha` must equal the candidate commit; `ci-required` delegates
  the attestation to the provider's required checks (`gate.py`,
  `docs/quickstart.md`);
- a failed run leaves nothing — no record, no reason, no count;
- the reviewer works on a snapshot of the candidate tree made with
  `git archive`, with no installed dependencies (`review.py`), and the
  verdict it records — `approved`, `changes_required`, `blocked` or
  `rejected`, with blocking and advisory finding ids — does not
  distinguish what the reviewer ran from what it only read.

## Decision

1. **A `check` record.** It records the task, the commit, the check's
   name, the outcome (`passed`, `failed`, `error`, `skipped`), the step
   that failed, a short excerpt — truncated, passed through leak-scan and
   the forgeable-text rule — and the source: a link to the run at the
   provider. Whoever observed the run writes it with `record-check`; the
   record travels with the task's next journal transaction, and the full
   output goes to the process log
   ([ADR-0014](ADR-0014-where-things-live.md)). **A `check` record is also
   admitted after the task's completion** — as a measurement, on a par
   with `session`: today only `session` and `reopened` are admitted after
   a terminal record (`status.py`, the
   [record-lifecycle](../../openspec/specs/record-lifecycle/spec.md)
   specification). The record model that names the fields is a later
   decision — under
   [ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md),
   new fields arrive under a single record schema.
2. **The gate decides nothing from a `check` record.** What the
   attestation trusts stays as today — the invoker's SHA or the provider's
   required checks, by mode. The record is a trace of what happened:
   declared by the observer, not proven.
3. **`brief` carries the last failing `check`** of the task; **`report`
   counts the candidates the pipeline rejected**, next to rounds and
   cost.
4. **The verdict says what was executed and what was read:** an optional
   section of the reviewer protocol — what the reviewer ran and with what
   result, what it checked by reading only, and what it could not run and
   why.
5. **External facts carry evidence or stand aside.** A review finding
   carries an optional evidence reference — a link or a `file:line`. And
   a line of the review protocol: a finding about an external fact the
   reviewer could not check is advisory — "unconfirmed".

## Left open

The snapshot-preparation command for review
([proposal 030](../proposals/030-review-verdicts-do-not-say-what-was-executed.md)'s
optional part): it changes the snapshot rather than pausing the process,
so [ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md)'s
stage rule does not cover it — it takes a decision of its own, when an
adopter asks for it.
