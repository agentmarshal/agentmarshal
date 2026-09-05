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
`summary`. It is written by the party that produced the output. It carries
`source` like every record since schema 2 (ADR-0005 D4), so a finding recorded
live and one imported later stay distinguishable; and, unlike other records,
where they are optional, `recorded_by` and `recorded_by_source` (ADR-0006) are
**required** on a finding — the independence check in Decision 3 has nothing to
compare without them, and a finding that cannot name its recorder is refused
at write time rather than at gate time. **The hash is
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
carries at least one `finding` record. The gate is invoked for it with
`--findings`, offering no candidate (the flag, and why it is a flag, are below).
This turns the existing empty-scope rule into a meaning
rather than a warning: an empty scope no longer says "nothing may land", it
says "this task lands through findings". A task with a scope keeps the diff
lane; a task with an empty scope and no finding is, as today, a task that
cannot land yet.

The findings lane computes the checks that have something to check and says
which it did not:

- the task is not closed — read from its projected state in the journal, as the
  sidecar gate already reads it (`task.state`), since there is no base tree to
  read it from;
- the **latest review binds to the latest finding** and is approving — or, when
  it is not, an `acceptance` record bound to that same latest finding through
  `accepted_finding` exists and satisfies ADR-0007's rules (Decision 2).
  Acceptance is a separate record; a review is never "accepted", it is
  overridden by one;
- the reviewer is independent of the finding's recorder — **compared on git
  identities.** Both sides can be brought to that representation, and the
  resolution runs from the recorder toward emails rather than from the reviewer
  toward an actor id, because an email absent from the actors table still names
  an identity while an actor id absent from it names nothing. A review carries
  an email; a finding's `recorded_by` is, per ADR-0006, one of three things,
  and `recorded_by_source` says which: a git email (compared directly), an
  actor id from the project's `actors` table (compared against that actor's
  `git_identities`), or an `AGENTMARSHAL_ACTOR` override (compared against the
  `git_identities` of the actor of that id in the table, when one exists; the
  override string itself is a label, not an identity, and is never compared). A
  recorder that resolves to no git identity — an override with no table entry,
  or a finding that somehow carries no `recorded_by` (this tool refuses to
  write one, per Decision 1; the gate still checks, for records another tool
  wrote) — leaves independence **unestablished, and the lane refuses**, naming
  that as the reason. Failing closed here is the same choice the diff lane
  makes when git cannot answer a question about the candidate — the run ends in
  a refusal, not a pass;
- every artifact whose reference resolves to a path under the journal's project
  root still hashes to what the finding recorded — **artifact drift refuses the
  lane**, the way a new commit invalidates a verdict; references that do not
  resolve locally are recorded, not verified, and the transcript names each;
- evidence records are append-only; added records are valid; lifecycle records
  are consistent. Today these read the candidate's diff; with no candidate they
  read the journal itself — its working tree and its own commit history, the
  way the sidecar gate already does through `_sidecar_tampered_records` — in
  both placements.

It does **not** diff the candidate against a scope — there is no candidate and
no changed path — ask for a pipeline attestation, since there is no pipeline,
check record-path collisions against a base tree, since no candidate adds
records to one, or run the advisory leak scan, which reads
`merge-base..candidate` and has no range to read. Those four, with six of the
seven computed above — artifact drift is new to this lane and has no diff-lane
counterpart — account for every check the diff lane runs today. Each of the
four prints as *not examined, with the reason*, in the manner the sidecar gate
already uses — so a findings-lane pass is not printed with the diff lane's
wording, and no check is left to print a diff-lane `PASS` over something nobody
looked at.

**The findings lane decides evidence, not a merge — and the lane is chosen by
what is offered, bounded by the contract.** The gate enters the findings lane
when told so explicitly — `gate --task X --findings` — and only for a task
whose scope is empty and that carries a finding. The flag is required rather
than inferred from a missing `--commit`, because today the absence of
`--commit` already means something: the candidate defaults to the current HEAD,
`--task` to the branch name, `--base` to the default branch, and those defaults
stay exactly as they are. Given a candidate, the gate runs the lanes it runs
today, on any task: a candidate whose changed paths all lie under
`.agentmarshal/journal/` takes the journal-only lane; any other candidate takes
the diff lane, where an empty scope refuses every path. Nothing about a
candidate's treatment changes for an empty-scope task — it is refused today and
stays refused — and nothing new is checked. What merges after a findings-lane
completion is the commit adding the `finding`, `review` and `completed`
records, and it is gated as a candidate through the journal-only lane like any
other journal transaction. A branch carrying host changes under an empty-scope
task is therefore refused where it is refused today, on the diff lane; the
findings lane, which examines no candidate, cannot be the way past it. In a
sidecar the records commit is not gated by this tool at all; its integrity
rests on the sidecar's own history, exactly as ADR-0008 Decision 7 already
states.

**The journal-only lane trusts the writer of a completion record, in both lanes
alike.** Merging a commit that adds `completed_finding` re-runs neither the
findings lane nor its review check — exactly as merging a commit that adds
`completed_commit` today re-runs neither the diff lane nor its review check.
The journal-only lane verifies shape, append-only integrity and lifecycle
consistency; it does not verify that a gate pass preceded a completion
record, for either binding. This ADR holds that boundary at parity and adds no
guard for one record type that the other lacks. Whether completion records
should be re-verified at merge is a question for both lanes together, and it is
not decided here.

`complete --task X --findings` runs this lane and, on a pass, writes
`completed` with `completed_finding` in place of `completed_commit`. Like the
gate, it takes the flag rather than a candidate; `complete` with `--commit` and
`--base` keeps today's meaning on any task.

