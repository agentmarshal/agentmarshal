# ADR-0011: A contract shows that it changed, and a review says which contract it judged

Status: Accepted
Date: 2026-09-16

Supersedes nothing. Builds on [ADR-0004](ADR-0004-journal-data-model.md) (a
contract is a document, evidence is records) and
[ADR-0006](ADR-0006-actors-and-identity.md) (a record names who wrote it).

## Context

A task's contract is a document. An amendment to it is a record: append-only,
timestamped, attributed, with a mandatory reason. That split is deliberate and
it is right.

The reviewer is given the contract text and the diff. It is not given the
amendment records, although they sit in the same task directory. A criterion
written at open time and a criterion added after two review rounds are
byte-identical in the review prompt.

An adopter reported this with measurements
([proposal 022](../proposals/022-amendments-invisible-to-the-reviewer.md)): six
amendments across four tasks, five of them recorded after implementation had
begun, nine reviews rendered against an already-amended contract, and none of
the six visible to the reviewer at verdict time. This project's own journal is
larger and no better: **21 amendment records across 18 of 91 completed tasks**,
including a contract amended between the second and third review round of its
own task, after a reviewer raised a blocking finding about the wording of a
criterion. Rounds three and four then judged the work against the amended text
with no way to know it had changed.

It is worth being exact about what is and is not broken, because the obvious
framing overstates it.

The evidence is intact. The records exist, they are append-only, and each
carries its reason. Nor can a candidate be judged against a contract it has not
incorporated: the gate reads the contract from the merge-base tree, the reviewer
reads it from the reviewed commit's snapshot, and a review is bound to the SHA
it judged. An amendment that lands while a candidate is in flight applies to
that candidate only once the candidate merges it, and that merge changes the
SHA — and a verdict about the earlier SHA does not speak for the new one.

What is broken is narrower and harder to see: **the one party we deliberately
keep independent is the one party not told that the document it is judging
against has a history.** That matters most in precisely the case that occurs
most — the text changed because the previous round objected to it — and it is
the case where an independent opinion is worth the most.

In a sidecar the reasoning is different and the exposure is larger. There the
contract is read from the sidecar's own working tree rather than from the
candidate's history, so nothing binds it to a SHA at all: the text can change
under an approved candidate with no commit anywhere in the host.

## Decision

### 1. `amend` maintains a visible history inside the contract document

`agentmarshal amend` appends an entry to a reserved section at the end of
`contract.md`: when, by whom, and the reason it already requires. The tool
maintains the section; the operator does not write it by hand.

The section answers *was this changed, when, by whom, and why*. It does not
answer *what changed*: the document's own version history holds that, and a
diff copied into the document would rot on the first edit.

### 2. Everything that reads the contract inherits the history

Nothing changes in the brief, the review prompt, or the gate's contract read.
They read the document, and the document now carries its history. That is the
whole reason for putting the projection in the document rather than in the
prompt: the implementer working from a brief has the same right to know that a
criterion is three days younger than the task.

### 3. The projection is checked against the records

`validate` and the gate compare the history section against the task's
amendment records, and refuse when they disagree, naming the task.

A visible history that nobody checks is a claim, not evidence. The record stays
the evidence; the section is a rendering of it that does not drift past
`validate` or the gate unnoticed, and the two check each other.

Sides and absence, stated so no reader has to guess:

- The gate reads the contract as it reads it today — from the merge-base tree
  in an embedded journal, from the sidecar's working tree in a sidecar — and
  the amendment records from the journal it is gating.
- A contract with no amendment records needs no section, and its absence is
  not a finding.
- An amendment is a journal-only transaction, and the document and the record
  it writes travel in it together; no lane sees one without the other.
- A contract that has amendment records and no matching section is a refusal,
  **for amendment records written after this decision ships**. Records written
  before it are ignored by the check: a closed task is not reopened to satisfy
  a rule it predates, and an append-only journal cannot be retrofitted.

### 4. A review record names the contract it judged

A review record carries `reviewed_contract`: the sha256 of the contract text
the reviewer was given. The field is optional; a record written before this
decision does not have it, and its absence is never a violation.

The field is read where every review record is read, and it is covered by the
same append-only rule as the rest of the record: a change to it after the fact is
tampering, and needs no rule of its own here.

Two things become answerable that are not answerable today: which text a given
verdict was about, and how amendments fall relative to review rounds across a
whole journal. The second is a measurement about how well contracts are being
written, and it costs one field.

### 5. The gate adds no new refusal for an amendment after a review

Considered and rejected for the embedded journal. SHA binding already covers
it: to be judged against an amended contract a candidate must incorporate the
amendment, which changes its SHA, and no verdict about the earlier SHA speaks
for the new one. A second refusal would cost a paid review round for a typo and
protect nothing that is not already protected.

In a sidecar, where no SHA binds the contract, the gate compares the approving
review's `reviewed_contract` with the contract it read and reports a mismatch
**as an advisory line**, under the notice that already says every sidecar check
is advisory. The exposure is real there, but a sidecar gate advises; it does
not refuse. Making this one line the exception would be a change to what a
sidecar gate is, and that is not what an adopter's proposal about review prompts
should be allowed to decide.

### 6. What this does not decide

- Whether an amendment needs its own review. It does not: the reason is
  mandatory, and it is now visible to the next reviewer, which is the cheaper
  half of the same goal.
- Whether a reviewer should be shown *what* changed. It should not: the
  reviewer is given a snapshot, not a repository, and the question it is being
  asked is about the work, not about the document's drafting.
- Anything about the findings lane. A finding record is not judged against a
  contract, and nothing here applies to it.

## Consequences

The reviewer and the implementer both see, in the document they are given, that
it was amended, when and why. A hand-edited history section becomes a refusal,
which is a new way for an operator to be stopped; that is the price of the
section being evidence rather than decoration.

`amend` now writes in two places instead of one, and the document it writes into
is one an operator may also be editing. The command owns the section; an
operator who edits it is refused by `validate` before the gate ever sees it.

Old tasks are untouched. New amendments carry the section. A journal that never
amends anything sees no change at all, and its transcripts stay byte-identical.

## Alternatives considered

**Render the amendment records into the review prompt and nothing else.**
Simplest, and it is what the reporter offered as the cheaper path. Rejected
because it informs exactly one consumer: the implementer's brief, and every
future reader of the contract, would still see a document with no history.

**Require a review of every amendment.** Turns contract repair into a two-round
process and would have made each of this project's 21 amendments a paid
transaction. The defect is invisibility, not insufficient ceremony.

**Refuse any amendment once a review record exists.** Forbids the legitimate and
common case: a review exposes a contradiction in the contract, and the contract
is repaired. That is the process working, not failing.

**Do nothing, because the records already exist.** They exist for whoever reads
the journal later. The party being asked for an independent judgement needs them
at the moment of judgement, and that is the moment we were withholding them.
