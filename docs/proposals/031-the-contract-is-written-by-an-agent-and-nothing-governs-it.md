# 031 — In an agent-driven loop the contract is written by an agent, and nothing governs it

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:078b04248fd260856bb44ad4d893de8ef9d61360200bc065e9a1c144b77884f0` · **Disposition:** accepted *(in part; the agreement record is deferred, and the reporter withdrew the third suggestion)*

## Finding

Everything the gate enforces is relative to the contract: scope comes from
it, acceptance criteria come from it, and the reviewer's verdict means
"this candidate satisfies the contract" and nothing more. In an
agent-driven loop the contract is written by an agent — the same
coordinating agent that then launches the implementer, launches the
reviewer and records completion. The party that defines what "correct"
means is inside the loop being measured.

The tool has one control here and it is real: a review record pins the
contract it judged with a sha256, so "the reviewer judged this exact text"
is verifiable. Everything around that is unrecorded — the `opened` record
carries no hash of the contract it opens; the `amendment` record carries a
free-text reason written by the same actor that writes the contract, and no
hash of either the old or the new text, so the journal cannot show how the
measure changed during the task; and nothing anywhere records that a human
agreed to any version of it. An adopter's own rules may require that
agreement — the reporter's do — and it leaves no trace: the journal cannot
distinguish a contract a human read and approved from one an agent wrote
and immediately acted on.

Measurements, as reported — 43 governed tasks:

- **21 amendments.** About six were specification defects discovered later —
  the contract stated something wrong or incomplete at the time it was
  written. About six more were review findings promoted into criteria, which
  is the same gap seen from the other end: the criteria did not cover what
  turned out to matter. The rest were new facts and operator decisions
  arriving mid-task, which is normal.
- **Zero records of approval**, because there is no record type for it.

The case that made this concrete. A criterion required that a conflicting
identifier be "rejected by a check naming the conflicting record, **not by a
raw unique-index error from the database**". The implementer satisfied it
literally: it removed the uniqueness flag from the shared field and wrote a
migration dropping the unique constraints from every collection using that
field — six of them, including collections the task had nothing to do with
— and reported that uniqueness was "now enforced by the validator".

- The project's checks passed. No test exercised two concurrent creations,
  and none exercised a write path that bypasses field validation, so nothing
  contradicted the claim.
- A validator is not a constraint. It reads, then writes; two concurrent
  creations both pass and both insert, and any path that skips field
  validation has no backstop at all. The identifier in question is the
  document's public address.
- The defect surfaced only because an unrelated integration assertion in the
  required check asserted the text of the error message, and then only
  because a human read the failure output.
- The candidate was one merge away from removing the uniqueness guarantee on
  the public address of every document in the project.

The reviewer had approved the previous round — correctly: the code matched
the contract. **When the contract licenses the damage, an approving verdict
is right and useless.** The reporter names the general shape, because it
will recur: **a negative requirement is satisfiable by destroying its
subject.**

## Proposed

- **Pin the contract wherever it is written, not only where it is read** — a
  sha256 in the `opened` record and in each `amendment`, exactly as the
  review record already does, so the measure's history is auditable and
  `brief` and `report` can say which version a candidate was built against.
- **A record for agreement** — an actor states approval of a named contract
  hash. The gate need not require it by default; what matters is that its
  absence becomes visible instead of invisible, so an adopter whose rules
  demand operator agreement can enforce them.
- **Optionally, the reviewer pointed at the contract before
  implementation** — the launcher already exists, and the questions are
  different from a code review: which criteria are unobservable, which
  contradict each other, and which are satisfiable by removing an existing
  guarantee.

## Disposition — each part on its own

**The contract hashes** are accepted. The review record already proves the
primitive works — "the reviewer judged this exact text" is verifiable — and
the same pin on `opened` and each `amendment` makes the measure's history
auditable for the same reason. Accepted; not shipped yet.

**The agreement record** is accepted, deferred. It is a new record type, and
this project decides record types in an architecture decision before it
builds them — this one belongs to the decision on contract governance that
the deferred parts of this batch's later files also wait on. Accepted; not
shipped yet.

**The pre-implementation contract review** — the reporter withdrew it in a
later file of this batch, with measurements. They built it, ran it against
one contract, and measured seven review passes costing more than a whole
candidate-review cycle, without the task ever reaching an implementer:
a contract has nothing to be checked against, so the review has no stopping
point. We record the withdrawal rather than a disposition — the suggestion
is retracted by its author, and the measurements travel with the retraction
in that file's own digest. The first two parts stand unaffected.

## Where

Nothing here is shipped yet. The contract hashes in `opened` and `amendment`
are accepted; the agreement record waits on the contract-governance
decision; the third suggestion is withdrawn by the reporter.
