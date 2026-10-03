# ADR-0018: Governing the contract

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0005](ADR-0005-evidence-capture-and-format.md) (the fields
the in-toto projection needs — the committed contract's hash among those
derived from history, not stored),
[ADR-0006](ADR-0006-actors-and-identity.md) (actors are declared, never
authenticated; the decision-rights policies, distinct-actor review among
them, are designed and off),
[ADR-0008](ADR-0008-journal-placements.md) (the sidecar placement, in
which the contract is versioned in a repository of its own) and
[ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)
(a new field arrives under the schema that introduces it — record fields
under the record schemas, contract-header fields under the contract's
own numbering). **It revises ADR-0005**: the contract's hash is stored,
not derived. It answers
[proposal 031](../proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md),
[proposal 033](../proposals/033-contract-review-before-implementation-does-not-pay-off.md)
and
[proposal 034](../proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md).

This ADR records a decision. The record fields, contract-header fields,
gate checks and status displays it describes are **not implemented by
this document**; they follow in their own tasks. The present tense below
is how a decision is written, not a claim about shipped behaviour.

## Context

Everything the gate enforces is relative to the contract: the scope and
the acceptance criteria come from it, and a verdict means "this candidate
satisfies the contract" and nothing more. The evidence about the contract
itself is thinner than the evidence built on it:

- Only a review the `review` command launched carries the contract's
  hash: `reviewed_contract`, the sha256 of the text the reviewer was
  given
  ([ADR-0011](ADR-0011-contract-amendment-visibility.md), `review.py`).
  A verdict recorded through `submit-review` carries none — the tool
  handed no contract to anyone, so there is nothing it can honestly hash.
  `opened` and `amendment` carry no hash at all (`records.py`): ADR-0005
  counts the committed contract's hash among the fields computed from
  history at projection time rather than stored.
- The gate's one independence check compares the declared reviewer email
  against the declared author and committer addresses of the candidate's
  `merge-base..candidate` commits (`gate.py`): it refuses a reviewer who
  wrote the candidate, and can check nothing else — not that the reviewer
  was the intended one, not independence by vendor or model.
- Actors carry no roles: the optional `actors` section of `project.json`
  maps an actor id to the git identities that resolve to it (`actors.py`),
  and [ADR-0006](ADR-0006-actors-and-identity.md)'s decision-rights
  policies are deferred and off.

Three proposals press on this:

- [proposal 031](../proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md):
  in an agent-driven loop the contract is written by an agent and nothing
  governs it — 21 amendments across the reporter's 43 governed tasks and
  zero records of agreement, because no record type exists for it; and
  the case the reporter generalises, a negative requirement satisfied by
  destroying its subject, correctly approved because the code matched the
  contract;
- [proposal 034](../proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md):
  the contract does not name its implementer and reviewer — six mid-task
  implementer switches over 69 tasks, and the choice expressed only in
  the launch wrappers' environment variables;
- [proposal 033](../proposals/033-contract-review-before-implementation-does-not-pay-off.md):
  the same reporter built the pre-implementation contract review that
  proposal 031's third suggestion offered, measured seven review passes
  over one contract — $27.02 and about 95 minutes, the cost higher than
  that of any of the six complete candidate-review cycles run the same
  day — without the task ever reaching an implementer, and withdrew the
  suggestion.

## Decision

### 1. The contract's hash is pinned where it is written

The `opened` record and every `amendment` record carry the sha256 of the
contract text they establish, in the lowercase hex `reviewed_contract`
already uses.

**This revises [ADR-0005](ADR-0005-evidence-capture-and-format.md)** and
says so. ADR-0005 derives the committed contract's hash from history, on
the ground that a field computed at projection time cannot be turned off.
The derivation assumes the contract lives in the history being read, and
in the sidecar placement it does not: the contract is versioned in the
sidecar's own repository
([ADR-0008](ADR-0008-journal-placements.md)), and the host's history has
no text to derive it from. Stored instead, the hash also lets `brief` and
`report` say which version of the contract a candidate was built against
with no access to history at all.

### 2. Agreement with the contract can be recorded

A record exists for it: a declared actor states agreement with the
contract at a stated hash.

The gate does not require the record by default. What changes without the
requirement is visibility: its absence is shown in `status`, instead of
being indistinguishable from agreement never asked for, and a project
whose rules demand agreement — the reporter's do — can make the record
required.

