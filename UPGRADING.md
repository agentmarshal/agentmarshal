# Upgrading

## 0.3.0 → 0.4.0

### Upgrade every reader before the first new record schema

**A 0.3.0 installation cannot read a journal containing a record schema 4, 5,
or 6.** Schema 4 is used by a `finding` and by a review, acceptance, or
completion bound to one (CR-086). Schema 5 is used by a review carrying
`reviewed_contract` (CR-096) — and `agentmarshal review` writes it into
**every** review it records, so in practice the first review run with 0.4.0
is a schema-5 record. (A verdict recorded with `submit-review` does not carry
it.) Schema 6 is used by a `coordination` session (CR-106). A 0.3.0 reader
refuses each with `record has an unknown or missing schema version`.

The break is one-directional and record-specific: 0.4.0 continues to read
older records, and ordinary records that do not use these additions retain
their existing schemas. Nothing needs migration or rewriting. Once anyone
writes one of the new records, however, every older reader of that shared
journal fails closed.

### The procedure

1. **Find every place that reads the shared journal.** Include each operator's
   checkout, CI that runs `validate`, `status`, `gate`, or `complete`, and any
   merge wrapper.
2. **Upgrade all of them before anyone runs `agentmarshal review` with
   0.4.0**, and before the first finding or coordination session is written.
   This is a coordinated cutover; do not let a 0.3.0 checkout remain as a
   reader.
3. **Verify** `agentmarshal --version` reports `0.4.0` everywhere, then run
   `agentmarshal validate` on the journal.
4. Resume work. A 0.3.0 reader that was missed will refuse the first such
   record with the message above; upgrade that reader rather than editing the
   journal to remove evidence.

### Per installation method

**Pinned (`agentmarshal==0.3.0`)** — change the pin to `==0.4.0` and reinstall.

**Unpinned (`pip install agentmarshal`)** — an unpinned install does not move on
its own where the requirement is already satisfied; it moves on a fresh
environment, on `pip install -U`, or when a container is rebuilt. For this
upgrade that divergence is not harmless: an unpinned CI runner still on 0.3.0 is
exactly the missed reader the procedure above warns about. Pin, or upgrade it
explicitly.

### Commit the review's prose with its record

`agentmarshal review` now keeps the reviewer's output as a journal artifact
under the task's `artifacts/` directory and pins its SHA-256 in the review
record (CR-091); on success it no longer leaves a temporary copy.
`submit-review --prose FILE` attaches human prose the same way. `validate`
fails when a review record pins an artifact that is missing, so a wrapper that
stages only `records/` must also stage `artifacts/` from the first review
recorded with 0.4.0.

### Contract headers gain schema 2

Contract headers that carry `decisions`, `documents` or `extensions` use
`schema = 2`; AgentMarshal 0.4.0 reads both schema 1 and schema 2 headers, while
0.3.0 refuses a schema-2 contract. Upgrade every checkout that reads a shared
journal before committing the first schema-2 contract. Existing schema-1
contracts do not change, and a schema-2 contract uses no new record schema.

### Writers now reject records the projection would reject

Record-writing commands now consult the task lifecycle projection before they
append to an existing task. In particular, a `submit-review` after a terminal
record, which could previously exit 0 and leave the journal invalid, now exits
1 without writing the review (CR-102). Session measurements and a reopening
that the projection admits remain allowed. No installation action is required;
scripts that treated that successful exit as a write must handle the refusal.

### The gate sees both ends of a rename

0.3.0 listed a renamed path by its destination alone for the scope check, the
choice between the journal-only and diff lanes, and the empty-range refusal.
0.4.0 reads one listing in which a rename is its source deleted and its
destination added (CR-093). Two kinds of candidate that passed the 0.3.0 gate
are refused or judged differently now:

- a rename from a path the contract's scope does not cover into one it does is
  refused, and the scope line names the source path;
