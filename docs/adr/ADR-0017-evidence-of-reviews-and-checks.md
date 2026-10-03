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
`check` record is admitted after any terminal record — completed or
abandoned — on a par with `session`: it joins the measurements the
projection, the writer and the gate admit post-terminal, and the gate
transcript's line for a measurements-only append on a task closed at
base names it. It answers
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
   ([ADR-0014](ADR-0014-where-things-live.md)). **A `check` record is
   admitted after any terminal record — completed or abandoned — on a
   par with `session`**: it is a measurement, not lifecycle. Today
   `session` is admitted after either terminal state and `reopened`
   after completion only (`status.py`, the
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
   carries an optional evidence reference — a link, a `file:line`, or
   the command that checked the claim with the essential part of its
   output. And a line of the review protocol: a finding about an
   external fact the reviewer could not check is advisory —
   "unconfirmed".

## Left open

The snapshot-preparation command for review
([proposal 030](../proposals/030-review-verdicts-do-not-say-what-was-executed.md)'s
optional part): it changes the snapshot rather than pausing the process,
so [ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md)'s
stage rule does not cover it — it takes a decision of its own, when an
adopter asks for it.

## Consequences

- [proposal 028](../proposals/028-check-outcomes-are-not-evidence.md)
  gets its answer: a failing run leaves a trace — what check ran, the
  step that failed and an excerpt of its output — and a candidate the
  pipeline refused is no longer indistinguishable from one never
  submitted. A skipped check is recorded too.
- The brief carries facts, not only the reviewer's opinion: `brief`
  names the task's latest failing `check`, and `report` counts the
  candidates the pipeline rejected, so the cost of a refusal is
  countable next to rounds and cost.
- [proposal 030](../proposals/030-review-verdicts-do-not-say-what-was-executed.md)
  gets its answer: the verdict distinguishes what the reviewer ran from
  what it only read — the two kinds of confirmation no longer produce
  the same word. Its optional part, the snapshot-preparation command,
  stays open.
- [proposal 026](../proposals/026-reviewer-facts-round-convergence-and-two-gaps.md)'s
  first finding gets its answer: a finding about an external fact
  carries its evidence or lands as advisory.
- What a `check` record guarantees is what its observer declares: a
  trace of what happened, not a proof. Nothing downstream re-verifies
  it, and nothing in the gate trusts it.
- The record lifecycle gains a measurement: the projection, the writer
  and the gate admit `check` post-terminal together, and the gate's
  transcript line for a measurements-only append names it.

## Alternatives considered

**The gate decides from `check` records.** Rejected: what the
attestation trusts stays with the attestation mode — the invoker's SHA
or the provider's required checks. A record carries an observer's
declaration, and letting the gate read it would lend the declaration a
weight this decision refuses it.

**Check outcomes stay in the provider's CI output.** Rejected: the
provider's retention decides how long a run's log survives, and the
journal would hold nothing showing the pipeline ran and refused — the
silence
[proposal 028](../proposals/028-check-outcomes-are-not-evidence.md)
measured.

**A store for check outcomes outside the journal.** Rejected: the full
output already has its place — the process log
([ADR-0014](ADR-0014-where-things-live.md)). What the journal keeps is
the outcome, where `brief` and `report` already read.
