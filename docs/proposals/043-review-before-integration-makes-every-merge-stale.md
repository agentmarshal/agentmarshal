# 043 — Review before integration makes every merge stale: parallel tasks pay a conflict round and a second review

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:72032bf8b7aa693b6c4bd2d36a9b40e748c13e14dd20b0f706f4e8fb2caf6b92` · **Disposition:** accepted *(the merge slot and its enforcement a supplied extension; the core unchanged)*

## Finding

The recommended loop is: implement on a task branch → review the candidate —
the review binds to its exact commit — → gate → complete → merge. In this
order **review happens before integration with the base**. With several
tasks in flight, an approved candidate then waits for its turn to merge —
for its required checks, and for the completions of the tasks ahead of it —
and meanwhile the base moves. When the base change touches the same lines,
the approved candidate no longer merges:

- the provider does not start checks on an unmergeable pull request, so a
  completion that waits for checks waits forever (proposal 040);
- resolving the conflict changes the head, and the review is bound to the
  old head — the task needs a fix round **and a full new review**, of a
  change whose only new part is the conflict resolution.

Nothing in the tool serialises the window between "reviewed" and "merged" —
nor could it: the gate decides and never merges, the merge itself is the
provider's. The reporter's provider account is a free plan — no server-side
branch protection, no merge queue — with one self-hosted runner. Adopters
notice the window as churn: the same task re-reviewed two or three times in
a day for conflicts it did not cause.

Measurements, as reported:

- **One day of parallel chains (about 10 tasks in flight):** 5 conflict
  integrations on approved or nearly approved candidates (one task twice,
  another twice, a third once), each costing a fix round and a new review;
  3 completions waited ~40 minutes for a check that could not start —
  proposal 040, from the same reporter, counted one such stall among the
  six it reports; the figures differ, and this digest does not reconcile
  them. Roughly 5 extra implementer rounds and 5 extra reviews in one
  day, plus several hours of chain time.
- **Where the conflicts were:** not in feature code but in shared files
  every feature touches — a schema migration index (two tasks that change
  the schema conflict there every time), configuration examples, shared
  helpers and layouts. Declared scopes were broad — one top-level
  directory — so scope overlap predicted nothing.
- **The same project, strictly one task at a time (the following two
  days):** 1 conflict integration in 12 completed tasks (from work done
  before the switch). End-to-end time of a small task about 55–75 minutes,
  of which 30–60 minutes are the final stage (checks on the task branch,
  completion, journal transaction, deployment) on one runner. Serialising
  everything removed the conflicts, at the cost of serialising
  implementation and review too, which do not need it.
- **Hosted merge queues** — the reporter checked them as an alternative: on
  both providers it evaluated, they are available only on enterprise plans
  for private repositories. More importantly, they reject a pull request
  with a textual conflict rather than resolve it, so the fix round and the
  second review remain; they shorten the stale window, they do not remove
  it.

> Note (2026-10-03): the published
> [self-hosting workflow](../self-hosting-workflow.md) numbers the loop
> differently — merge is step 4 and complete step 5 — while allowing that
> completion may run before or after the implementation merges. The
> stale-merge observation above holds either way: the window it measures
> is between "reviewed" and "merged", on whichever side of the merge
> `complete` falls.

## Proposed

1. **The recommended order is integration → review → merge.** The final
   stage of a task takes a merge slot, integrates the candidate with the
   current base — a conflict resolved inside the same implementer round —
   reviews the *integrated* candidate with checks running in parallel,
   merges immediately, releases the slot. Under the slot the base cannot
   move between review and merge, so a conflict after approval is impossible
   by construction, and no one needs to reason about scope overlap.
   Implementation and fix rounds stay parallel; only the final stage is
   serialised.
2. **A merge slot in the tool**, not in every adopter's wrappers:
   `slot acquire / renew / release / break` with a fencing token, an expiry
   renewed by a heartbeat, a forced break only by compare-and-swap on the
   expected token — automatic after expiry or by an operator — and each
   acquisition and break recorded in the journal. On git this maps to an
   atomic ref on the remote: creating a ref fails if it exists, a ref update
   can be conditional on its old value — no service beyond the repository.
3. **`gate` (or completion) refuses to merge without the slot**, or at least
   warns, so the order is enforced where the merge happens.
4. **A short review of the resolution only, as a fallback** — when
   integration under the slot did produce a conflict: the reviewer sees the
   approved diff, the base change and the resolution, not the whole task
   again — feeding the previous round forward rather than starting over, as
   proposal 039 asks.
5. **A metric:** rounds and reviews caused by integration conflicts per day,
   target zero — proposal 032's time axis makes it computable.

## Disposition — accepted; the order as documentation, the slot and its enforcement a supplied extension

**The recommended order** — integrate, review, merge — is accepted for the
process documentation and the reference driver in the adopter kit. The
reporter's own numbers say why it is worth stating: serialising everything
removed the conflicts but serialised the parallelisable work too; the slot
serialises only the final stage. Accepted; to be written.

**The merge slot** is accepted as a supplied extension, not the core: a lock
is live state — who holds it now, until when — and
[ADR-0012](../adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md)'s rule
keeps live state out of the core, which holds no live process. That
decision's application to proposal 040 ends "there are no heartbeats and no
mutual-exclusion locks" — in the core; the slot is a supplied extension's
lock, and the core does neither. The atomic remote ref gives fencing,
expiry and the compare-and-swap break without any service beyond the
repository; acquisitions and breaks land in the process log the decision on
where local state lives defines. Accepted; not shipped yet.

**Enforcement where the merge happens** is met through
[ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
rather than by changing the gate: the slot extension runs in `pre-gate-stop`
mode — a separate step before the gate that may pause the process — and
pauses while the task does not hold the slot. The gate itself reads neither
an extension's output nor its flags, and it decides and never merges; the
core does not change. Accepted; not shipped yet.

**The resolution-only review** is accepted, with the finding-lifecycle
decision: a review mode bound to the integrated head, with the earlier
approval as context — the reviewer sees the approved diff, the base change
and the resolution. Accepted; not shipped yet.

**The metric** — implementer rounds and reviews caused by integration
conflicts per day — is accepted: `report` over the journal's time axis, with
the accounting rework. Accepted; not shipped yet.

## Where

Nothing here is shipped yet. The integrate → review → merge order is
accepted for the process documentation and the adopter kit's reference
driver; the merge slot — fencing token, heartbeat renewal, compare-and-swap
break over an atomic remote ref, its events in the process log — is accepted
as a supplied extension, enforced by its `pre-gate-stop` pause per ADR-0013
with the core unchanged; the resolution-only review goes with the
finding-lifecycle decision; the conflicts-per-day metric goes with `report`
and the accounting rework.
