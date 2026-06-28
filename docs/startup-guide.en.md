# AgentMarshal Startup Guide

Document-ID: agentmarshal-startup-guide
Document-Version: 1
Language: en

<!-- Section-ID: overview -->
## Overview

This guide describes the first day of a new AgentMarshal host integration.
AgentMarshal is a Git governance layer: it provides contracts, evidence,
policy checks and runbook rails. It is not a model runtime.

<!-- Section-ID: when-to-use -->
## When To Use

Use AgentMarshal when agent work must be auditable: task contracts, independent
review, exact SHAs, CI evidence and durable follow-up tracking matter more than
fully autonomous execution.

<!-- Section-ID: install -->
## Install

Add AgentMarshal as a pinned submodule:

```bash
git submodule add <agentmarshal-url> agentmarshal
git submodule update --init --recursive
```

Do not configure the submodule to track a moving branch. Host repositories
should update the gitlink through a dedicated task and review.

<!-- Section-ID: init -->
## Init

Fresh host:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language en
./agentmarshal/bin/agentmarshal doctor --project-root .
./agentmarshal/bin/agentmarshal validate --project-root .
```

Existing host with a historical `.agents` archive:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language en \
  --legacy-archive .agents
```

Use `--adopt-existing` only when the old journal remains the active runtime.

<!-- Section-ID: first-task -->
## First Task

1. Create a small documentation or configuration task.
2. Generate a task-local AgMake runbook.
3. Review the generated runbook before running it.
4. Run the runbook in a terminal, not inside a long-lived model polling loop.
5. Review the exact implementation commit with an independent reviewer.

```bash
./agentmarshal/bin/agmake init --task CR-001 --branch docs/CR-001-first-task
./agentmarshal/bin/agmake lint .agentmarshal/journal/tmp/runner/CR-001-runbook.sh
bash .agentmarshal/journal/tmp/runner/CR-001-runbook.sh
```

<!-- Section-ID: update -->
## Update

Framework updates are host changes:

```text
read changelog -> update submodule -> host CI -> review exact gitlink -> merge
```

Never push framework commits from inside a host submodule checkout unless the
operator explicitly opened a framework-development task.
