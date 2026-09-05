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
`merge-base..candidate` and reads the contract from the base side. That is the
right shape for the work this project was built around: a change to a
repository, proven against the exact commit that carries it.

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
`artifacts: [{ref, hash}]` — the "supplementary artifact: reference + hash" row
of ADR-0005 Decision 5's compatibility matrix, validated in `records.py` as a
reference plus 64 lowercase hex characters. Its only writer today is the import
path in `backfill.py`, which no CLI command reaches; nothing a user runs writes
one. Proposal 005 set the constraint that still holds: the tool records
**that** findings exist and **where** they are pinned; it does not become a
store for research content.

## Decision

### 1. A `finding` record names a task's output by content hash

A `finding` record carries a non-empty `artifacts` list — each entry a
reference and a hash of the content it points at — and a one-line
`summary`. It is written by the party that produced the output, and like
every record since schema 2 it carries the provenance fields `source`,
`recorded_by` and `recorded_by_source` (ADR-0005 D4, ADR-0006) — a finding
recorded live and one imported later must stay distinguishable. **The hash is
sha256 over the artifact's bytes, lowercase hex.** No accepted document named
the algorithm before — `records.py` admits any 64 hex characters, and
`backfill.py` happens to write sha256 — so this ADR, which pins content by
hash, is the one that decides it. It projects to no state: a
task with findings is still open until it completes.

The artifacts are the evidence; the record pins them. A document that is
later edited no longer matches its recorded hash, and that mismatch is
detectable by anyone holding the journal — the same property a commit SHA
gives a diff.

### 2. A review — and an acceptance — may bind to a finding instead of a commit

A `review` record names **exactly one** of `reviewed_commit` or
`reviewed_finding`. The second is the identifier of a `finding` record in the
same task. A reviewer of a finding reviewed the artifacts at the hashes that
record names — not the file as it happens to be on disk when the review is
read.

An `acceptance` record likewise names exactly one of `accepted_commit` or
`accepted_finding`. ADR-0007 binds acceptance to "the exact commit" and
`records.py` requires `accepted_commit`; a findings-lane task has no commit,
so ADR-0007 cannot apply *unchanged*. Its rules carry over intact — the latest
review of that exact finding must be non-approving, the acceptance names every
blocking finding, and it never reads as an approval — with the binding field
substituted. This is the same extension ADR-0007 itself made to the gate: a
new binding, the same discipline.

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
  accepted over its findings through `accepted_finding` (Decision 2);
- the reviewer is independent of the finding's recorder — **compared on git
  identities.** Both sides can be brought to that representation, and the
  resolution runs from the recorder toward emails rather than from the reviewer
  toward an actor id, because an email absent from the actors table still names
  an identity while an actor id absent from it names nothing. A review carries
  an email; a finding's `recorded_by` is, per ADR-0006, one of three things,
  and `recorded_by_source` says which: a git email (compared directly), an
  actor id from the project's `actors` table (compared against that actor's
  `git_identities`), or an `AGENTMARSHAL_ACTOR` override (compared against the
  override string and, when an actor of that id exists in the table, its
  identities too). A recorder that resolves to no git identity — an override
  with no table entry, or a finding with no `recorded_by` — leaves independence
  **unestablished, and the lane refuses**, naming that as the reason. Failing
  closed here is the same choice the diff lane makes when git cannot answer a
  question about the candidate — the run ends in a refusal, not a pass;
- every artifact whose reference resolves to a path under the journal's project
  root still hashes to what the finding recorded — **artifact drift refuses the
  lane**, the way a new commit invalidates a verdict; references that do not
  resolve locally are recorded, not verified, and the transcript names each;
- evidence records are append-only; added records are valid; lifecycle records
  are consistent — as today.

It does **not** diff anything, check any scope, or ask for a pipeline
attestation — there is no candidate, no changed path, and no pipeline. Each
of those lines prints as *not examined, with the reason*, in the manner the
sidecar gate already uses, so a findings-lane pass is not printed with the
diff lane's wording.