### 4. Placement does not change the lane — an exception to ADR-0008 D5 and D6

The findings lane exists in both placements. ADR-0008 Decision 5 makes a
sidecar's gate advisory because **the merge belongs to the host's process**,
which the sidecar's operator does not control. The findings lane has no merge
and changes nothing in the host: there is nothing for the host's process to
decide. So for this lane, and only this lane, a sidecar's pass is the
sidecar's own decision over its own records — the journal owns its findings and
their hashes. This is an exception to ADR-0008 Decision 5 **scoped to the
findings lane**, stated here rather than left to inference; the diff lane in a
sidecar stays advisory exactly as ADR-0008 decided. The same exception reaches
ADR-0008 Decision 6, which says a completion recorded in a sidecar states that
its checks passed advisorily: a findings-lane completion states instead that
they passed on the sidecar's own evidence, and its transcript says which lane
produced it. ADR-0008 Decision 7's boundary still holds for everything the
sidecar says about its host.

### 5. What this establishes, and what it does not

A finding plus an approving review of it establishes: a declared party
recorded that these artifacts, at these hashes, are the task's output; a party
whose **declared** identity differs from the recorder's recorded a verdict on
exactly that content — a difference of declarations, which is all the
independence check ever establishes (ADR-0006); and,
**for each artifact the gate could resolve and re-hash**, the bytes at gate
time are the bytes the finding recorded — a statement about the present
content, not about what happened to the file in between. For an artifact it
could not resolve it establishes only that a
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
counterpart — are the format extensions. The release rule that has held since
0.3.0 says neither appears in a journal until a task uses the lane, and that
promise holds only if **each record is stamped with the schema its content
requires, with 3 as the floor**: a record carrying neither the new type nor any
of the new fields is written at schema 3 exactly as today; a `finding`, or a
review, acceptance or completion bound to one, at schema 4. No record is ever
stamped below 3 — CR-069's floor stands. Then a journal that never uses the
lane is byte-identical in what 0.4.0 writes to what 0.3.0 wrote, and stays
readable by 0.3.0. The precedent runs the other way, and for a reason that does
not apply here: the 0.1.0→0.2.0 break came from the schema-2 provenance fields
themselves — 0.1.0 refused `recorded_by` as an unsupported field — and CR-069
stamped every record 3 so that refusal read as a schema mismatch instead. Every
record carried the new fields then; most records will not carry the new fields
now, so the floor stays where it is. A journal that does use the lane is
refused by 0.3.0 with `record has an unknown or missing schema version` —
fail-closed, which is the right failure and the opposite of what 0.2.0 did with
a sidecar configuration.

**Five registration points, and three field validators.** A record type is
known in five places — `_RECORD_FIELDS`, `_validate_record`, `PREDICATE_TYPES`,
`_RECORD_TYPE_STATES`, and the factory with its CLI command. Each of the three
records that gains a finding binding also needs its exactly-one-of rule in
`_validate_record`, and `acceptance.py` needs to resolve the latest review by
finding as it does by commit. The predicate URI is
`https://agentmarshal.dev/attestations/finding/v1`. A review of a finding
projects (when the projection exists, ADR-0005) to a Statement whose subjects
are the finding's artifact digests — in-toto's subject model already takes a
content digest of anything. The projection as ADR-0005 Decision 5 specifies it
does change by one row: its matrix maps `subject[].digest` only from
`reviewed_commit` and `completed_commit`, and a finding-bound record supplies
its subjects from the finding's `artifacts` instead. That row is wave S's to
add; this ADR names it so the work is counted.

**Other documents this reaches.** ADR-0004 describes schema 3 as "the schema-2
provenance rules plus creator attribution"; after schema 4 exists that sentence
must not read as a complete history, so the implementation task extends it.
UPGRADING gains a 0.3.0 → 0.4.0 section at release, stating the floor-3 rule
and what a 0.3.0 reader does with a schema-4 record.

**ADR-0008 gains pointers.** Decision 4 carves a bounded exception into
ADR-0008 Decisions 5 and 6. That document must not keep reading as an
unqualified rule, so the implementation task adds a one-line reference from
each of D5 and D6 to this ADR; the decision itself is made here.

**`brief` follows the lane.** For a task with an empty scope the briefing
stops saying "you are implementing" and "no change can land", and says that
the task lands through findings. The three vocabulary frictions the sidecar
dogfood recorded are one friction, and this is its fix.

**The first users are our own two open research tasks — once a prerequisite is
met.** They become the first `finding` records and the first findings-lane
completions, a test on live data rather than a fixture. But every record in
that sidecar carries `recorded_by` as an `AGENTMARSHAL_ACTOR` override, and
neither of this project's `project.json` files declared an `actors` table when
this was written; by Decision 3 the lane refuses an unmapped override. The
operator's first step is therefore to map the recording agent to a git identity
in the sidecar's `actors` table. Without it the lane is correct and unusable,
which is the intended order.

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

**Let the command choose the lane on its own** (`complete --findings` admitting
any task). Rejected: it would let a task that declared a scope — and so
promised a diff — land without one. The flag survives in a narrower role: it
names which evidence is being offered, because for `gate` the absence of
`--commit` already means "the current HEAD" and cannot double as "no
candidate" (`complete` requires `--commit` today and simply gains the
alternative). Whether
that evidence is admitted is still the contract's decision, never the flag's.

**Leave research tasks unclosable.** The status quo. Rejected by the
evidence: two tasks in our own sidecar are open with their work done, and the
practitioner journals proposal 005 and ADR-0008 both cite keep this evidence
as files with dates typed into them — the thing the journal exists to
replace.