- a move from outside `.agentmarshal/journal/` into it is no longer a
  journal-only candidate: it takes the diff lane, where the contract is read
  and the source path must be in scope.

No installation action is required. A branch built on either shape must widen
the task's scope to the source path, through an amendment, or drop the move.
The gate's transcript for a candidate with no rename is unchanged.

### A reopening transaction now passes the gate

`agentmarshal reopen` on a completed task was already a valid projected record,
but its additive transaction was refused by the gate. 0.4.0 admits that
reopening transaction (CR-105). No migration is needed; rerun the normal gate
after upgrading if an earlier reopening was blocked.

### Update copied GitHub gate workflows

The gate has `--without-review` for a pull-request head that cannot yet carry
its review. It evaluates the remaining checks and says that the review-bound
checks were not examined; an existing review is still judged normally
(CR-099). The shipped GitHub workflow now passes this flag. If you copied the
old template, update its gate command to include `--without-review` and stop
tolerating the structurally failing gate run.

### Adjust parsers of leak-scan output

Leak-scan hits now render as `file: what matched`, naming a public signature or
a configured private marker by position while never printing the matched secret
(CR-100). The standalone `agentmarshal leak-scan` command prints every hit; the
gate transcript shows at most twenty and appends how many were not shown
(CR-103). Update any parser that expected the former category-only output or a
shared hit limit.

## 0.2.0 → 0.3.0

### What you must know first

**The record format does not change.** The schema is 3 in both releases, so
every **record** either version writes is read by the other, and nothing needs
migrating. For an embedded journal that settles it: there is no coordination
window and no order to respect, so upgrade each place when it suits you.

Records are not the whole of a journal, though. The next section is about the
part this sentence does not cover — a sidecar journal's configuration, which
0.2.0 reads without understanding.

One arrangement does break, and it breaks **silently** — which is why it gets
the rest of this section.

### A sidecar journal requires 0.3.0 everywhere that reads it

The sidecar placement is new in 0.3.0. If you use it — `agentmarshal init --host
PATH`, a journal in its own repository naming a host — then **every checkout that
runs AgentMarshal against that journal must be on 0.3.0.**

A 0.2.0 install does not fail on it. That is the problem. It does not know the
`placement` and `host` keys in `project.json`, so it treats the journal
repository as the repository being governed. `status` and `validate` then work
and say nothing about the placement, and the gate does this:

```
PASS: task CR-001 is not closed at base
PASS: journal-only transaction (deterministic lane; review not required)
PASS: pipeline attested for 1d9461e88503
PASS: evidence records are append-only
PASS: added records are valid
PASS: no record-path collisions with the base tree
PASS: task lifecycle records are consistent
gate: passed
```

Every line is true of the wrong repository. Everything in a sidecar lives under
`.agentmarshal/`, so the candidate looks like a journal-only transaction, the
review requirement is waived on that basis, and the result prints the merge
authority's own wording — for a placement whose gate is supposed to say it
decides nothing. That transcript is from the published 0.2.0, run against a real
sidecar journal.

If you do not use the sidecar placement, none of this applies to you.

### The procedure

1. **Upgrade wherever AgentMarshal runs:** each operator's machine, every CI
   runner that executes `validate`, `gate` or `complete`, and the host running
   your merge wrapper.
2. **Verify:** `agentmarshal --version` reports `0.3.0`, and `agentmarshal
   validate` passes on the journal.
3. If you run a sidecar journal, verify before anyone gates against it — a 0.2.0
   checkout left behind produces the transcript above rather than an error.

### Per installation method

**Pinned (`agentmarshal==0.2.0`)** — change the pin to `==0.3.0` and reinstall.

**Unpinned (`pip install agentmarshal`)** — an unpinned install does not move on
its own where the requirement is already satisfied; it moves on a fresh
environment, on `pip install -U`, or when a container is rebuilt. For this
upgrade that divergence is harmless unless you run a sidecar journal, in which
case pin, because the failure it produces is a passing transcript rather than a
refusal.

