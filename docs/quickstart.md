# Quickstart

This walks through the whole AgentMarshal loop on a throwaway repository —
from installing the package to a task that carries durable, SHA-bound
evidence that its work was independently reviewed. Every command below is run
against the published `agentmarshal` 0.1.0.

New here? [overview.md](overview.md) explains the idea and the vocabulary
(**host repo**, task, contract, scope, gate, …) in a page. This guide is the
hands-on companion.

Requirements: **Python ≥ 3.12** and **git** on your `PATH`.

## Install

```sh
pip install agentmarshal
agentmarshal --version
```

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

Only those three fields are allowed. `verdict` is an AgentMarshal verdict
(`approved`, `changes_required`, …); `findings` is an array of finding-id
strings. This is the entire contract a custom or model reviewer must satisfy.

### Gate attestation modes (`--attestation`)

- `commit` (default) — the invoker attests the pipeline via
  `AGENTMARSHAL_PIPELINE_OK_SHA` (Variant 1, e.g. a merge wrapper).
- `ci-required` — attestation is delegated to the provider's required checks
  (Variant 2): the gate runs as one required check and the provider blocks the
  merge until the test check is also green. Only sound when the provider
  actually requires that test check.

### The contract (`contract.md`)

Per task, in its TOML header: **`scope`** (paths the task may change — the gate
enforces it) and **`acceptance`** (machine-readable criteria; populate these so
a merged task doubles as an evaluation case). The markdown body holds the
objective and prose acceptance.

### `project.json`

`agentmarshal init` writes a minimal `.agentmarshal/project.json`
(`schema` + framework version); no hand-editing is needed for the loop. Optional
sections — a `capture` policy and `leak_scan.private_markers` — belong to
features that are **not active in 0.1.0** (see the roadmap in
[overview.md](overview.md)); ignore them for now.

## The governed loop

### 1. Initialize the host repo

Run this inside a git repository (make one with `git init` if needed):

```sh
agentmarshal init
```

This writes `.agentmarshal/project.json`. `agentmarshal doctor` checks the
project's health at any time.

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

### 4. Record an independent review

The gate requires a review whose **reviewer email differs from the commit
authors'** — independence is the property AgentMarshal makes durable, so it is
enforced. Record a verdict for the exact candidate commit:

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

### 5. Gate the candidate

The gate is the merge authority. It passes only when every check holds:

```sh
AGENTMARSHAL_PIPELINE_OK_SHA="$IMPL" \
  agentmarshal gate --task CR-001 --commit "$IMPL" --base "$BASE"
```

```
PASS: task CR-001 is not closed at base
PASS: diff within contract scope
PASS: latest review of <sha> is approved
PASS: reviewer is independent of the candidate's writers
PASS: pipeline attested for <sha>
PASS: evidence records are append-only
PASS: added records are valid
PASS: no record-path collisions with the base tree
PASS: task lifecycle records are consistent
gate: passed
```

It refuses, fail-closed, on any violation — an out-of-scope path, a missing or
non-independent review, a stale attestation.

The gate only **decides**; performing the actual merge is your provider's job.
Wiring the gate to block merges on GitHub, GitFlic, or a self-hosted setup is
covered in [self-hosting-workflow.md](self-hosting-workflow.md) and
[github-enforcement.md](github-enforcement.md).

### 6. Complete the task

Completion re-runs the gate and, on a pass, writes the `completed` record.
`--base` must stay the merge base the candidate was gated against:

```sh
AGENTMARSHAL_PIPELINE_OK_SHA="$IMPL" \
  agentmarshal complete --task CR-001 --commit "$IMPL" --base "$BASE"
git add .agentmarshal && git commit -m "complete CR-001"
```

### 7. Inspect the evidence

```sh
agentmarshal status CR-001
agentmarshal validate
```

`status` shows the task as `done` with its full record trail — the opened
event, the approved review bound to the commit SHA, and the completion.
`validate` checks the whole journal for integrity and is the check you run in
CI.

## What next

That is the complete loop: a merged task now carries portable, SHA-bound
evidence — living in git, not in a session log — that its work was
independently reviewed. From here:

- fill in **machine-readable acceptance criteria** in each contract;
- **enforce the gate** on your provider ([self-hosting-workflow.md](self-hosting-workflow.md),
  [github-enforcement.md](github-enforcement.md));
- record **token-economics** with `agentmarshal record-session` and read them
  back with `agentmarshal report`.

For the concepts, terminology, and roadmap, see [overview.md](overview.md); for
the design decisions and the honest 0.1.0 boundary, the [ADRs](adr/) and
[migration-v1-to-v2.md](migration-v1-to-v2.md).
