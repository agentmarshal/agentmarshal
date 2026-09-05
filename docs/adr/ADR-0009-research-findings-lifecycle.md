# ADR-0009: A research task lands through findings, not diffs

Status: Accepted
Date: 2026-09-05

This ADR records a decision. The record type, the review binding and the
gate lane it describes are **not implemented by this document**; they follow
in their own task. The present tense below is how a decision is written, not
a claim about shipped behaviour.

## Context

The records that carry evidence of work bind to a commit. A review names
`reviewed_commit`; completion names `completed_commit`; the gate diffs
`merge-base..candidate` and reads the contract from the base side. That is the right shape for the
work this project was built around: a change to a repository, proven against
the exact commit that carries it.

It is the wrong shape for a task whose output is a conclusion. An audit, an
investigation, a measurement, a re-read of prior art — these produce a
document, not a diff. Proposal 005 named the gap from an adopter's side: a
task whose entire output was four facts about an external system had nowhere
in the journal to put them, and a day later the project's own register still
showed the questions open. We then met it from the inside. The sidecar
placement (ADR-0008) gave a private research journal a home, and its first two
tasks — a measurement protocol and this project's own prior-art re-read —
**cannot complete**. There is no host commit to review; the gate, asked to
evaluate a sidecar's own commit, correctly answers that it does not exist in
the configured host. The tool is telling the truth: it has no way to say that
a conclusion was checked.

The pieces are already in the schema. Every record since schema 2 may carry
`artifacts: [{ref, hash}]` — hash-pinned references, defined in ADR-0005
Decision 4 and validated in `records.py` — and nothing writes them. Proposal
005 set the constraint that still holds: the tool records **that** findings
exist and **where** they are pinned; it does not become a store for research
content.

## Decision

### 1. A `finding` record names a task's output by content hash

A `finding` record carries a non-empty `artifacts` list — each entry a
reference and a hash of the content it points at — and a one-line
`summary`. It is written by the party that produced the output, and like
every record since schema 2 it carries `recorded_by` (ADR-0006). The hash is
the sha256 ADR-0005 Decision 4 already specifies and `records.py` already
validates. It projects to no state: a
task with findings is still open until it completes.

The artifacts are the evidence; the record pins them. A document that is
later edited no longer matches its recorded hash, and that mismatch is
detectable by anyone holding the journal — the same property a commit SHA
gives a diff.

### 2. A review may bind to a finding instead of a commit

A `review` record names **exactly one** of `reviewed_commit` or
`reviewed_finding`. The second is the identifier of a `finding` record in the
same task. A reviewer of a finding reviewed the artifacts at the hashes that
record names — not the file as it happens to be on disk when the review is
read.

The claim boundary is ADR-0006's, unchanged: the reviewer is a declared
identity, the verdict is a declared verdict, and nothing establishes that the
conclusion is true. What is established is *which content* a named party
said *what* about, at *what time*.

### 3. The gate has a findings lane, admitted by the contract

A task enters the findings lane when **its contract declares no scope** and it
carries at least one `finding` record. The gate is invoked for it without a
candidate commit. This turns the existing empty-scope rule into a meaning
rather than a warning: an empty scope no longer says "nothing may land", it
says "this task lands through findings". A task with a scope keeps the diff
lane; a task with an empty scope and no finding is, as today, a task that
cannot land yet.

The findings lane computes the checks that have something to check and says
which it did not:

- the task is not closed at base — as today;
- the **latest review binds to the latest finding**, and is approving or
  accepted over its findings (ADR-0007 applies unchanged);
- the reviewer's declared identity differs from the finding's `recorded_by`;
- every artifact whose reference resolves to a path under the journal's
  project root still hashes to what the finding recorded — **artifact drift
  refuses the lane**, the way a new commit invalidates a verdict; references
  that do not resolve locally are recorded, not verified, and the transcript
  names each;
- evidence records are append-only; added records are valid; lifecycle
  records are consistent — as today.

It does **not** diff anything, check any scope, or ask for a pipeline
attestation — there is no candidate, no changed path, and no pipeline. Each
of those lines prints as *not examined, with the reason*, in the manner the
sidecar gate already uses, so a findings-lane pass is not printed with the
diff lane's wording.

`complete` on a findings-lane task runs this lane and writes `completed` with
`completed_finding` in place of `completed_commit`.

### 4. Placement does not change the lane

The findings lane exists in both placements. In a sidecar — where research
journals will mostly live — it is the first lane that decides something the
placement can actually decide: the sidecar owns its findings and their
hashes, so this pass is not advisory in the way the diff lane's is. The
transcript still states the placement, and ADR-0008 Decision 7's boundary
still holds for everything the sidecar says about its host.

### 5. What this establishes, and what it does not

A finding plus an approving review of it establishes: a declared party
recorded that these artifacts, at these hashes, are the task's output; a
declared, independent party recorded a verdict on exactly that content; the
content has not changed since. It does not establish that the finding is
correct, that the reviewer read it, or that the artifacts are complete. Those
are the same limits every record in this journal carries, and the
documentation will state them next to this lane as it does next to the others.

## Consequences

**Schema 4, appearing only when used.** A new record type and a new review
field are format extensions. By the release rule that has held since 0.3.0,
neither appears in a journal until a task uses the lane; a journal that never
does stays readable by 0.3.0. One that does is refused by 0.3.0 with `record
has an unknown or missing schema version` — fail-closed, which is the right
failure and the opposite of what 0.2.0 did with a sidecar configuration.

**Five registration points.** A record type is known in five places —
`_RECORD_FIELDS`, `_validate_record`, `PREDICATE_TYPES`, `_RECORD_TYPE_STATES`,
and the factory with its CLI command. The predicate URI is
`https://agentmarshal.dev/attestations/finding/v1`. A review of a finding
projects (when the projection exists, ADR-0005) to a Statement whose subjects
are the finding's artifact digests — in-toto's subject model already takes a
content digest of anything, so the projection as ADR-0005 specifies it needs
no change for this.

**`brief` follows the lane.** For a task with an empty scope the briefing
stops saying "you are implementing" and "no change can land", and says that
the task lands through findings. The three vocabulary frictions the sidecar
dogfood recorded are one friction, and this is its fix.

**The first users are our own two open research tasks.** They become the
first `finding` records and the first findings-lane completions — a test on
live data, not a fixture.

**Cost attribution is separate and already handled** by declared-window
attribution in the operator's driver; nothing here touches it.

## Alternatives considered

**Bind the review to an artifact digest directly** (`reviewed_artifact`
carrying a sha256) rather than to the finding record. Rejected: a task's
output is usually several files, so the review would need the whole list or a
digest over the list — a second hashing scheme to specify and verify. Binding
to the finding record, which already holds the list, keeps one scheme, and
the "latest review of the latest finding" rule gives the invalidation
property without it.

**A separate `review-finding` record type** instead of a second binding field
on `review`. Rejected: one more type to register in five places, one more
predicate URI, and a reviewer vocabulary split in two for what is the same
act. Exactly-one-of two fields is a validation rule, not a new concept.

**Infer the lane from the command** (`complete --findings`) rather than from
the contract. Rejected: it would let a task that declared a scope — and so
promised a diff — land without one. The contract chooses the lane; the
command only supplies the evidence.

**Leave research tasks unclosable.** The status quo. Rejected by the
evidence: two tasks in our own sidecar are open with their work done, and the
practitioner journals proposal 005 and ADR-0008 both cite keep this evidence
as files with dates typed into them — the thing the journal exists to
replace.
