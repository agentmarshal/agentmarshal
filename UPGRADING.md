# Upgrading

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

Nothing is required. The new commands are additive and the loop is unchanged.
Worth knowing:

- `agentmarshal brief --task <id>` gives an implementer the contract; the tool
  had no delivery for it before.
- `agentmarshal accept` exists for a review that will not converge. Read
  [ADR-0007](docs/adr/ADR-0007-operator-acceptance.md) before using it — an
  acceptance is evidence that someone took a decision, and it is meant to cost
  something.
- `agentmarshal prune` clears the branches and worktrees of finished tasks.
- If an agent runs the rails on your behalf, set `AGENTMARSHAL_ACTOR` in its
  session environment. Without it the journal cannot tell the agent from the
  human whose git identity it uses.

### If you have to go back

Downgrading the tool is possible; downgrading a journal is not. A 0.1.0 install
pointed at a journal that has been written to by 0.2.0 will refuse it, and the
only remedy is to restore the journal from git history to a commit before the
first 0.2.0 record. Decide the cutover before it happens rather than after.
