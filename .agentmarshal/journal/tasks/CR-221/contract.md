+++
schema = 2
id = "CR-221"
title = "stage run enforces a stage's declared isolation as far as the platform allows — no network unless declared, a read-only candidate and no provider secrets at pre-gate — and names on the stage's line what it could not enforce"
scope = [
  "src/agentmarshal/stages.py",
  "src/agentmarshal/isolation.py",
  "tests/",
  "openspec/changes/stage-isolation/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "the change stage-isolation has a proposal, a design.md and a delta spec on the capability extension-stages (ADDED requirements, and MODIFIED where an existing requirement states what a stage receives); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "a stage whose manifest does not declare `network = true` runs without network access (ADR-0013 decision 8: network is allowed only when declared, and a declared manifest is approved by the grant that covers it): on Linux the stage process is started in a new user and network namespace by the core itself — `os.unshare` in the child before exec, never a shell and never a tool looked up on PATH; a stage declaring `network = true` runs as today",
  "at `pre-gate` the candidate working directory the stage runs in is read-only for the stage: on Linux, in the same child, a new mount namespace bind-mounts the candidate directory read-only over itself through libc `mount` (ctypes), after making mount propagation private; nothing outside the candidate directory is made read-only by this task, and `writes` beyond the candidate is reported as not enforced",
  "at `pre-gate` no provider secret reaches the stage even when `isolation.env` names it: a fixed, documented list of names and suffixes (at least `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GITHUB_TOKEN`, `GH_TOKEN`, `GITLAB_TOKEN`, and any name ending `_API_KEY`, `_TOKEN`, `_SECRET`, `_PASSWORD`) is withheld, and the run notes once which declared names were withheld; `post-gate` is unchanged",
  "whatever the core cannot enforce on this platform or in this environment — namespaces refused (non-Linux, a kernel or policy forbidding unprivileged user namespaces, a sandbox around the core), a mount that fails — does not stop the stage: the stage runs and its result line, or one note line for it, names each guarantee not enforced and why (`not enforced: network (…)`, `not enforced: read-only candidate (…)`); a guarantee enforced is not mentioned, so a stage line on a platform that enforces everything is unchanged",
  "tests do not depend on whether the machine permits namespaces: each branch is demonstrated by forcing the probe's answer, and one end-to-end test — a stage that tries to open a TCP connection and to write into the candidate — runs where the probe succeeds and is skipped with its reason where it does not; switched-off, not-run and changed-after-approval outcomes are unchanged; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-stages/"]
decisions = ["ADR-0001", "ADR-0013", "ADR-0014"]
+++

# Stage isolation

## Context

ADR-0013 decision 8: isolation is declared in the manifest for any stage —
network, environment variables by name, where the extension writes,
timeout. For `pre-gate` there is a floor the manifest cannot remove: the
candidate snapshot is read-only, no provider secrets, the timeout no higher
than the core's limit. Network is allowed when declared and approved. The
core enforces what is declared as far as the platform allows, and names in
its output what it cannot enforce; it restricts only the extension
processes it launches itself — the isolation of agents stays with the
harness (ADR-0001). CR-211 already passes only the declared environment
variables beside a minimal `PATH` and caps the timeout.

## Objective

A stage cannot reach the network or change the candidate unless it was
allowed to, and where the core cannot stop it, the output says so.

## Acceptance Criteria

As in the header.

## Non-Goals

- `doctor` showing declared and enforced isolation (a later task).
- Making anything outside the candidate directory read-only; a filesystem
  sandbox for the stage beyond the candidate; macOS or Windows mechanisms
  (they report "not enforced").
- Personal extensions (a later task).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
