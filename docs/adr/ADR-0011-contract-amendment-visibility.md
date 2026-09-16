# ADR-0011: A contract shows that it changed, and a review says which contract it judged

Status: Accepted
Date: 2026-09-16

Builds on [ADR-0004](ADR-0004-journal-data-model.md) (a contract is a document,
evidence is records) and [ADR-0006](ADR-0006-actors-and-identity.md) (a record
names who wrote it).

This ADR records a decision. The rendering and the record field it describes are
**not implemented by this document**; they follow in their own task. The present
tense below is how a decision is written, not a claim about shipped behaviour.

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
begun, nine reviews rendered against an already-amended contract, none of the
six visible to the reviewer at verdict time. This project's own journal is
larger and no better: **21 amendment records across 18 of the 92 tasks completed
when this was written**, including a contract amended between the second and
third review round of its own task, after a reviewer raised a blocking finding
about the wording of a criterion. Rounds three and four then judged the work
against the amended text with no way to know it had changed.

What is broken is narrower than it first looks, and worth stating exactly. The
evidence is intact: the records exist, they are append-only, each carries its
reason. Nor can a candidate be judged against a contract it has not
incorporated — the gate reads the contract from the merge-base tree, and a
review is bound to the SHA it judged. What is broken is that **the one party we
deliberately keep independent is the one party not told that the document it is
judging against has a history.** That matters most in the case that occurs most:
the text changed because the previous round objected to it.

## Decision

### 1. The history is rendered from the records, where the contract is delivered

The review prompt and the implementer's brief render the task's amendment
records alongside the contract they already carry. Each entry says when, why —
the reason an amendment record requires — and who recorded it, when the record
names an actor.

The records are read from the journal the command is working in: the working
tree in an embedded journal, the sidecar's journal in a sidecar. In an embedded
journal that is not where the prompt's contract comes from, which is the
reviewed commit's snapshot, and the difference is deliberate: an amendment is
evidence about the task, not about the candidate, and a reviewer asked whether a
criterion is new needs the history as it stands when the verdict is given —
including an amendment recorded after the candidate was built.

The rendering is built from the records, which are JSON, and never from prose.
That is not an implementation detail. [ADR-0004](ADR-0004-journal-data-model.md)
D3 says the record is the source of truth for machines and that **gates never
parse prose**, and an earlier draft of this decision asked exactly that of the
gate.

### 2. The tool does not write into the contract document

`amend` does not edit `contract.md`. There is no maintained section and nothing
in the document a tool has to keep in step with the records.

A rendered section inside the document would be a second copy of the records
that nothing could check without parsing prose. An unchecked copy inside the
document a reviewer judges against is worse than none, because it looks
authoritative.

### 3. The gate is unchanged

This decision adds no check and no line to the gate, in any placement and on
any lane. What it changes is what the deciding party is *shown*, not what the
gate refuses.

Nor does it add a refusal for an amendment recorded after a review. In an
embedded journal that case is already covered: to be judged against an amended
contract a candidate must incorporate the amendment, which changes its SHA, and
no verdict about the earlier SHA speaks for the new one. A further refusal would
cost a paid review round for a typo.

A sidecar is different and this decision does not close it. There the contract
is read from the sidecar's own working tree; it is versioned in the sidecar's
history ([ADR-0008](ADR-0008-journal-placements.md)), but nothing ties the text
the gate read to the host commit it was judging, so the text can change under an
approved candidate with no host commit anywhere. What this decision gives that
placement is the evidence to see it afterwards, through the field below, and not
a gate line.

### 4. A review record names the contract it judged

A review record carries `reviewed_contract`: the sha256 of the contract text the
reviewer was given, in the lowercase hex every other digest in this journal
uses.

Adding it raises the review record's schema number. Record validation is closed
— a record carrying a field its schema does not allow is refused — so a new
field arrives through a version, and records written under the previous schema
keep it and are read as they were. As with the version before it
([ADR-0004](ADR-0004-journal-data-model.md)), a writer stamps the new schema
only on a record that carries the field and keeps the current one as the floor.

The field is optional within its schema, and the case it is optional for is the
human path: `submit-review` records a verdict without a prompt, so there is no
contract the tool handed anyone and nothing it can honestly hash. An absence is
never a violation and never a line anywhere.

## Left open

Whether a sidecar gate should say anything when an approving review carries a
`reviewed_contract` that differs from the contract it reads. It belongs to the
task that implements this decision.

What the findings lane does with any of it is also unsettled: the task carrying
this decision put that lane outside its scope, and a record should not decide
what its own contract excluded.

## Consequences

The reviewer and the implementer are both told that the contract was amended,
when and why, in the material they are already handed. A task with no
amendments has nothing to render and nothing about it changes.

`amend` gains nothing and the contract document gains nothing, so there is no
new way for an operator to be stopped and no second copy to keep in step. The
prompt and the brief grow by a few lines per amendment.

The review record grows one optional field under a new schema number. That is
the only part of this decision that reaches a journal which has never amended
anything.

## Alternatives considered

**A maintained history section inside the contract document.** The reporter's
preferred shape, and the first draft of this decision. Rejected once it was
clear what holding it to the records would cost: nothing could check it without
parsing prose, which ADR-0004 D3 forbids a gate to do.

**Require a review of every amendment.** Turns contract repair into a two-round
process, and would have made each of this project's 21 amendments a paid
transaction. The defect is invisibility, not insufficient ceremony.

**Refuse any amendment once a review record exists.** Forbids the legitimate and
common case: a review exposes a contradiction in the contract, and the contract
is repaired. That is the process working, not failing.
