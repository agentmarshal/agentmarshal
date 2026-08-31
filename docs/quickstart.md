# Quickstart

This walks through the whole AgentMarshal loop on a throwaway repository —
from installing the package to a task that carries durable, SHA-bound
evidence that its work was independently reviewed. Every command below was
verified against a wheel built from the `agentmarshal` 0.2.0 source. Version
0.2.0 was not yet published to the package index at verification time.

New here? [overview.md](overview.md) explains the idea and the vocabulary
(**host repo**, task, contract, scope, gate, …) in a page. This guide is the
hands-on companion.

Requirements: **Python ≥ 3.12** and **git** on your `PATH`. Until 0.2.0 is
published you also need **[uv](https://docs.astral.sh/uv/)**, because the only
way to get this version is to build it from source.

## Install

Version 0.2.0 is **not yet on the package index**, so it is installed from a
source checkout. These are the exact commands this guide was verified with:

```sh
uv build
uv venv .venv
uv pip install dist/agentmarshal-0.2.0-py3-none-any.whl
./.venv/bin/agentmarshal --version
```

After 0.2.0 is published, `pip install agentmarshal==0.2.0` installs the same
release and uv is no longer needed. Plain `pip install agentmarshal` installs
the latest published release, which may not be the version described here — pin
it if you share a journal, and see [UPGRADING.md](../UPGRADING.md) for why.

AgentMarshal is a single, dependency-free CLI. It stores everything in git
under `.agentmarshal/`, so there is no server and no database.

## Configuration

Everything you can configure, in one place. You do **not** need to set any of
this to run the loop below with a human review — the defaults work. Reach for
these when you wire in a model reviewer or CI.

### Environment variables

| Variable | Used by | What it does |
|---|---|---|
| `AGENTMARSHAL_REVIEWER_CMD` | `agentmarshal review` | The reviewer command to launch (model-agnostic; none is bundled). Placeholders `{model}` and `{prompt_file}` are substituted; the command receives the review prompt on **stdin** and must print the machine verdict block (below). Unset it and use `submit-review` for a human review instead. |
| `AGENTMARSHAL_PIPELINE_OK_SHA` | `agentmarshal gate`, `complete` | Your attestation that a **green pipeline ran for this exact commit**. The gate (in the default `commit` mode) passes the attestation check only when this equals the candidate commit. Locally you set it; in CI the pipeline sets it. `--pipeline-sha` is the equivalent flag. |

### The model-reviewer verdict protocol

When you use `agentmarshal review`, your `AGENTMARSHAL_REVIEWER_CMD` must end
its output with exactly one JSON object between a line reading
`AGENTMARSHAL_VERDICT_BEGIN` and a line reading `AGENTMARSHAL_VERDICT_END`:

```
AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "<sha>", "verdict": "approved", "findings": []}
AGENTMARSHAL_VERDICT_END
```

Required: `reviewed_commit`, `verdict` — one of **`approved`,
`changes_required`, `blocked`, `rejected`** — and `findings`, an array of unique
finding-id strings (empty only for `approved`, non-empty for every other
verdict). Optionally `advisory_findings`: non-blocking finding ids, disjoint
from `findings`, allowed with any verdict including `approved`.

Any other key is refused, and the error names it. The prompt AgentMarshal builds
states all of this, so a reviewer does not have to guess. It also asks for one
line of prose per blocking or advisory finding id before the verdict block,
naming what is wrong and where: ids are labels for the machine, while the prose
is what a human will read. When a verdict is refused the reviewer's **raw
output is kept** and its path is named in the error — a rejected verdict should
not cost you the analysis.

The same holds for a verdict that is *accepted* and **names a finding** —
blocking, or advisory alongside an approval. A record carries finding **ids**
and not the reasoning behind them, so the raw output is kept and
`agentmarshal review` names the file **on stderr**; stdout stays the record
path alone, for callers that read it. Keeping the output is best effort: if the
file cannot be written the review is still recorded, because the record is the
evidence. And it keeps only what the reviewer actually wrote — a reviewer that
ignores the prompt and emits an id with no prose leaves you a file with no prose
in it.

### Gate attestation modes (`--attestation`)

- `commit` (default) — the invoker attests the pipeline via
  `AGENTMARSHAL_PIPELINE_OK_SHA` (Variant 1, e.g. a merge wrapper).
- `ci-required` — attestation is delegated to the provider's required checks
  (Variant 2): the gate runs as one required check and the provider blocks the
  merge until the test check is also green. Only sound when the provider
  actually requires that test check.

`agentmarshal complete` has no `--attestation` flag — it always uses
`commit`-mode attestation, so pass `AGENTMARSHAL_PIPELINE_OK_SHA` (or
`--pipeline-sha`) for the candidate commit even when your gate runs
`ci-required`.

### The contract (`contract.md`)

Per task, in its TOML header: **`scope`** (paths the task may change — the gate
enforces it) and **`acceptance`** (machine-readable criteria; populate these so
a merged task doubles as an evaluation case). The markdown body holds the
objective and prose acceptance.

**Mind the trailing slash.** A scope entry ending in `/` matches everything
under that directory; without it the entry must equal a path exactly. So
`--scope src` matches only a file literally named `src`, and gates everything
under `src/` as out-of-scope. `agentmarshal open` warns about this case by name,
about an entry that names nothing on disk, and when no scope is declared at all.
An empty scope means no change can land until one is declared. The command still
opens the task, because a scope may legitimately declare a path the work is about
to create, or an operator may amend the scope later. The warning is a check on
the common mistakes, not a path validator.

### Who recorded a record (`actors`)

Every record carries `recorded_by` — the actor that created it — alongside
`recorded_by_source` saying where that name came from. This is separate from a
review's `reviewer`: one says who *wrote the record*, the other who is *said to
have reviewed*. When an agent records a human's verdict, the record says so.

The value is derived, not typed. `AGENTMARSHAL_ACTOR` overrides it and is marked
as an override; otherwise the invoking checkout's git identity is used, looked up
in an optional `actors` table:

```json
{
  "actors": {
    "lead": { "git_identities": ["lead@example.invalid"] },
    "review-bot": { "git_identities": ["bot@ci.example.invalid"] }
  }
}
```

With no table the git identity is recorded as-is; when nothing can be determined
both fields are omitted rather than guessed.

**If an agent runs AgentMarshal on your behalf, have it declare itself.** Set
`AGENTMARSHAL_ACTOR` in the agent's **session environment** — not per command,
which only works until someone forgets:

```json
{ "env": { "AGENTMARSHAL_ACTOR": "agent-claude-code" } }
```

The actors table cannot do this for you. An agent working on your behalf
normally commits under *your* git identity, so identity alone cannot tell the
two of you apart — only a declaration can. Without it the field still resolves,
to the checkout's address, and the journal keeps conflating the party that wrote
a record with the party it names.

**It is a declaration, not authentication** — like `vendor` and `email`. It does
not establish that the named actor did anything, and an agent that declines to
declare itself is indistinguishable from the human whose identity it uses.
Nothing detects that, and this is deliberately not presented as a control. What
it does is make the honest case expressible and a false attribution require a
second, explicit lie. See [ADR-0006](adr/ADR-0006-actors-and-identity.md).

### `project.json`

`agentmarshal init` writes a minimal `.agentmarshal/project.json`
(`schema` + framework version); no hand-editing is needed for the loop. The
supplementary-artifact `capture` policy is parsed but not acted on in
0.2.0: there is no policy-driven artifact writer or private store yet. The
`leak_scan.private_markers` list is active in 0.2.0 and adds project-specific
strings to the built-in advisory scan used by `leak-scan` and the gate.

## The governed loop

### 1. Initialize the host repo

Run this inside a git repository (make one with `git init` if needed):

```sh
agentmarshal init
```

This writes `.agentmarshal/project.json`. `agentmarshal doctor` checks the
project's health at any time.

It also creates `.agentmarshal/upstream/` — the **outbox**, where findings about
AgentMarshal itself go, one file per finding, to be sent upstream as a batch. Its
README states the convention, including the part that matters most: sanitize at
source, because upstream is public and cannot un-publish. An outbox README you
have already written is never overwritten, and a project that could not create
the directory is still initialized.

### 2. Open a task

A **task** declares a **scope** — the paths it may touch. Opening one creates
its contract and an `opened` record:

```sh
agentmarshal open --title "Add a greeting helper" --scope src/
```

The first task is `CR-001`, under `.agentmarshal/journal/tasks/CR-001/`:

- `contract.md` — fill in the acceptance criteria and objective; this is the
  task's specification.
- `records/…-opened.json` — the append-only lifecycle record.

Commit the opening so the contract is in history before any work builds on it.
The gate always reads the contract from the committed base, never from the
candidate, so a task can never widen its own scope:

```sh
git add .agentmarshal
git commit -m "open CR-001: add a greeting helper"
BASE=$(git rev-parse HEAD)   # the base the work is gated against
```

If an open task's contract needs correction, edit it and record the repair
before continuing, then commit the journal-only repair and advance the base:

```sh
agentmarshal amend --task CR-001 --reason "Clarify the greeting behaviour"
git add .agentmarshal && git commit -m "amend CR-001 contract"
BASE=$(git rev-parse HEAD)
```

`amend` records the reason; git history remains the contract's content trail.

Deliver the complete governed task to the implementer through the briefing
command. It includes the declared scope and acceptance criteria, the rules the
tool enforces, and the contract's prose boundaries verbatim. The output is only
the briefing, so it can be piped into whichever agent you use:

```sh
agentmarshal brief --task CR-001 | some-agent
```

### 3. Do the work

Branch, make the change **within the declared scope**, and commit:

```sh
git switch -c feat/CR-001
mkdir -p src
printf 'def greet(name):\n    return f"Hello, {name}!"\n' > src/app.py
git add src && git commit -m "implement CR-001"
IMPL=$(git rev-parse HEAD)
```

Task state is never edited by hand — it is projected from the records.

### 4. Record the session and inspect its economics

Record the work while its token counts and their origin are still available,
then read the task report as part of the loop:

```sh
agentmarshal record-session \
  --task CR-001 --role implementer --actor example/model \
  --activity implementation --outcome implemented \
  --input-tokens 1200 --output-tokens 300 --cache-tokens 100 \
  --usage-provider example --usage-method reported
agentmarshal report --task CR-001
```

Use `--usage-method measured` when the counts were reconstructed afterwards
from logs. Omit both usage flags when their provenance is unavailable; the
report identifies those counts as unrecorded rather than silently treating
them as provider-reported.

### 5. Record an independent review

The gate requires a review whose **recorded reviewer email differs from the
commit authors'**, and refuses the merge when it does not. Be clear about what
that establishes: it compares two declared identities. It does not establish
that a person reviewed anything — the reviewer fields are labels chosen by
whoever recorded the verdict (see the trust boundary in the README). Record a
verdict for the exact candidate commit:

```sh
agentmarshal submit-review \
  --task CR-001 --commit "$IMPL" \
  --verdict approved \
  --role reviewer --vendor human --model none \
  --email reviewer@example.com
```

`submit-review` records a verdict you already have; it runs no model, and
`--vendor`/`--model` are provenance labels (here, a human review). To have a
model produce the verdict, set `AGENTMARSHAL_REVIEWER_CMD` (see Configuration)
and use `agentmarshal review` with the same `--task/--commit/--base` plus
`--role/--vendor/--model/--email`.

The review record is written into the journal working tree. It stays
uncommitted until you record completion, so a review never has to be part of
the very diff it attests.

If the latest review of the candidate is non-approving, an operator may instead
accept that exact commit over all of its blocking findings:

```sh
agentmarshal accept \
  --task CR-001 --commit "$IMPL" \
  --by operator@example.com \
  --reason "The review loop did not converge"
```

The command derives the findings from the latest review. At gate time,
AgentMarshal checks them again and refuses a stale, partial, extra-finding, or
different-commit acceptance. This acceptance satisfies only the review-verdict
check: it is **not an approving review**, and reviewer independence and every
other gate check still apply.

### 6. Gate the candidate

Run the same advisory added-content scan independently when your CI needs a
separate check:

```sh
agentmarshal leak-scan --commit "$IMPL" --base "$BASE"
```

The gate runs this scan too and warns on matches; in 0.2.0 a match does not
block. The gate is the merge authority. It passes only when every blocking
check holds:

```sh
AGENTMARSHAL_PIPELINE_OK_SHA="$IMPL" \
  agentmarshal gate --task CR-001 --commit "$IMPL" --base "$BASE"
```

```
PASS: task CR-001 is not closed at base
PASS: diff within contract scope
PASS: latest review of <sha> is approved
PASS: declared reviewer identity differs from the candidate's declared writers
PASS: pipeline attested for <sha>
PASS: evidence records are append-only
PASS: added records are valid
PASS: no record-path collisions with the base tree
PASS: task lifecycle records are consistent
gate: passed
```

For a candidate accepted over findings, the approval line is replaced by an
explicit line such as:

```
PASS: accepted over findings F-001 by operator@example.com; not an approving review
```

It refuses, fail-closed, on any violation — an out-of-scope path, a missing or
non-independent review, a stale acceptance or attestation.

The gate only **decides**; performing the actual merge is your provider's job.
Wiring the gate to block merges on GitHub, GitFlic, or a self-hosted setup is
covered in [self-hosting-workflow.md](self-hosting-workflow.md) and
[github-enforcement.md](github-enforcement.md).

### 7. Complete the task

Completion re-runs the gate and, on a pass, writes the `completed` record.
`--base` must stay the merge base the candidate was gated against:

```sh
AGENTMARSHAL_PIPELINE_OK_SHA="$IMPL" \
  agentmarshal complete --task CR-001 --commit "$IMPL" --base "$BASE"
git add .agentmarshal && git commit -m "complete CR-001"
```

### 8. Inspect the evidence

```sh
agentmarshal status CR-001
agentmarshal validate
```

`status` shows the task as `done` with its full record trail — the opened
event, the approved review bound to the commit SHA, and the completion.
`validate` checks the whole journal for integrity and is the check you run in
CI.

If later evidence shows that completed work is unfinished, reopen the task
without rewriting its earlier completion:

```sh
agentmarshal reopen --task CR-001 --reason "A missing case was found"
```

The task projects as open again; an abandoned task cannot be reopened.

### 9. Prune finished-task artifacts

After completed work is merged, inspect the local branches and linked
worktrees that can be removed:

```sh
agentmarshal prune
agentmarshal prune --delete
```

The report considers only local state and never contacts a remote. A branch is
eligible under the journal and merge checks shown in the report, and never
while any worktree has it checked out. A linked worktree is eligible only when
its checked-out branch names a task whose projected state is `done` and the
worktree has no uncommitted changes. The main worktree is always skipped.

In a repository with more than one remote, configure any surrounding pruning
or cleanup automation to target the working remote, never a backup mirror.
Remote selection is the operator's responsibility because `agentmarshal prune`
contacts no remote. Keep the working remote tidy: at least one provider fails
closed beyond roughly a hundred branches, turning accumulated branches into an
outage rather than a cosmetic nuisance.

`--delete` uses Git's non-forcing branch deletion and worktree removal. If Git
refuses either operation — for example because a worktree is locked —
AgentMarshal reports the refusal and leaves the artifact in place.

## What next

That is the complete loop: a merged task now carries portable, SHA-bound
evidence — living in git, not in a session log — that its work was
independently reviewed. From here:

- fill in **machine-readable acceptance criteria** in each contract;
- **enforce the gate** on your provider ([self-hosting-workflow.md](self-hosting-workflow.md),
  [github-enforcement.md](github-enforcement.md)).

For the concepts, terminology, and roadmap, see [overview.md](overview.md); for
the design decisions and the honest implemented-vs-roadmap boundary, the
[ADRs](adr/) and [migration-v1-to-v2.md](migration-v1-to-v2.md).
