# ADR-0007: The operator accepts work over findings

Status: Accepted
Date: 2026-08-31

## Context

The gate merges an implementation candidate only when the latest review of that
exact commit is `approved`. There is no other path. The practical consequence is
that **the acceptance decision belongs to the reviewer**, while the operator is
accountable for the product and the reviewer is a tool the operator chose.

While findings are real this is the behaviour we want, and it works. The problem
is non-convergence. Adopter proposal 007 reports it with measurements: one task
at **thirteen review runs and still not closed**, another at six, three more
abandoned and reopened purely to escape the loop. The escape was expensive and
dishonest — the journal then records an abandonment, which says the *work* was
wrong when what failed was the loop.

We have the same measurement on ourselves, independently: five verdicts on one
identical commit in this repository, one pass and four refusals carrying
different findings each time. In one session a single reviewer channel produced
a factually false finding, missed three real defects, and caught a real one that
the lead agent had not. Thirteen runs on one task is not a strict reviewer; it
is a control loop that does not terminate.

An unterminating loop has exactly two exits today: abandon the task, or keep
paying until a run happens to approve. The second is worse than it looks — under
a non-deterministic reviewer, *waiting for approval is sampling until you get
the answer you want*, which is verdict-shopping with extra steps and no record
that it happened.

So the question is not whether to add an escape. One exists; it is untracked.
The question is whether the exit is **recorded**.

## Decision

### 1. An acceptance is a record, not a mode

The operator accepts a specific commit over specific findings by appending an
`acceptance` record. It names the accepting party, the exact commit, the finding
ids being accepted over, and the reason in prose.

There is no flag, no environment variable, and no configuration that makes the
gate lenient. A gate run is either satisfied by an approving review or by an
acceptance record, and in the second case it says so in those words. An
operator who wants this must leave evidence that they wanted it.

### 2. An acceptance requires a real review to have happened

An acceptance is only valid when a **non-approving review of the same commit
already exists**, and it may only name finding ids that such a review raised.

This is the decision that keeps the feature from being a hole. "Accepting over
findings" presupposes findings; without this rule the same machinery would merge
work no reviewer ever looked at, which is a different act entirely and one we
are not building a path for. Review is not optional; agreeing with the reviewer
is.

### 3. It overrides one check, and the enumeration is closed

An acceptance substitutes for **the approving-verdict check and nothing else**.
Every other gate check applies unchanged:

- the diff must be within the contract's scope, read from the base side;
- the recorded reviewer's identity must still differ from the candidate's
  declared writers;
- the pipeline must still be attested for the exact commit;
- records must still be append-only, valid, collision-free, and the task's
  lifecycle consistent;
- the task must still not be closed at base.

An acceptance is not a master key. It says "I have read this objection and I am
taking responsibility for shipping anyway", which is a statement about *one*
judgement, not about whether the change is in scope or whether the tests ran.

### 4. Self-acceptance is permitted, and always visible

Someone may accept work they authored.

The alternative was to require the accepting party to differ from the commit
authors, mirroring the reviewer-independence check. We reject it for two
reasons. It would make the feature unusable in the configuration that actually
needs it — a single operator, which is every adopter this project has, and where
the author of record is frequently an agent working under that operator's git
identity. And it would be a control in appearance only: identity here is
declared, not authenticated (ADR-0006), so a rule requiring a different name
would be satisfied by typing a different name.

Instead the case is made **visible rather than impossible**. Where the accepting
party's identity matches a declared writer of the candidate, every surface that
reports the task says so — self-accepted, in those terms. We do not prevent it;
we refuse to let it look like something else.

### 5. Accepted is never displayed as approved

An accepted-over-findings task must be distinguishable from a reviewed-and-
approved one everywhere either is read:

- the **gate** reports the acceptance in place of the approval line, naming who
  accepted and over which findings — never `PASS: latest review is approved`;
- **`status`** shows the acceptance in the record trail and states it in the
  task's summary, so a reader who does not read every record still sees it;
- **`report`** distinguishes tasks that closed over findings from tasks that
  closed on an approval;
- the **attestation projection** gives the record its own predicateType, so a
  consumer of projected evidence cannot mistake one for the other.

A merge that happened over an objection is a fact about the work. Hiding it
would defeat the reason for recording it, and a system that let an operator
quietly convert "refused" into "shipped" would be worse than the dead end it
replaces.

### 6. What the record establishes, and what it does not

Following ADR-0006, the boundary is stated rather than implied.

An acceptance record establishes that **someone claiming to be the named party
recorded a decision to ship this commit over these findings, with this reason,
at this time.** It is durable, append-only, and bound to the exact SHA.

It does **not** establish that the named party is who they say they are — the
identity is declared, exactly as `vendor`, `email` and `recorded_by` are. It
does not establish that they read the findings, that the findings were wrong, or
that the work is correct. It does not transfer any legal or organisational
accountability; it records a claim about who took a decision, and organisations
decide what that means.

This boundary is about identity and judgement only. It does not narrow anything
else: scope enforcement, base-side reads, pipeline attestation, append-only
integrity and collision detection are unaffected by this ADR.

## Consequences

**The dead end becomes a fork with a record.** Where an adopter had thirteen
runs and no close, they now have a decision they must sign their name to. That
is not free — it is meant not to be.

**Abandonment regains its meaning.** Tasks abandoned to escape a review loop
have been polluting the one signal that should mean "this work was wrong".

**A new failure mode appears, and we should expect it.** Acceptance is cheaper
than fixing, so it will sometimes be used where fixing was right. Nothing in the
tool can tell those apart, and we do not claim to. What the journal gives is the
count and the reasons, which is what makes the pattern visible to whoever cares
to look — including the operator who wrote them.

**This is a new record type**, so a journal containing one cannot be read by
versions that predate it. It appears only when the feature is used, so a project
that never accepts over findings never acquires the incompatibility.

## Alternatives considered

**Leave it out.** The exit already exists — abandon and reopen, or resample the
reviewer — so leaving it out does not prevent the act, only the evidence of it.
That is the worst of both.

**A quorum of reviewer runs instead.** Requiring N agreeing verdicts would
reduce non-convergence rather than adjudicate it. It is worth doing on its own
merits and does not answer this question: a loop that does not terminate at one
run may not terminate at three, and someone must still own the decision. The two
are complementary, and the quorum's cost in tokens needs measuring first.

**Let the operator edit the review record.** Refused outright. Records are
append-only because a verdict that can be rewritten is not evidence.

**A configuration flag that relaxes the gate.** Refused: it would make every
merge in that project silently unreviewed-capable, and leave nothing in the
journal saying which merges used it.
