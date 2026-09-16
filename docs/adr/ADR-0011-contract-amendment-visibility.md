# ADR-0011: A contract shows that it changed, and a review says which contract it judged

Status: Accepted
Date: 2026-09-16

Supersedes nothing. Builds on [ADR-0004](ADR-0004-journal-data-model.md) (a
contract is a document, evidence is records) and
[ADR-0006](ADR-0006-actors-and-identity.md) (a record names who wrote it).

This ADR records a decision. The rendering, the record field and the reading it
describes are **not implemented by this document**; they follow in their own
task. The present tense below is how a decision is written, not a claim about
shipped behaviour.

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
larger and no better: **21 amendment records across 18 of the 92 tasks
completed when this was written**,
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

### 1. The history is rendered where the contract is delivered, from the records

The review prompt and the implementer's brief render the task's amendment
records alongside the contract they already carry. Each entry says when, why —
the reason an amendment record requires — and who recorded it, when the record
names an actor; older records may not, which is why the rendering states what
it has rather than promising three fields.

The records are read from the journal the command is working in: the working
tree in an embedded journal, the sidecar's journal in a sidecar.

Whether that is the same side the contract comes from depends on the placement,
and the difference is worth naming rather than smoothing over. In an embedded
journal the review prompt takes the contract from the reviewed commit's
snapshot while the records come from the working tree, so the two sides differ.
In a sidecar both come from the sidecar's working tree, and they do not.

The asymmetry in the embedded case is deliberate. An amendment is evidence about
the task, not about the candidate, and a reviewer asked whether a criterion is
new needs the history as it stands when the verdict is given, including an
amendment recorded after the candidate was built. Reading the records from the
snapshot would hide exactly those.

It follows that a rendering can name an amendment the contract text beside it
does not yet reflect. That is the signal rather than a defect: the contract has
moved since the candidate incorporated it, and the reviewer is told so instead
of being left to judge a text whose history it cannot see. Nothing here makes
the candidate take the newer text — the gate reads the contract from the
merge-base tree, so a candidate that has not merged the amendment is judged
against the contract it did incorporate.

The rendering is built from the records, which are JSON, and never from prose.
That is not an implementation detail. [ADR-0004](ADR-0004-journal-data-model.md)
D3 says the record is the source of truth for machines and that **gates never
parse prose**, and an earlier draft of this decision asked exactly that of the
gate. Rendering records into a prompt respects the split; parsing a prose
section in order to decide something does not.

It answers *was this changed, when, by whom, and why*. It does not answer *what
changed*: the document's own version history holds that, and the reviewer is
handed a snapshot rather than a repository.

### 2. The contract document stays what the operator writes

`amend` does not edit `contract.md`. There is no maintained section, no
reserved heading, and nothing in the document that a tool has to keep in step
with the records.

This is the opposite of what an earlier draft decided, and the reason is worth
keeping. A rendered section inside the document would be a second copy of the
records that no rule could check without parsing prose, and an unchecked copy
is a claim rather than evidence. An operator who wants that history in the
document may write it; it then carries the weight of any other sentence an
operator writes there, and nothing reads it back.

### 3. The gate gains no check, and its transcript does not change

This decision adds no line to the gate. In an embedded journal that is because
the existing rules already cover what can be covered: amendment records are
append-only evidence, and a candidate cannot be judged against a contract it
has not incorporated, since the gate reads the contract from the merge-base
tree and a review is bound to the SHA it judged. In a sidecar none of that
reasoning holds — the contract comes from the sidecar's working tree and no SHA
binds it — and the answer there is not that the exposure is covered but that
this decision does not close it; Decision 5 says so and leaves the question
open.

What this decision changes is what the deciding party is *shown*, not what the
gate refuses. That is its honest scope, and it is why no question about
transcripts arises.

### 4. A review record names the contract it judged

A review record carries `reviewed_contract`: the sha256 of the contract text
the reviewer was given, in the lowercase hex every other digest in this journal
uses.

Adding it raises the review record's schema number. Record validation is
closed — a record carrying a field its schema does not allow is refused — so a
new field arrives the way every other one has, through a version, and records
written under the previous schema keep it and are read as they were. As with
the version before it ([ADR-0004](ADR-0004-journal-data-model.md)), a writer
stamps the new schema only on a record that carries the field and keeps the
current one as the floor for the rest.

The field is optional within its schema, and the case it is optional for is the
human path: `submit-review` records a verdict without a prompt, so there is no
contract the tool handed anyone and nothing it can honestly hash. The launcher
always has one. An absence is therefore never a violation and never a line
anywhere.

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

In a sidecar — the placement [ADR-0008](ADR-0008-journal-placements.md)
defines, where the gate advises and decides no merge, and where the contract is
read from the sidecar's own working tree — no SHA binds the contract. The
exposure is real and this decision still adds no gate line. What it adds there is the evidence to see the
problem afterwards: an approving review names the contract it judged, so a
reader can compare that with the contract as it now stands. Whether a sidecar
gate should say anything when the field is present and differs is left to the
task that implements this. Absence is not part of that question: Decision 4
settles it, and a check that read a missing field as suspicion would condemn
every record written before this decision. Making a sidecar line the one
exception to a gate that advises would also change what a sidecar gate is, and
that is not what a record about review prompts should decide.

### 6. What is settled here, and what is left open

One question is genuinely open, and Decision 5 names it: whether a sidecar gate
should say anything when an approving review carries a `reviewed_contract` that
differs from the contract it reads. It belongs to the task that implements
this.

The rest of this section settles small questions rather than leaving them:

- Whether an amendment needs its own review. It does not: the reason is
  mandatory, and it is now visible to the next reviewer, which is the cheaper
  half of the same goal.
- Whether a reviewer should be shown *what* changed. It should not: the
  reviewer is given a snapshot, not a repository, and the question it is being
  asked is about the work, not about the document's drafting.
- What the findings lane does with any of this is not settled here. The task
  that carries this decision put that lane outside its scope, and a record
  should not decide what its own contract excluded; the question is a real one
  and belongs to whoever opens it.

## Consequences

The reviewer and the implementer are both told that the contract was amended,
when and why, in the material they are already handed. A task with no
amendments has nothing to render, and nothing about it changes.

`amend` gains nothing and the contract document gains nothing, so there is no
new way for an operator to be stopped and no second copy to keep in step. The
prompt and the brief grow by a few lines per amendment, which is the whole cost.

The review record grows one optional field. That is the only part of this
decision that reaches a journal which has never amended anything, and it puts
no line in any transcript.

## Alternatives considered

**A maintained history section inside the contract document.** The reporter's
preferred shape, and the first draft of this decision. Rejected once it was
clear what holding it to the records would cost: a rendered section is a second
copy, and nothing could check it without parsing prose, which
[ADR-0004](ADR-0004-journal-data-model.md) D3 forbids a gate to do. An unchecked
copy inside the document a reviewer judges against is worse than none, because
it looks authoritative.

**Require a review of every amendment.** Turns contract repair into a two-round
process and would have made each of this project's 21 amendments a paid
transaction. The defect is invisibility, not insufficient ceremony.

**Refuse any amendment once a review record exists.** Forbids the legitimate and
common case: a review exposes a contradiction in the contract, and the contract
is repaired. That is the process working, not failing.

**Do nothing, because the records already exist.** They exist for whoever reads
the journal later. The party being asked for an independent judgement needs them
at the moment of judgement, and that is the moment we were withholding them.