Any declared actor may record it, and `status` shows who did. There are
no roles: binding "who may agree" to a role would be a permission over
unauthenticated identity — the appearance of a control, which is the
reason [ADR-0006](ADR-0006-actors-and-identity.md) deferred roles until
signing. Roles arrive with signing; this decision introduces none.

### 3. The contract may name who implements and who reviews

The contract header gains fields under a new contract schema — the header
has a schema numbering of its own, and a new field arrives under the
schema that introduces it
([ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)):

- the permitted implementers and the permitted reviewers, each an ordered
  list of declared actors — the order is the fallback order;
- the independence rules in force, from a fixed vocabulary: the reviewer
  is not an author or committer of the candidate's commits — today's
  check; the reviewer is a different declared actor than the implementer —
  the distinct-actor policy
  [ADR-0006](ADR-0006-actors-and-identity.md) designs and leaves off; the
  reviewer's vendor differs from the implementers' vendors; the model
  differs.

For the last two rules to be checkable, an implementer session records
which vendor and model did the work and which commit the session
produced; today a session's `actor` is a free string (`records.py`). What
is recorded is decided here; the fields themselves arrive with the later
decision on the record model.

The gate checks membership and the rules: the review that makes a
candidate mergeable comes from a permitted reviewer and satisfies the
declared independence rules against the implementers whose commits the
candidate carries. It does not check why a run fell back to a later entry
in a list — the reason for a fallback is shown, not verified. `status`
shows the declared assignment next to what actually ran, and a change to
the lists or the rules is a contract amendment like any other.

The guarantee is "declared and cross-checked", not "proven": the record
of who implemented is written by an agent, and an actor is a declared
label until signing exists
([ADR-0006](ADR-0006-actors-and-identity.md)).

### 4. No review of the contract before implementation

[Proposal 031](../proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md)'s
third suggestion — pointing the reviewer at the contract before
implementation — is not taken: its reporter built it, measured it and
withdrew it
([proposal 033](../proposals/033-contract-review-before-implementation-does-not-pay-off.md)).
A contract has nothing to be checked against, so the review has no
stopping point. What is kept is the evidence: the retraction travels with
its measurements, so the next project does not rerun the experiment.

## Consequences

- The measure the work is judged against becomes auditable end to end:
  the hash is pinned at opening, at every amendment and at every launched
  review, and `brief` and `report` can say which text a candidate was
  built and judged against — including where no shared history exists to
  ask.
- Agreement becomes a fact the journal can hold, and its absence a
  visible fact rather than silence; a project that requires it can
  enforce the requirement.
- The assignment moves from environment variables into the reviewed
  document: checked by the gate, shown next to what ran, changed only by
  amendment — the trace proposal 034 found missing.
- Nothing here strengthens what identity means: everything is declared
  and cross-checked, and it stays so until signing exists.
- The new fields arrive under the schema that introduces each — those on
  `opened`, `amendment`, the agreement record and the implementer session
  under the record schemas, the header fields under the contract's own
  ([ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md)).
  What is recorded is decided here; names and numbers belong to the later
  decision on the record model.

## Alternatives considered

**Keep deriving the contract hash from history.** Still right for the
fields ADR-0005 named — commit digests, writer identities — which live in
the history every placement shares. The contract does not: a sidecar
versions it in a repository of its own. Derivation stays the rule where
derivation is possible; the contract hash is the exception because there
it is not.

**Require the agreement record by default.** Refused: a project that
never needed one would pay a record per task for nothing, and the absence
already shows in `status` — visibility, not the requirement, is the
default's job. The switch belongs to the project, like
[ADR-0006](ADR-0006-actors-and-identity.md)'s decision-rights policies.

**Roles in the actors table now.** Refused: binding the right to agree —
or to review — to a role asserts a control the journal cannot check until
records are signed, and ADR-0006's reasoning stands: an unenforceable
claim shown as enforced is worse than none. Any declared actor may agree,
and `status` says who did.

**Check the reason a fallback was taken.** Refused: the gate checks what
can be checked — membership in the lists and the declared independence
rules. The reason a run moved down the list is shown so a person can
judge it; the gate does not evaluate whether a provider limit really
happened.

## Corrections

- 2026-10-03: the Context read the contract review's cost and its minutes
  as both exceeding the day's six candidate-review cycles;
  [proposal 033](../proposals/033-contract-review-before-implementation-does-not-pay-off.md)
  measured the comparison in cost only, and the sentence now claims only
  that.