## 0.1.0 → 0.2.0

### What you must know first

**A journal written by 0.2.0 cannot be read by 0.1.0.** Records carry fields and
types 0.1.0 does not know, and it refuses a record it does not understand — by
design, because a record that cannot be validated is not evidence.

The break is **one-directional**: 0.2.0 reads everything 0.1.0 wrote. Nothing is
migrated, nothing is rewritten, and records keep the schema they were written
at. There is no data conversion step in this upgrade.

The consequence is about **coordination, not conversion**. From the moment any
party writes a record with 0.2.0, every party that reads that journal must
already be on 0.2.0. A 0.1.0 install will fail closed on the first such record —
`validate`, `status` and the gate alike — reporting:

```
FAIL: CR-001: record has an unknown or missing schema version
```

That message is the upgrade telling you it happened. It replaced a less helpful
one that named an unrecognised field instead.

### The procedure

1. **Find every place AgentMarshal runs.** Each operator's machine, every CI
   runner that executes `validate`, `gate` or `complete`, and the host running
   your merge wrapper. It is easy to forget the last two.
2. **Upgrade them all before anyone writes a record.** The order among them does
   not matter; what matters is that no 0.2.0 write happens while a 0.1.0 reader
   is still in use.
3. **Verify**: `agentmarshal --version` on each, then `agentmarshal validate` on
   the journal. It should pass everywhere.
4. Resume work. The first `open`, `review` or `complete` writes a schema-3
   record and the cutover is done.

### Per installation method

**Pinned (`agentmarshal==0.1.0`)** — change the pin to `==0.2.0` and reinstall.
This is the method to prefer if you share a journal: an upgrade happens when you
decide it does.

**Unpinned (`pip install agentmarshal`)** — this is the case that needs care,
and not for the reason it first appears. An unpinned install does not reliably
move: `pip install agentmarshal` where 0.1.0 is already present keeps it, since
the requirement is already satisfied. It moves on a fresh environment, on
`pip install -U`, or when a container is rebuilt.

So the fleet does not upgrade together and does not stay together either — it
**diverges**, on each machine's own schedule, which is worse for a format break
than either extreme. Whichever party rebuilds first starts writing records the
others cannot read.

Either pin now:

```sh
pip install 'agentmarshal==0.2.0'
```

or upgrade every party in one sitting and accept that the next release will
present the same problem again.

**Vendored wheel** — rebuild or re-download the 0.2.0 wheel, replace the vendored
artifact, and commit it. Remember the CI runner uses the committed wheel, so the
commit *is* the upgrade for that party.

**From source** — fetch and check out `v0.2.0`, then reinstall.

### After upgrading

Nothing is required, and the loop you already run behaves as it did: open,
implement, review, gate, complete. What 0.2.0 adds are further paths you may
take — an acceptance when review will not converge, and a way to reopen a task
that turned out to be unfinished. Worth knowing:

- `agentmarshal brief --task <id>` gives an implementer the contract; the tool
  had no delivery for it before.
- `agentmarshal accept` exists for a review that will not converge. Read
  [ADR-0007](docs/adr/ADR-0007-operator-acceptance.md) before using it — an
  acceptance is evidence that someone took a decision, and it is meant to cost
  something.
- `agentmarshal prune` reports the branches and worktrees of finished tasks;
  `--delete` removes the ones it listed as eligible.
- If an agent runs the rails on your behalf, set `AGENTMARSHAL_ACTOR` in its
  session environment. Without it the journal cannot tell the agent from the
  human whose git identity it uses.

### If you have to go back

Downgrading the tool is possible; downgrading a journal is not. A 0.1.0 install
pointed at a journal that has been written to by 0.2.0 will refuse it, and the
only remedy is to restore the journal from git history to a commit before the
first 0.2.0 record. Decide the cutover before it happens rather than after.
