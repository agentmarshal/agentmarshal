# 032 — The journal has no time axis: lead time and the CI cost of the loop are invisible

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:1949fe976c09a02900788374ce713df63af005c42085abff153582d1776aff5d` · **Disposition:** accepted

## Finding

`report` answers what a task cost in tokens and how many reviews it took —
per task it prints `reviews=` and `tokens=`, and nothing about time. It
does not answer how long a task took or where the time went. The records
carry enough to answer that roughly and nothing to answer it precisely:
every record has `created_at`, so ordering and gaps between records are
derivable; a session record has no start time and no duration — its
`created_at` is the moment the wrapper recorded the session, the *end* of
the implementer's or reviewer's run — so a run's duration is only the gap
to the previous record, which also contains whatever the coordinator did
in between. The reporter adds that a check run a wrapper waited for — the
required check on the candidate, on the merge, on the journal transaction
— leaves no timing at all, the blind spot of proposal 028, and that a
journal transaction that timed out waiting for it leaves nothing either.

An adopter who wants to know where the loop is slow therefore reconstructs
it from record timestamps and the git provider's run history, by hand —
which is what the reporter did.

Measurements, as reported — reconstructed by hand from 24 consecutive
completed tasks over ~30 calendar hours, record timestamps plus the
provider's run history:

- Median lead time open → completed: **85 min**. Split: open → first
  candidate reviewed 28 min; first → last review 34 min; last review →
  completed 15 min.
- Review rounds per task: mean **2.3**. Tasks with 3–4 rounds took
  150–180 min; tasks with one round 47–66 min — rounds are the largest
  single component, and the journal cannot say how long each round took
  because sessions have no duration.
- CI per task: **three full runs of the required check** — the candidate
  pull request, the merge, and the journal transaction that records review
  and completion — plus the deploy. Median run 5–10 min on one runner. The
  journal transaction changes only `.agentmarshal/` and still runs the
  same check as a code change: **18 such runs, median 10.4 min each, all
  green**.
- With two tasks in flight the single runner queued up to 42 min; twice
  the wrapper's 15-minute wait for the journal transaction's check expired
  although the check later passed, and completion had to be resumed by
  hand — about 20 min each time.
- **27%** of the calendar period had no task open — waiting for decisions,
  recovering from the above. The journal shows this only as a gap between
  `completed` and the next `opened`.

The token report for the same period was complete and needed no
reconstruction.

## Proposed

1. `record-session` to accept a start time or a duration — both are known
   to the wrapper that runs the worker — so a session means "this much
   wall-clock work", not "recorded at this moment".
2. `report` to print, per task and in aggregate, lead time and its phases
   — open → first review, review rounds and their durations, last review →
   completed — alongside tokens; the data is the same journal.
3. The cost of the journal transaction itself made visible. Each
   completion adds a full pass of the required check, which is a property
   of the journal-through-pull-requests workflow of proposal 019 — so the
   documentation should say that a completion costs one more run, and the
   tool should offer a way for the required check to recognise a
   journal-only change (a `gate` mode or a documented marker), so adopters
   can run a lighter check on it without weakening the gate on code.

## Disposition — accepted

**The sentence** about what a journal transaction costs in CI is accepted
— it is the kind of fact the workflow documentation should state, and the
reporter's count gives it the number. Accepted; not shipped yet.

**Session duration and lead time** are accepted, into the rework of
accounting — where the cost field of proposal 018 and the reset-time field
of proposal 024 already sit. What a session record
should say about a run — its tokens, the provider's meter, its wall-clock
time — is one question, and it should be answered once rather than one
field at a time; a start-time or duration field is also a record schema
change, the same reason proposal 024's field is in that rework. Accepted;
not shipped yet.

**The journal-only lane** needs less than was asked, because the gate
already computes it: a candidate whose changes all sit under the journal
prefix takes a deterministic lane — the transcript reads `PASS:
journal-only transaction (deterministic lane; review not required)` —
skipping the scope and review checks entirely. In a sidecar placement
the gate forces the lane off: the evidence lives in the sidecar, so a
host candidate is work whatever paths it touches. What is missing is that a
required check cannot ask for that answer without running the whole gate:
the lane exists inside the verdict, not as a signal the check can read
early and run light on. The accepted part is exposing the lane the gate
already has to the required check — into the journal-transactions work of
proposals 019 and 035, where telling a journal-only diff from a code
change is already the question on the table. Accepted; not shipped yet.

## Where

Nothing here is shipped yet. The documentation sentence is accepted, to be
written; session duration and lead time are accepted into the accounting
rework, alongside the cost field of proposal 018 and the reset-time field
of proposal 024; exposing the gate's journal-only lane to the required
check goes with the journal-transactions work of proposals 019 and 035.
