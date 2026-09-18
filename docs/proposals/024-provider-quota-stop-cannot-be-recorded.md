# 024 — A provider quota stop cannot be recorded, so a model choice rests on inference

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:8c807aabe08af886625fdf8abefc02c7cdca2813d7ed1a06437b44e8717be135` · **Disposition:** accepted *(in part; the reset-time field is deferred)*

## Finding

The reporter compared three executor models across twelve governed tasks
using the session records' token counts. The comparison could not be settled
with them: the provider meters an allowance in its own units that refills on
its own schedule, and that allowance — not the token count — is what stops
work.

Two runs ended because the provider refused to continue. Each is a session
whose `outcome` is free text and whose token counts are empty, which a reader
cannot tell from a run that failed for any other reason. Both refusals stated
when the allowance would reset; the journal kept neither. The decision rested
on how much each model consumed before a refusal — a ratio held outside the
journal. The token counts inside it point the other way: counted in tokens, the
rejected model is six times cheaper.

Measurements, as reported:

- Implementer sessions recorded: **13**, across **12** tasks and **3** models.
- Sessions that ended because the provider refused further work: **2**. Token
  counts recorded for them: **0**.
- Sessions where the provider stated a reset time in its refusal: **2 of 2**.
  Reset times retained in the journal: **0**.
- Tokens consumed before refusal, by model, reconstructed from outside the
  journal: **~0.67M** for one model, **>27.5M without refusal** for another.
- Records able to express "stopped by the provider's allowance": **0**.

## Proposed

1. Distinguish a provider stop from a crash with a documented `outcome`
   vocabulary — for example `provider-limit` — so journals compare between
   adopters.
2. Keep the reset time the provider stated, in an optional field of the
   session record beside the usage block.
3. Say plainly in the documentation that tokens are not cost for an executor
   metered in provider units.

## Disposition — accepted for the vocabulary and the statement, deferred for the field

The finding is right about what the journal measures. A session record carries
tokens and their provenance; the thing that stopped the reporter's work, and
decided their choice of model, was something else, and the journal had no
place for it. Our own documentation made it worse by calling the token record
what a task cost.

**The statement** is accepted and made in this intake: the quickstart's step on
recording a session says that token counts are what the record measures, not
what a provider charges, and the README no longer calls them what each task
cost.

**The vocabulary** is accepted as documentation, which is what the reporter
asked for. The quickstart names `provider-limit` as the outcome for a session
the provider refused to continue. `outcome` stays free text: the tool neither
checks the value nor counts it in `report`, and this intake does not change
that. Agreeing on the word is what lets two journals be compared; making the
tool enforce or aggregate it is a change of behaviour, and belongs with the
accounting rework below.

**The reset-time field** is deferred, for the reason proposal 018's cost field
is. A new session field is a record schema change, and 0.4.0 already asked
every adopter for a coordinated upgrade over three new schemas. What a session
record should say about a provider's meter — its units, its window, when it
refills — is one question, and it belongs with the rework of accounting that
018 deferred, not answered one field at a time. That rework is not scheduled in
any published release yet.

## Where

The statement and the vocabulary are on the default branch and ship with the
next release. The field waits for the accounting rework.
