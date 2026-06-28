# AgMake transactional runbooks

AgMake is the built-in AgentMarshal reference layer for task-local runbooks.
It is intentionally small: it generates, checks and documents deterministic
runbooks that execute the AgentMarshal protocol in a terminal process.

AgMake is not a dispatcher, daemon, dashboard, model runtime or replacement for
provider adapters. AgentMarshal remains a governance/process framework: policy,
contracts, gates, provenance and evidence. AgMake is the default v0.1 way to run
one prepared task protocol without keeping an expensive coordinator model alive.

## Position in the system

```text
model session
  prepares task + AgMake runbook
  stops

human or external runner
  runs <journal_root>/tmp/runner/CR-NNN-runbook.sh
  waits for pipeline/review in terminal
  records success or failure evidence

model session
  reads evidence only when needed
```

The concrete runbook belongs to host runtime state, for example:

```text
.agentmarshal/journal/tmp/runner/CR-NNN-runbook.sh
```

For an adopted legacy host the same path resolves under `.agents/` because the
project config has `"journal_root": ".agents"`. It is not committed. Framework
templates, schemas and documentation are committed under `agentmarshal/`.

## Section lifecycle

Every AgMake section is a small transaction. A section should follow this
lifecycle:

```text
prepare -> preflight -> execute -> verify -> sanitize -> checkpoint -> cleanup
```

If the section fails, it should run the failure path:

```text
classify failure -> cleanup owned temp -> safe rollback -> failure handoff -> exit nonzero
```

The terms are deliberately operational:

| Stage | Meaning |
|---|---|
| prepare | derive local paths, expected branch, expected files and section inputs |
| preflight | fail before side effects when required state is missing |
| execute | run the smallest useful command group |
| verify | check exact SHA/MR/review/file state produced by the section |
| sanitize | normalize artifacts, remove stale owned drafts, redact nothing-sensitive |
| checkpoint | write non-secret facts into runner state |
| cleanup | delete only section-owned temporary files |
| rollback | undo only local, section-owned side effects that are explicitly safe |
| handoff | print a compact `AGENTMARSHAL_RUNBOOK_FAILURE` block |

## Safe rollback policy

AgMake v0.1 is fail-closed and conservative.

Allowed rollback:

- delete or overwrite files below `<journal_root>/tmp/runner/<task>/`;
- remove stale runbook-owned event drafts before writing the canonical event;
- abandon an uncommitted section-local draft when the section owns every path;
- restore the previous branch only when no tracked changes were produced.

Forbidden automatic rollback:

- delete raw review files or run logs;
- rewrite pushed commits;
- close or merge MR automatically after an unknown failure;
- reset a branch broadly with `git reset --hard`;
- undo a successful remote merge;
- bypass scope-guard, pipeline, review or merge-policy.

When a side effect cannot be safely rolled back, the runbook stops and prints
the exact state needed for a human/model handoff.

## Resume and checkpoints

AgMake runbooks support explicit resume:

```bash
RUNBOOK_FROM=60 bash .agentmarshal/journal/tmp/runner/CR-NNN-runbook.sh
```

The runbook loads non-secret facts from:

```text
<journal_root>/runs/runner/CR-NNN/state.env
```

Checkpoint data may include:

- implementation SHA;
- implementation MR id;
- pipeline id;
- raw review artifact path;
- completion branch;
- completion SHA;
- completion MR id;
- completion review artifact path.

Sections must be idempotent or explicitly refuse re-entry. A section that
commits a completion transaction should detect an already-present transaction
before attempting to recreate it.

## Evidence rules

Implementation branches must not receive tracked runner evidence after review,
because any tracked change changes the reviewed SHA. Durable runner evidence is
written in the completion transaction.

| Artifact | Location | Tracked |
|---|---|---|
| concrete runbook | `<journal_root>/tmp/runner/` | no |
| runbook logs/state | `<journal_root>/runs/runner/` | no |
| raw review output | `<journal_root>/runs/` | no |
| canonical completion review | `<journal_root>/reviews/YYYY/` | yes |
| durable runner event | `<journal_root>/events/YYYY/CR-NNN/` | yes |
| task done move | `<journal_root>/tasks/done/YYYY/` | yes |

## Sequential v0.1, parallel later

AgMake v0.1 runs sections sequentially. The schema already records
`sections[].mode`, `sections[].after` and `sections[].locks` so a future runner
can reason about a graph, but the default bash implementation rejects parallel
execution.

This is intentional. Bash is acceptable for a deterministic single-task v0.1
runbook, but it is a poor foundation for true multithreaded scheduling,
structured cancellation, shared locks and rich error recovery. A future v0.2+
runner may use Python, TypeScript or another portable runtime while preserving
the same AgentMarshal evidence contract.

## CLI

`agentmarshal/bin/agmake` provides the deterministic v0.1 helper:

Fresh host:

```bash
agentmarshal/bin/agmake init \
  --task CR-031 \
  --branch docs/CR-031-agmake-transactional-runbooks \
  --title "CR-031: AgMake transactional runbooks"

agentmarshal/bin/agmake lint .agentmarshal/journal/tmp/runner/CR-031-runbook.sh
agentmarshal/bin/agmake state CR-031
```

Adopted legacy host:

```bash
agentmarshal/bin/agmake lint .agents/tmp/runner/CR-031-runbook.sh
```

The generated script can then be run directly:

```bash
bash .agentmarshal/journal/tmp/runner/CR-031-runbook.sh
```

The model should prepare the task and runbook, then stop. The operator or
external runner executes it and returns only the success summary or failure
handoff.
