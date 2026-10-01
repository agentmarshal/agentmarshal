# 039 — Review findings do not feed back: repeat rounds dominate, and one-new-instance-per-round spirals have no brake

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:26238693adf96972caa832831eccf810d4d29aebcfb72f65568006c4d26e052b` · **Disposition:** accepted *(in part; the executor self-check and the findings base are deferred, the plugin interface declined)*

## Finding

After about 140 tasks, the largest single cost of the reporter's loop is not
implementation and not CI but **repeat rounds**: a candidate is returned with
findings, the implementer fixes exactly the named findings, and the next
review names new ones. The tool records every verdict and every finding id,
and nothing flows back — a finding id lives only inside its review record, so
there is no view of which *classes* of findings recur across tasks (a missing
test for an acceptance criterion, a fail-open default, a non-idempotent
script, an unvalidated input format, documentation claiming more than the
code does); the implementer of the next task starts without that knowledge
and makes the same classes of mistakes; and for tasks about edge cases the
reviewer finds **one new instance of the same class per round** — the
implementer closes the instance, not the class. The only brake is a person or
the coordinating agent noticing the spiral and amending the contract by hand.

Measurements, as reported — the last 46 completed tasks of one project, over
two days, reconstructed from records and run directories because sessions
carry no duration (proposal 032):

- median lead time open → completed **3.2 h**; per task on average **2.5
  implementer rounds** and **2.4 reviews**, 1.2 of them `changes_required`;
- only **15 of 46** candidates were approved by the first review;
- an implementer round takes a median **14.5 min** (p90 31 min), a review
  **16.8 min** (p90 35 min) — one extra round costs about half an hour of
  wall-clock time plus tokens of both parties;
- **9 of 46** tasks reached the project's intervention threshold (a third
  `changes_required` or a fifth review). In 6 of them the findings of
  successive reviews were new instances of one class; after the coordinator
  amended the contract with an acceptance criterion stated as a **principle
  covering the whole class**, and told the reviewer that further instances of
  a covered class are advisory, **each closed in one more round**;
- the counter-case: a data-verification task (about 470 evidence-backed
  claims) kept producing new instances for 8 reviews even after a principle
  amendment plus a self-check script, because the reviewer sampled
  differently each time. It ended with an operator acceptance over the
  residual findings. For such tasks a review that samples is the wrong
  instrument; a mechanical check of the whole set is the right one, and the
  contract should say so up front.

## Proposed

1. **Finding classes across tasks** — a `class` tag on findings, free-form or
   from a project vocabulary, and `report --findings` showing recurring
   classes across tasks with counts and example ids; the data is already in
   review records.
2. **Feedback into the implementer** — the recurring classes, or a project
   file the coordinator curates from them, offered to the implementer as a
   pre-submission self-check, so the next candidate is checked against the
   classes that most often failed before.
3. **Principle criteria in the contract** — a contract section (the
   reporter's example is an edge-case principle) that states the class and
   how it is closed, with the review protocol asking that a new instance of
   a covered class be reported as advisory unless the principle itself is
   violated — turning the observed one-round closure after a manual
   amendment into the default.
4. **A brake the tool sees** — `status` (and the gate output) saying when a
   task has passed a threshold of `changes_required` verdicts.
5. **Whole-set checks over sampling** — a documented pattern where an
   acceptance criterion over a large set of items requires a mechanical
   check of the whole set, shipped with the candidate and verified by the
   reviewer rather than sampled.
6. **Classification as a required lifecycle step, into a shared base** —
   every blocking and advisory finding triaged (class, and a decision:
   fixed, deferred with reason, accepted, not a defect) and appended to a
   project-level findings base in the journal, append-only and hash-pinned
   to the review it came from, with `gate` and `complete` refusing while a
   task's findings are untriaged — which would also give proposal 027's
   advisory findings their lifecycle. The file names the two anchors 0.4.0
   already has: `finding` records a hash-pinned finding, per task and only
   for research, and `brief` builds the implementer briefing from the
   contract, its amendment history and the decisions and documents the
   contract names — review findings are not among its inputs.
7. **If the maintainers consider a lifecycle step outside the tool** — a
   plugin interface for lifecycle steps: declared hooks at named points with
   a documented contract, each run recorded with its command and output
   hash, on which such a step could be built instead of yet another wrapper.

## Disposition — classes, the principle and the count accepted; the self-check and the base deferred, the plugin interface declined

**Finding classes and their aggregation** are accepted, into the
finding-lifecycle work where proposal 027's dispositions and the
converging-rounds machinery of proposal 026's second finding already sit: a
finding's class, its status against the previous round, and the answer it
eventually got are one record's questions, and they should be settled once.
The reporter's premise is the measured one — the data is already in the
review records, and the journal is the place that holds it. Accepted; not
shipped yet.

**The principle criterion in the contract** is accepted as documentation: the
reporter measured the move working — six spirals, each closed within a round
once the criterion stated the class — and the contract guidance can state
the pattern without any new machinery: the class written as a principle
covering it, further instances advisory. The whole-set check over a large
set — the counter-case's lesson — is the same kind of contract guidance, a
pattern to document rather than a mechanism to build. Accepted for
documentation; not shipped yet.

**The `changes_required` count** is accepted — in both places the reporter
names, `status` and the gate output — with the same lifecycle work. `status`
already prints every review record with its `verdict=`, `findings=N` and
`advisory=N`; what is missing is the count of `changes_required` verdicts
itself — the brake the tool can see — and that count is a fact the finding
lifecycle already has to track. The same count, printed in both. Accepted;
not shipped yet.

**The executor self-check and the findings base** are deferred — by us. Both
presuppose the lifecycle machinery they would hang from: a self-check built
on recurring classes needs the classes to exist, and a project-level base of
triaged findings is the lifecycle's own storage question, so they wait for
the same decision rather than arriving before it.

**The plugin interface** for lifecycle steps — the reporter's fallback for
the case that a lifecycle step sits outside the tool — is declined, by us:
code that runs at the gate boundary becomes something the gate trusts,
which is the line ADR-0010 draws.

## Where

Nothing here is shipped yet. Finding classes and their aggregation, and the
`changes_required` count in `status` and the gate output, go with the
finding-lifecycle work of proposals 027 and 026's second finding; the
contract principles — the edge-case principle and the whole-set check — are
accepted as documentation, to be written. The executor self-check and the
findings base are deferred by us, waiting on the same decision; the plugin
interface is declined by us, for the trust boundary ADR-0010 draws.
