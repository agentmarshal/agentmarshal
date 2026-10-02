# 042 — The liveness of an unattended loop is watched by hand: a step watchdog and a loop monitor the reporter offers to contribute

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:6bf1b733ad6a4f83bbddf67f935a47dd61008ce745d5c7aa9f4a72e3d7d48ca6` · **Disposition:** accepted *(in part; actions through the tool declined for the core and met elsewhere; the offered code accepted in principle; it arrives through the reporter's outbox under an explicit Apache-2.0 license line, decided 2026-10-03)*

## Finding

In the reporter's loop the implementers are three agent CLIs run in a
sandbox. An unattended loop fails in two ways the journal cannot see
(proposal 040): **a step that is alive but slow is killed**, and **a step —
or the whole loop — that is dead is not noticed**.

1. **A hard time limit kills live work.** The reporter's wrapper ran each
   implementer under `timeout 3600`; three times in two days the limit
   killed an implementer that was actively writing code. The files survived
   as a work-in-progress commit, but the next round started a new session,
   re-read the repository and the contract, and lost the reasoning that had
   produced them. Raising the limit to two hours only moved the cliff: one
   run finished its work within seconds of the mark and was still recorded
   as killed — proposal 041's second failure class.
2. **A dead loop looks like a quiet one.** Between steps nothing writes
   anything for 10–40 minutes — waiting for checks on a single runner,
   waiting for a deployment. A stopped queue, a step blocked on a lock, or
   a provider outage looks exactly like that normal quiet. Before the
   reporter built a monitor, the operator found a stopped queue only by
   asking — about half a working day was lost that way in one day.

The reporter built both halves outside the tool, and both are generic:

- **Step level — a liveness watchdog inside the implementer wrapper**
  (standard library only, ~830 lines with session handling): runs the
  implementer in the background and samples three kinds of signals every few
  seconds — a fingerprint of the task worktree; growth of the implementer's
  own output, filtered to *this* run, because CLI home directories are
  shared on the machine and a parallel run must not keep another one alive;
  CPU time of the process tree. It stops the tree softly — TERM, then KILL
  after a grace period — only when *no signal* has been seen for an idle
  window (default 20 min), recording the reason `stalled`; a long safety
  limit (default 6 h) remains. Every 5 minutes it writes a heartbeat line to
  a progress log in the run directory — elapsed time, files and lines
  changed, which signal was last seen and how long ago — readable by a
  person or another agent without touching the implementer. On any stop it
  saves the session id and everything the CLI produced next to the run, so
  the next round can resume the same session; if the CLI refuses to resume,
  it falls back to a new round and says so. It fails closed: if the watchdog
  itself dies, the implementer tree is stopped rather than left without any
  limit.
- **Loop level — a monitor outside the loop** (a small polling script the
  coordinating agent keeps armed): tails the loop's log and emits only lines
  that need action — verdicts, refusals, stops, completions, conflicts;
  every few minutes checks that the driver process is alive, and that
  *something* in a set of activity paths changed in the last 25 minutes,
  emitting "silence" otherwise — the signal for a hang that writes nothing;
  checks the deployed version on the target and emits when it changes;
  bounds every external call by its own timeout, so one slow network call
  cannot freeze the monitor.

Measurements, as reported:

- **Before the watchdog** (hard limit of 60, then 120 minutes): 3 kills of
  an implementer that was actively working, across 2 tasks; each was
  followed by a fresh session that re-read the task. One task needed 6
  rounds, 2 of them ended by the time limit.
- **After the watchdog** (one day, 11 implementer runs on 6 tasks, two
  different CLIs): **0 stops of a live implementer**; longest run 41 min,
  median 8 min (runs ended by a provider usage limit included); 28 heartbeat
  lines written; 8 follow-up rounds decided between resume and new round —
  4 resumed the same session, 4 fell back to a new round (the CLI refused,
  or the implementer changed), each recorded with its reason.
- **Loop monitor:** after it was armed, every stop of the queue (5 in two
  days: a provider usage limit, scope refusals, a gate refusal, time limits)
  reached the coordinator as an event within one polling interval; no stop
  was found by a person asking. Building it cost three false starts worth
  listing for anyone writing one: a process-name probe that matched its own
  command line, a remote call without a timeout that froze the loop, and a
  `find` variant that did not support the time predicate used.

## Proposed

The plugin system upstream is preparing is the right home for both halves.
For a liveness plugin to be portable rather than a fork of the reporter's
wrappers, the interface needs:

1. **Lifecycle events with identity** — step started / heartbeat / finished,
   with task, step kind, actor, run directory and the process (or a handle):
   the leases of proposal 040, published to extensions. The loop monitor
   subscribes to these instead of parsing a log.
2. **A way to contribute activity signals** — an extension (or an
   implementer adapter) declares how to tell that *its* run is alive — paths
   owned by this run, a session id, a process tree — so the watchdog is
   generic and only the probes are per-CLI.
3. **A stop outcome with a reason and a resume handle** — `stalled` or
   `safety-limit` recorded together with the session id and saved artifacts,
   so the next-step decision of proposal 041 can choose `resume` over a new
   round. The reporter notes this extends proposals 024 and 034.
4. **A progress record readable by others** — the heartbeat goes to a known
   place per run (and optionally to `status`), so a person or another agent
   can answer "is it working?" without attaching to the process.
5. **Actions as hooks, not kills from outside** — pause a task until a time,
   resume the same session, stop softly — so an operator or a monitor acts
   through the tool and the journal stays the record.

And the offer: the reporter can contribute both components as a reference
plugin — the watchdog, standard library only and tested with mocks for the
three agent CLIs it runs (an active long run not stopped, an idle run
stopped as stalled, heartbeat lines, the session saved, resume chosen and
its fallback), and the loop monitor.

## Disposition — the stage and the outcomes accepted; actions declined for the core; the offered code accepted in principle as a supplied extension

**Step lifecycle events** are accepted: they are a `step` stage under
[ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)'s
rule for future stages — new stages are added at an adopter's request, and
this request arrives with its measurements, so the condition is met and
the stage is accepted, to be added to the decision. The ADR itself starts
with `pre-gate` and `post-gate` and lists two candidates, each with its
own condition; `step` is not among them. Under
[ADR-0012](../adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md)'s
boundary the core holds no live state: the process handle the request asks
for is data the harness declares when a step starts, and the core only
passes the event — handle included — on to the `step`-stage extension.
The events land in the process log the decision on where local state lives
defines. Accepted; not shipped yet.

**The activity-probe extension point** is accepted in the manifest's form:
an extension at the `step` stage declares its probes — the paths this run
owns, the session id, the process tree — and the core knows no CLI.
Accepted; not shipped yet.

**The `stalled` / `safety-limit` stop outcomes with a resume handle** are
accepted: outcome vocabulary is the accounting rework's ground — beside
`provider-limit`, documented since 0.4.1, and the values proposal 041 adds —
and the session record will carry the session id, decided with the records
of a later decision; `next` reads it to choose `resume` over a new round.
Accepted; not shipped yet.

**The per-run progress record** is accepted: the heartbeat is written by
the watchdog extension into the process log the decision on where local
state lives defines — the known place a person or another agent can read
without attaching to the process.
[ADR-0012](../adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md)'s
application of its rule to proposal 040 ends "there are no heartbeats and
no mutual-exclusion locks"; that line speaks for the core, and it stands —
the core does neither: the heartbeat is the watchdog extension's, and the
merge slot of proposal 043 is a supplied extension's lock. Accepted; not
shipped yet.

**Actions through the tool** — pause a task until a time, resume a session,
stop softly — are declined for the core, by us:
[ADR-0012](../adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md)'s
boundary holds: the core does not execute and holds no live state. The needs
underneath are still met — pausing a task until a time is the plan file of
proposal 041, and stopping or resuming a run is what the watchdog extension
itself does.

**The offered code** — the watchdog and the loop monitor as a reference
plugin — is accepted with thanks, in principle, as a supplied extension
under ADR-0012: the project recommends it, a compatibility test in the
project's CI checks it against a full task cycle, and the pin is re-reviewed
with each release. The route by which the code reaches the project is
decided 2026-10-03, with
[ADR-0012](../adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md)'s
amendment: it arrives through the reporter's own findings outbox carrying
an explicit Apache-2.0 license line — a new use of that channel the ADR
names — and is adapted into a supplied extension by an ordinary task that
names its source.

## Where

Nothing here is shipped yet. The `step` stage with its lifecycle events, the
manifest-declared activity probes, the `stalled` / `safety-limit` outcomes
with a session handle and the per-run progress record are accepted — the
outcomes with the accounting rework, the session-id field with the records
of a later decision, the events and the progress in the process log.
Actions through the tool are declined for the core by us — a pause is
proposal 041's plan file, a stop or a resume is the watchdog's own. The
offered watchdog and monitor are accepted in principle as a supplied
extension; the code arrives through the reporter's outbox under an
explicit Apache-2.0 license line and is adapted by a project task naming
its source (decided 2026-10-03).
