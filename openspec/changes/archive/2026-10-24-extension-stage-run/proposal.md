## Why

ADR-0013 section A gives an extension one obligation — to be invoked at
its declared stage — and its decisions bind how: stages live at the
pre-gate and post-gate points (decision 2), an extension is a separate
step before the gate and the gate reads none of its output (decisions 4
and 5), the manifests and the code of shared extensions come from the
base commit, never the candidate's (decision 6), and every extension
gets a result line and its output a frame that cannot read as a gate
line (decision 7). Decision 14 makes the run on a workstation
conditional on a local grant matching the hash of the extension's
directory — CR-209 keeps those grants in `trust.toml` — and ADR-0022
section 7 names the `extension-event` process-log event each result
leaves. The manifests parse, the grants are kept, and nothing invokes
the stages themselves: there is no `stage` command.

## What Changes

A new `stage` command group, registered from `stages.py` the way the
`step` group is, carries one subcommand — `stage run --phase
<pre-gate|post-gate> --task <id> --commit <rev> --base <ref>`:

- `--phase pre-gate` runs every shared extension's `pre-gate-warn` and
  `pre-gate-stop` stages and `--phase post-gate` runs its `post-gate`
  stages — extensions in sorted-name order, each extension's matching
  stages in manifest order. The manifests are read at the merge base of
  `--base` and `--commit` with the gate's own base-tree reader, and each
  extension's directory is materialized from that tree — `git show` of
  every blob into a temporary directory — so neither the candidate's
  commit nor the working tree decides what runs.
- Each stage's `command` runs as
  `[<the core's Python interpreter>, <the path under bin/>]` — an argv
  process, never a shell and never a `PATH` lookup — in a fresh snapshot
  of the candidate commit, with an environment of a minimal `PATH`, the
  variables `isolation.env` names and the five `AGENTMARSHAL_*`
  protocol variables, bounded by the declared `timeout_seconds` capped
  at the core's 600-second limit; a breach kills the process group.
- On a workstation a stage runs only when a grant's per-file hashes
  match the base-materialized directory — `not granted` or
  `changed after approval: <file>` is `not run`; `CI=true` needs none.
- Every stage gets exactly one result line — `checked`,
  `failed (exit <n>)`, `did not finish (timeout)` or
  `not run (<reason>)` — and its captured output is reprinted one line
  each under a `<name> | ` frame with forgeable characters escaped, so
  extension output cannot read as a result line.
- Each result appends one `extension-event` to the process log:
  extension, `scope` `shared`, the stage's phase, decision, reason and
  commit, plus `result` for a post-gate stage.
- A `pre-gate-stop` stage that failed, did not finish or did not run
  pauses the process before the gate — the command prints it and exits
  3. A `pre-gate-warn` stage's failure is a loud warning; a `post-gate`
  stage's is a notification. Nothing is written to the journal.

## Capabilities

- new: `extension-stages`

## Impact

The gate is unchanged: it reads no stage output, and an extension cannot
alter its decisions — `stage run` is a step beside it. The trust and
local-state boundaries hold: the grant check reuses `extension_trust`'s
own hashing and grant reading, the process log is local working state,
and a sidecar runs no stages. Out of scope by the ADR's own staging:
network isolation, write isolation and pause records are later work; a
missing or symlinked command is `not run`, a grant mismatch `not run`,
and a timeout `did not finish` — every result is one line and one event,
never silence.