**The findings lane decides evidence, not a merge — and the lane is chosen by
what is offered, bounded by the contract.** Invoked **without** a candidate,
the gate enters the findings lane, and only for a task whose scope is empty and
that carries a finding. Invoked **with** a candidate, the gate runs exactly the
lanes it runs today, on any task: a candidate whose changed paths all lie under
`.agentmarshal/journal/` takes the journal-only lane; any other candidate takes
the diff lane, where an empty scope refuses every path. Nothing about a
candidate's treatment changes for an empty-scope task — it is refused today and
stays refused — and nothing new is checked. What merges after a findings-lane
completion is the commit adding the `finding`, `review` and `completed`
records, and it is gated as a candidate through the journal-only lane like any
other journal transaction. A branch carrying host changes under an empty-scope
task is therefore refused where it is refused today, on the diff lane; the
findings lane, having no candidate, cannot be the way past it. In a sidecar the
records commit is not gated by this tool at all; its integrity rests on the
sidecar's own history, exactly as ADR-0008 Decision 7 already states.

`complete` on a findings-lane task runs this lane and writes `completed` with
`completed_finding` in place of `completed_commit`.

### 4. Placement does not change the lane — a bounded exception to ADR-0008 D5

The findings lane exists in both placements. ADR-0008 Decision 5 makes a
sidecar's gate advisory because **the merge belongs to the host's process**,
which the sidecar's operator does not control. The findings lane has no merge
and changes nothing in the host: there is nothing for the host's process to
decide. So for this lane, and only this lane, a sidecar's pass is the
sidecar's own decision over its own records — the journal owns its findings and
their hashes. This is an exception to ADR-0008 Decision 5 **scoped to the
findings lane**, stated here rather than left to inference; the diff lane in a
sidecar stays advisory exactly as ADR-0008 decided. The transcript still
states the placement, and ADR-0008 Decision 7's boundary still holds for
everything the sidecar says about its host.

### 5. What this establishes, and what it does not

A finding plus an approving review of it establishes: a declared party
recorded that these artifacts, at these hashes, are the task's output; a
declared, independent party recorded a verdict on exactly that content; and,
**for each artifact the gate could resolve and re-hash**, the content has not
changed since. For an artifact it could not resolve it establishes only that a
hash was recorded — the transcript names which artifacts fall on which side,
so a pass over unverified references is not printed as a pass over verified
ones. It does not establish that the finding is
correct, that the reviewer read it, or that the artifacts are complete. Those
are the same limits every record in this journal carries, and the
documentation will state them next to this lane as it does next to the others.

## Consequences

**Schema 4, appearing only when used — which requires a rule about stamping.**
One new record type and three new binding fields — `reviewed_finding`,
`accepted_finding`, `completed_finding`, each exactly-one-of with its commit
counterpart — are the format extensions. The release
rule that has held since 0.3.0 says neither appears in a journal until a task
uses the lane, and that promise holds only if **each record is stamped with the
lowest schema its content needs**: a record carrying neither the new type nor
any of the new fields is written at schema 3; a `finding`, or a review,
acceptance or completion bound to one, at schema 4. Then a journal that never
uses the lane is byte-identical in what 0.4.0 writes to what 0.3.0 wrote, and
stays readable by 0.3.0. The precedent
runs the other way — CR-069 stamped every record 3, and that is the source of
the one-directional 0.1.0→0.2.0 break UPGRADING documents. This ADR decides
against repeating it. A journal that does use the lane is refused by 0.3.0
with `record has an unknown or missing schema version` — fail-closed, which is
the right failure and the opposite of what 0.2.0 did with a sidecar
configuration.

**Five registration points, and three field validators.** A record type is
known in five places — `_RECORD_FIELDS`, `_validate_record`, `PREDICATE_TYPES`,
`_RECORD_TYPE_STATES`, and the factory with its CLI command. Each of the three
records that gains a finding binding also needs its exactly-one-of rule in
`_validate_record`, and `acceptance.py` needs to resolve the latest review by
finding as it does by commit. The predicate URI is
`https://agentmarshal.dev/attestations/finding/v1`. A review of a finding
projects (when the projection exists, ADR-0005) to a Statement whose subjects
are the finding's artifact digests — in-toto's subject model already takes a
content digest of anything, so the projection as ADR-0005 specifies it needs
no change for this.

**ADR-0008 gains a pointer.** Decision 4 carves a bounded exception into
ADR-0008 Decision 5. That document must not keep reading as an unqualified
rule, so the implementation task adds a one-line reference from ADR-0008 D5 to
this ADR; the decision itself is made here.

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
