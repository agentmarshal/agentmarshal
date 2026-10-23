+++
schema = 2
id = "CR-211"
title = "agentmarshal stage run runs the stages shared extensions declare at the base, under a valid local grant, with one result line each and a pause exit for a stopping stage"
scope = [
  "src/agentmarshal/stages.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/extension-stage-run/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "the change extension-stage-run has a proposal, a design.md and a delta spec creating the capability extension-stages — its Purpose written in the delta, covering ADR-0013 decisions 1, 2, 4, 5, 6, 7 and 14 — with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal stage run --phase pre-gate|post-gate --task <id> --commit <rev> --base <ref>` reads the manifests of shared extensions in directory form from the base commit and runs each `[[stage]]` whose mode matches the phase (`pre-gate`: `pre-gate-warn` and `pre-gate-stop`; `post-gate`: `post-gate`), with the extension's directory materialized from the base commit, never from the candidate (decision 6); each command runs as `[<the core's Python interpreter>, <path under bin/>]`, never through a shell, with a time limit of the declared `timeout_seconds` capped by the core's limit",
  "the invocation protocol is the coordinator's decision, written in design.md and the spec: the extension's working directory is a temporary snapshot of the candidate commit; the environment carries `AGENTMARSHAL_PHASE`, `AGENTMARSHAL_TASK`, `AGENTMARSHAL_COMMIT`, `AGENTMARSHAL_BASE`, `AGENTMARSHAL_SNAPSHOT` and only the variables the manifest's `isolation.env` names (when present in the caller's environment) beside a minimal `PATH`; exit status 0 means checked, any other means failed",
  "on a workstation (environment variable `CI` not `true`) a stage runs only when the extension's local grant (CR-209's `trust.toml`) matches the hash of the base-materialized directory; otherwise its result is `not run (not granted)` or `not run (changed after approval: <file>)` naming the file; in CI no grant is needed (decision 14); every stage gets exactly one result line — checked / failed (exit <n>) / did not finish (timeout) / not run (<reason>) — and the extension's output is framed with a prefix naming it, so it cannot read as a gate line (decision 7); each result is appended to the process log as an `extension-event`",
  "the command exits 0 unless a `pre-gate-stop` stage failed, did not finish or did not run — then it exits 3 and prints that the process is paused before the gate; a `pre-gate-warn` failure prints a warning and exits 0; nothing is written to the journal; the gate is unchanged; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-stages/"]
decisions = ["ADR-0010", "ADR-0013", "ADR-0014", "ADR-0022"]
+++

# Running extension stages

## Context

ADR-0013 section A: an extension's one obligation is to be invoked at its
declared stage; two stages to start — `pre-gate` (in CI and at the merge
step, before the gate) and `post-gate` (after `complete`); the mode sits in
the manifest — `post-gate` notifies, `pre-gate-warn` warns loudly,
`pre-gate-stop` pauses, and an extension's own failure pauses too; an
extension is a separate step before the gate and the gate reads none of its
output; manifests and the code of shared extensions are taken from the
base; every extension gets a result line (decision 7). Decision 14: a
shared extension with a command runs on a workstation only under a valid
local grant (CR-209), recomputed before each run; in CI no grant is
needed. CR-152 and CR-158 parse `[[stage]]` entries (phase, command under
`bin/`) and the directory form; CR-206 reads the directory form from the
base tree.

The invocation protocol — what the command receives and what its exit
status means — is not fixed by an ADR; this contract fixes it and the
design records it, open to the operator's veto.

## Objective

A project can run its extensions' stages before the gate and after
completion, from approved code, with a result line for each.

## Acceptance Criteria

As in the header.

## Non-Goals

- Isolation beyond the time limit and the snapshot as working directory —
  network, write restrictions, the pre-gate floor (decision 8; a later task).
- Pause records and their acceptance, switches, `record-ext`, `complete`
  running stages, personal extensions, "addressee not found" (later tasks).
- Installing dependencies (decision 12: the tool does not install).
- Protection against a process with the user's rights (decision 15; see
  docs/threat-model.md).
