# ADR-0014: Where things live — the journal, the process log, CI output

Status: Accepted
Date: 2026-10-03
Amended 2026-10-03 (what the gate reads and from where; the rotation
decision's pointer to the record-model formats; decisions 3, 7 and 8 in
full sentences)

Builds on [ADR-0004](ADR-0004-journal-data-model.md) (documents for
contracts, append-only records for evidence),
[ADR-0005](ADR-0005-evidence-capture-and-format.md) (the capture policy
whose `hash` level names a durable private store),
[ADR-0008](ADR-0008-journal-placements.md) (the host is never written;
references to private content are an explicit opt-in) and
[ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md)
(extensions write to the process log; local state lives outside the working
tree).

This ADR records a decision. The process log, the map of places and the
path printing it describes are **not implemented by this document**; they
follow in their own tasks. The present tense below is how a decision is
written, not a claim about shipped behaviour.

## Context

[ADR-0005](ADR-0005-evidence-capture-and-format.md) introduced the `hash`
capture level for review prose. At that level today the journal holds
**nothing** about the prose, and the prose itself sits in the system's
temporary directory, bound to no task and easily lost. The durable private
store [ADR-0004](ADR-0004-journal-data-model.md) and
[ADR-0005](ADR-0005-evidence-capture-and-format.md) designed — persistent,
possibly synced to a private remote — is not built. Everything that is not
evidence is today either lost or inflates the journal and takes a
transaction through CI. In-flight steps
([proposal 040](../proposals/040-in-flight-steps-are-invisible-and-journal-writes-contend-on-one-checkout.md))
and extension events
([ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md)) do not
fit there.

## Decision

### 1. Three places

| Place | Holds | Seen by | Feeds the gate's decision |
|---|---|---|---|
| the journal (versioned) | evidence | everyone, forever | yes |
| the process log (local, not versioned) | in-flight steps; review prose at `hash`; reviewer diagnostics (at any level); raw accounting; post-gate results on the workstation; output and events of shared and personal extensions; local grant changes | one machine | never |
| CI output | a run of the checks | the provider, temporarily | — |

### 2. The process log is a local working log, not the durable private store of ADR-0004/0005

That store stays designed and unbuilt. At `hash` the prose goes to the
process log instead of the temporary directory — with no promise of
durability. **The journal at `hash` still holds nothing** (as today);
[ADR-0008](ADR-0008-journal-placements.md) — references to private content
only by explicit choice, no machinery writing one by default — is
unchanged.

### 3. The gate never reads the log

Or anything local at all.

Amended 2026-10-03, in a full sentence and precisely: the gate reads
neither the process log nor any of the local state this ADR places outside
the journal. What it does read, and from where, depends on the placement:
in the embedded placement the contract, the extension manifests, the
leak-scan markers and the lifecycle state at the base come from the base
side of the history, and the journal's records from the calling checkout's
working tree; in a sidecar all of them come from the journal repository's
working tree, pinned to no commit, and the gate advises rather than
decides — the findings lane excepted
([ADR-0008](ADR-0008-journal-placements.md) D5).

### 4. The location is the git common directory of the repository the work is in

`.git/agentmarshal/` — shared by all worktrees, never committed, deleted
with the clone; not inside the working tree, even under `.gitignore`.

### 5. Sidecar placement

Local state lives in the git common directory of the **journal
repository**, not the host's:
[ADR-0008](ADR-0008-journal-placements.md) promises the host is never
written.

### 6. Format

Appended events, one JSON object per line; an atomic append of short
lines, or one file per writer.

### 7. Rotation and retention

Prose and prompts may be deleted.

Amended 2026-10-03, in a full sentence: the process log is rotated, and
the prose and prompts it holds may be deleted under retention; the local
formats this rotation works on are those the later decision on the record
model defines.

### 8. What the log does not promise

Protection against forgery — the same user rewrites it whole — or
visibility between machines.

Amended 2026-10-03, in full sentences: the log does not promise protection
against forgery — a process running as the same user rewrites it whole —
and it does not promise visibility between machines.

### 9. In-flight steps

The harness announces a step's start — a "step started, deadline" entry in
the log; a step is closed by the record it already ends with (an
implementer session, a review, `completed`); `status` and `doctor` show
the overdue ones
([proposal 040](../proposals/040-in-flight-steps-are-invisible-and-journal-writes-contend-on-one-checkout.md)).
Step events are passed to the extensions' `step` stage
([ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md)).

### 10. post-gate results

On the workstation the result goes to the log; in CI — to the CI output
and the extension's own channel; nothing is written to the journal.

### 11. What goes in first

In the first release that ships this: in-flight steps, reviewer prose and
diagnostics; raw accounting and post-gate results come next.

### 12. The map of places — in the top-level documentation

The README and the overview, ahead of the operating instructions:

```
<repository>/
├── .agentmarshal/                  committed — shared by the team and CI
│   ├── project.json                project settings (actors, placement, capture policy)
│   ├── journal/                    the journal: contracts (documents) and append-only records
│   ├── switches.toml               shared extension switches; changed only by an operational CR
│   ├── extensions/                 shared extensions (ADR-0013)
│   │   ├── <name>.toml             a declared extension — manifest only
│   │   └── <name>/                 an extension with commands: manifest.toml, bin/, lock/
│   └── upstream/                   an adopter's outbox of findings for upstream; created by init
└── .git/
    └── agentmarshal/               NOT committed — the clone's local state, shared by all worktrees
        ├── log/                    the process log
        ├── extensions/<name>/      this clone's personal extensions
        ├── deps/<name>/            extension dependencies installed from the lock
        ├── trust.toml              local run grants
        └── switches.toml           personal switches

later, when an adopter asks:
~/.config/agentmarshal/extensions/  user-scope extensions (Windows: %APPDATA%\agentmarshal\)
~/.local/share/agentmarshal/deps/   their dependencies (Windows: %LOCALAPPDATA%\agentmarshal\)
```

Three rules stand next to it: the gate reads nothing local — the journal
and the committed configuration from the base decide; everything under
`.git/agentmarshal/` is local, not evidence, and is never committed; the
executor runs in a sandbox with no write access to any local-state place —
without it, the local protection is off. In a sidecar the
`.git/agentmarshal/` tree is the journal repository's.

Amended 2026-10-03, on the first rule: "the journal ... decide" is two
different provenances, and "decide" holds in one placement only. In the
embedded placement the gate decides on the journal's records, read from
the calling checkout's working tree, and on the contract, the extension
manifests, the leak-scan markers and the lifecycle state at the base, read
from the base side of the history. In a sidecar all of them come from the
journal repository's working tree, pinned to no commit, and the gate
advises rather than decides — the findings lane excepted
([ADR-0008](ADR-0008-journal-placements.md) D5).

### 13. `doctor` and `status` print the actual paths

A new obligation — today `status` prints only the placement kind.

## Consequences

- The journal stays evidence only; the ephemeral does not go through CI.
- Prose at `hash` is no longer lost in a temporary directory — but it does
  not become durable either; the durable store remains a separate task.
- The host in a sidecar is still never written.
- Developers on different machines do not see each other's steps — a
  boundary of the decision.

## Alternatives considered

**"Step started" in the journal.** Visible immediately only in one's own
checkout; clutters the evidence.

**The log under `.gitignore`.** Per-worktree, writable by the executor,
held by a single line.

**A user directory.** Must be tied to the repository and does not
disappear with the clone.

**The log as ADR-0005's durable store.** Rotation and locality contradict
the durability promise.

**Pinning log records into the journal.** Revisits ADR-0008 and adds a
field no one asked for.

**A state database.** A path to an orchestrator.
