# 022 — Contract amendments are invisible to the reviewer that judges the work against the contract

- **Reporter:** Adopter D (greenfield project on Linux, GitHub, agent-driven loop with three paid roles) · **Observed on:** 0.3.0 · **Source:** `sha256:688e569ec6de9307` · **Disposition:** accepted

## Finding

The review prompt carries the contract text and the diff. It does not carry the
task's amendment records, although they live in the same task directory and hold
exactly what a reviewer needs in order to judge the criteria it is being asked
to check: whether they were written before the work or after it, when, and why.

An amendment changes the document. The record of it is evidence. The reviewer is
handed the changed document with no indication that it changed. A criterion
added after two review rounds and a criterion written at open time are
byte-identical in the prompt.

This matters more in an agent-driven loop than it would with human authors,
because the party that amends the contract is usually the same party that
orchestrates the implementer and requests the review. The gate's base-side
contract read is a real protection against a *candidate* widening its own scope.
Nothing plays the equivalent role for the base: an orchestrator can widen,
soften or retarget a criterion between rounds, land it through a legitimate
journal transaction, and the next review will assess the work against the new
text as though it had always said that. The one reader positioned to notice is
the reviewer, and it is the one reader not told.

Measurements, as reported, from the reporter's first five governed tasks:

- Amendments recorded: **6**, across **4** tasks.
- Recorded **after** implementation had begun: **5 of 6**.
- Reviews recorded against an already-amended contract: **9**.
- Amendments visible to the reviewer at verdict time: **0 of 6**.
- Classified by intent: 1 repair of a factually wrong statement, 2 resolutions
  of a contradiction between the contract and the tool's own rules, 3 additions
  of work. **None lowered a criterion** — and, as the reporter notes, that
  classification is the amending party's own claim about itself, which is
  precisely the claim a reviewer could have checked and was never given the
  means to.

## Proposed

Keep the record as it is: append-only, timestamped, attributed, with a mandatory
reason, and measurable across a journal. Add a human-readable projection of it
into the contract document, maintained by the tool, so that everything already
delivered to the reviewer and to the implementer's brief carries the history
automatically. Rendering the records into the review prompt directly would also
close the gap and is simpler, but leaves every other consumer of the contract
uninformed.

## Disposition — accepted; an architecture decision follows

This is the most valuable proposal the project has received, and the least
comfortable, because the evidence for it is strongest in our own journal rather
than the reporter's. This repository carries **21 amendment records across 18 of
its 91 completed tasks**. At least one contract was amended between the second
and third review round of its own task, after a reviewer raised a blocking
finding about the wording of a criterion — and the third and fourth rounds then
judged the work against the amended text with no way to know it had changed.
That is the scenario in this proposal, performed by the project that wrote the
rule.

The reporter's framing is right on both counts. The record is not the defect:
it is the primitive that makes the defect measurable, and it stays. The defect
is that the judgement is requested from a party we deliberately keep
independent, while withholding the one fact that would let it see the document
being changed underneath the judgement.

It is accepted as a decision rather than a patch, because it touches what the
gate's independence check means. The decision will settle three things the
proposal correctly leaves open: whether the history is projected into the
contract document or rendered into the prompt, or both; what the tool does when
a hand-edited history section contradicts its records; and whether an amendment
recorded after a review exists should affect what the gate says at merge, rather
than only what the reviewer sees. The next release carries the decision and the
mechanism it names.
